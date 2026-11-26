from django.contrib import admin

from .models import ItemPesanan, Kantin, Kedai, Menu, Pesanan


class ItemInline(admin.TabularInline):
    model = ItemPesanan
    extra = 0


@admin.register(Pesanan)
class PesananAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'kedai', 'nomor_meja', 'status', 'total', 'dibuat')
    list_filter = ('status', 'kedai')
    inlines = [ItemInline]


admin.site.register(Kantin)
admin.site.register(Kedai)
admin.site.register(Menu)
