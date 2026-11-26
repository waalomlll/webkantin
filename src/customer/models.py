from django.conf import settings
from django.db import models


class Kantin(models.Model):
    kode = models.SlugField(primary_key=True, max_length=20)
    nama = models.CharField(max_length=80)
    lokasi = models.CharField(max_length=120)
    emoji = models.CharField(max_length=8, default='🍽️')

    class Meta:
        ordering = ['nama']
        verbose_name_plural = 'kantin'

    def __str__(self):
        return self.nama


class Kedai(models.Model):
    kantin = models.ForeignKey(Kantin, on_delete=models.CASCADE, related_name='kedai')
    nama = models.CharField(max_length=80)
    deskripsi = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ['id']
        verbose_name_plural = 'kedai'

    def __str__(self):
        return f'{self.nama} ({self.kantin.nama})'


class Menu(models.Model):
    kedai = models.ForeignKey(Kedai, on_delete=models.CASCADE, related_name='menu')
    nama = models.CharField(max_length=80)
    harga = models.PositiveIntegerField()
    tersedia = models.BooleanField(default=True)
    emoji = models.CharField(max_length=8, default='🍽️')
    foto = models.FileField(upload_to='menu/', blank=True)

    class Meta:
        ordering = ['id']
        verbose_name_plural = 'menu'

    def __str__(self):
        return self.nama


class Pesanan(models.Model):
    DITERIMA = 'diterima'
    DIPROSES = 'diproses'
    SIAP = 'siap'
    SELESAI = 'selesai'
    DIBATALKAN = 'dibatalkan'
    STATUS = [
        (DITERIMA, 'Pesanan diterima'),
        (DIPROSES, 'Sedang diproses'),
        (SIAP, 'Siap diambil'),
        (SELESAI, 'Selesai'),
        (DIBATALKAN, 'Dibatalkan'),
    ]
    PINDAH = {
        DITERIMA: (DIPROSES, DIBATALKAN),
        DIPROSES: (SIAP,),
        SIAP: (SELESAI,),
    }

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pesanan')
    kedai = models.ForeignKey(Kedai, on_delete=models.PROTECT, related_name='pesanan')
    nomor_meja = models.CharField(max_length=10)
    status = models.CharField(max_length=12, choices=STATUS, default=DITERIMA)
    total = models.PositiveIntegerField()
    dana_dikembalikan = models.BooleanField(default=False)
    dibuat = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-dibuat']
        verbose_name_plural = 'pesanan'

    def __str__(self):
        return f'Pesanan #{self.pk}'

    def bisa_pindah(self, tujuan):
        return tujuan in self.PINDAH.get(self.status, ())

    def ubah_status(self, tujuan):
        if not self.bisa_pindah(tujuan):
            return False
        self.status = tujuan
        if tujuan == self.DIBATALKAN:
            self.dana_dikembalikan = True
        self.save()
        return True


class ItemPesanan(models.Model):
    pesanan = models.ForeignKey(Pesanan, on_delete=models.CASCADE, related_name='item')
    menu = models.ForeignKey(Menu, on_delete=models.SET_NULL, null=True, blank=True)
    nama = models.CharField(max_length=80)
    harga = models.PositiveIntegerField()
    jumlah = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.harga * self.jumlah
