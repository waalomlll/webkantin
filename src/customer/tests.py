from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Menu, Pesanan


class AlurPesananTest(TestCase):
    def setUp(self):
        call_command('seed_kantin', verbosity=0)
        self.client.login(username='mahasiswa', password='demo123')
        self.menu = Menu.objects.get(nama='Nasi Ayam Goreng')
        self.habis = Menu.objects.get(nama='Nasi Rendang')

    def tambah(self, menu, jumlah=1):
        return self.client.post(reverse('customer:menu', args=[menu.kedai_id]),
                                {'menu_id': menu.pk, 'jumlah': jumlah})

    def pesan(self):
        self.tambah(self.menu, 2)
        self.client.post(reverse('customer:keranjang'), {'aksi': 'lanjut', 'nomor_meja': '5'})
        return self.client.post(reverse('customer:bayar'), {'hasil': 'berhasil'})

    def test_qr_menyimpan_meja(self):
        r = self.client.get('/customer/', {'kantin': 'gku2', 'meja': '7'})
        self.assertRedirects(r, reverse('customer:kedai', args=['gku2']))
        self.assertEqual(self.client.session['meja'], '7')

    def test_menu_habis_ditolak(self):
        self.tambah(self.habis)
        self.assertFalse(self.client.session.get('keranjang'))

    def test_jumlah_tidak_valid_ditolak(self):
        for nilai in ('0', '-1', 'abc', ''):
            self.tambah(self.menu, nilai)
        self.assertFalse(self.client.session.get('keranjang'))

    def test_satu_pesanan_satu_kedai(self):
        self.tambah(self.menu)
        lain = Menu.objects.get(nama='Es Teh Manis')
        self.tambah(lain)
        self.assertEqual(list(self.client.session['keranjang']['item']), [str(self.menu.pk)])

    def test_bayar_berhasil_membuat_pesanan(self):
        r = self.pesan()
        pesanan = Pesanan.objects.get()
        self.assertRedirects(r, reverse('customer:pesanan_detail', args=[pesanan.pk]))
        self.assertEqual(pesanan.total, 30000)
        self.assertEqual(pesanan.nomor_meja, '5')
        self.assertEqual(pesanan.status, 'diterima')
        self.assertFalse(self.client.session.get('keranjang'))

    def test_bayar_gagal_tidak_membuat_pesanan(self):
        self.tambah(self.menu)
        self.client.post(reverse('customer:keranjang'), {'aksi': 'lanjut', 'nomor_meja': '5'})
        r = self.client.post(reverse('customer:bayar'), {'hasil': 'gagal'})
        self.assertContains(r, 'Pembayaran gagal')
        self.assertEqual(Pesanan.objects.count(), 0)
        self.assertTrue(self.client.session.get('keranjang'))

    def test_harga_diambil_dari_database(self):
        self.tambah(self.menu)
        self.menu.harga = 20000
        self.menu.save()
        self.client.post(reverse('customer:keranjang'), {'aksi': 'lanjut', 'nomor_meja': '5'})
        self.client.post(reverse('customer:bayar'), {'hasil': 'berhasil'})
        self.assertEqual(Pesanan.objects.get().total, 20000)

    def test_menu_jadi_habis_sebelum_bayar(self):
        self.tambah(self.menu)
        self.client.post(reverse('customer:keranjang'), {'aksi': 'lanjut', 'nomor_meja': '5'})
        self.menu.tersedia = False
        self.menu.save()
        self.client.post(reverse('customer:bayar'), {'hasil': 'berhasil'})
        self.assertEqual(Pesanan.objects.count(), 0)

    def test_batal_hanya_saat_diterima_dan_refund(self):
        self.pesan()
        pesanan = Pesanan.objects.get()
        pesanan.ubah_status('diproses')
        self.client.post(reverse('customer:pesanan_batal', args=[pesanan.pk]))
        pesanan.refresh_from_db()
        self.assertEqual(pesanan.status, 'diproses')
        pesanan.status = 'diterima'
        pesanan.save()
        self.client.post(reverse('customer:pesanan_batal', args=[pesanan.pk]))
        pesanan.refresh_from_db()
        self.assertEqual(pesanan.status, 'dibatalkan')
        self.assertTrue(pesanan.dana_dikembalikan)

    def test_transisi_status(self):
        self.pesan()
        p = Pesanan.objects.get()
        self.assertFalse(p.ubah_status('selesai'))
        self.assertTrue(p.ubah_status('diproses'))
        self.assertTrue(p.ubah_status('siap'))
        self.assertFalse(p.ubah_status('dibatalkan'))
        self.assertTrue(p.ubah_status('selesai'))

    def test_status_json_dan_akses_milik_orang_lain(self):
        self.pesan()
        p = Pesanan.objects.get()
        self.assertEqual(self.client.get(reverse('customer:pesanan_status', args=[p.pk])).json()['status'], 'diterima')
        get_user_model().objects.create_user('lain', password='x12345678')
        self.client.login(username='lain', password='x12345678')
        self.assertEqual(self.client.get(reverse('customer:pesanan_detail', args=[p.pk])).status_code, 404)

    def test_perlu_login(self):
        self.client.logout()
        r = self.client.get(reverse('customer:keranjang'))
        self.assertEqual(r.status_code, 302)
