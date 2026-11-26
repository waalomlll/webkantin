from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from src.customer.models import Kantin, Kedai, Menu

DATA = {
    'gku2': ('Kantin GKU 2', 'Gedung Kuliah Umum 2', '🏫', [
        ('Kedai Nasi', 'Nasi dengan aneka lauk', [
            ('Nasi Ayam Goreng', 15000, True, '🍗'),
            ('Nasi Telur Balado', 12000, True, '🍳'),
            ('Nasi Rendang', 20000, False, '🍛'),
        ]),
        ('Kedai Minuman', 'Minuman dingin dan hangat', [
            ('Es Teh Manis', 4000, True, '🧋'),
            ('Es Jeruk', 6000, True, '🍊'),
            ('Kopi Susu', 10000, True, '☕'),
        ]),
    ]),
    'koica': ('Kantin Koica', 'Area Koica', '🍜', [
        ('Kedai Mie dan Bakso', 'Mie ayam, bakso, dan sejenisnya', [
            ('Mie Ayam', 13000, True, '🍜'),
            ('Bakso Urat', 15000, True, '🍲'),
            ('Mie Ayam Bakso', 17000, False, '🥢'),
        ]),
        ('Kedai Camilan', 'Gorengan dan roti', [
            ('Tahu Isi (3 pcs)', 5000, True, '🥟'),
            ('Roti Bakar Cokelat', 9000, True, '🍞'),
            ('Pisang Goreng', 6000, True, '🍌'),
        ]),
    ]),
    'tb2': ('Kantin Asrama TB 2', 'Asrama TB 2', '🏠', [
        ('Kedai Ayam Geprek', 'Ayam geprek dan teman-temannya', [
            ('Ayam Geprek', 14000, True, '🌶️'),
            ('Ayam Geprek Keju', 18000, True, '🧀'),
            ('Nasi Putih', 4000, True, '🍚'),
        ]),
        ('Kedai Sarapan', 'Bubur dan lontong', [
            ('Bubur Ayam', 12000, True, '🥣'),
            ('Lontong Sayur', 11000, False, '🥘'),
            ('Teh Hangat', 3000, True, '🍵'),
        ]),
    ]),
    'tb3': ('Kantin Asrama TB 3', 'Asrama TB 3', '🍽️', [
        ('Kedai Nasi Campur', 'Nasi campur dan lauk rumahan', [
            ('Nasi Campur', 16000, True, '🍱'),
            ('Nasi Tempe Orek', 10000, True, '🥗'),
            ('Soto Ayam', 14000, True, '🍲'),
        ]),
        ('Kedai Jus dan Minuman', 'Jus segar dan minuman kemasan', [
            ('Jus Alpukat', 12000, True, '🥑'),
            ('Jus Mangga', 11000, False, '🥭'),
            ('Air Mineral', 4000, True, '💧'),
        ]),
    ]),
}


class Command(BaseCommand):
    help = 'Isi data contoh kantin, kedai, menu, dan akun pembeli demo'

    def handle(self, *args, **options):
        if not Kantin.objects.exists():
            for kode, (nama, lokasi, emoji, daftar_kedai) in DATA.items():
                kantin = Kantin.objects.create(kode=kode, nama=nama, lokasi=lokasi, emoji=emoji)
                for nama_kedai, deskripsi, daftar_menu in daftar_kedai:
                    kedai = Kedai.objects.create(kantin=kantin, nama=nama_kedai, deskripsi=deskripsi)
                    for nama_menu, harga, tersedia, emoji_menu in daftar_menu:
                        Menu.objects.create(kedai=kedai, nama=nama_menu, harga=harga,
                                            tersedia=tersedia, emoji=emoji_menu)
        User = get_user_model()
        if not User.objects.filter(username='mahasiswa').exists():
            User.objects.create_user('mahasiswa', password='demo123', first_name='Mahasiswa Contoh')
        self.stdout.write('Data contoh siap.')
