from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import ItemPesanan, Kantin, Kedai, Menu, Pesanan


def _keranjang(request):
    return request.session.get('keranjang') or {'kedai': None, 'item': {}}


def _simpan(request, data):
    request.session['keranjang'] = data


def _baris_keranjang(data):
    menus = Menu.objects.filter(pk__in=[int(k) for k in data['item']]).select_related('kedai__kantin')
    baris = []
    for menu in menus:
        jumlah = data['item'][str(menu.pk)]
        baris.append({'menu': menu, 'jumlah': jumlah, 'subtotal': menu.harga * jumlah})
    return baris


def _jumlah_valid(nilai):
    try:
        angka = int(nilai)
    except (TypeError, ValueError):
        return None
    return angka if angka >= 0 else None


def kantin_list(request):
    kode = request.GET.get('kantin')
    meja = request.GET.get('meja')
    if kode and Kantin.objects.filter(pk=kode).exists():
        request.session['kantin'] = kode
        if meja and meja.isdigit():
            request.session['meja'] = meja
        return redirect('customer:kedai', kode=kode)
    return render(request, 'customer/kantin.html', {'daftar': Kantin.objects.all()})


def kedai_list(request, kode):
    kantin = get_object_or_404(Kantin, pk=kode)
    return render(request, 'customer/kedai.html', {
        'kantin': kantin,
        'daftar': kantin.kedai.all(),
        'meja': request.session.get('meja'),
    })


def menu_list(request, kedai_id):
    kedai = get_object_or_404(Kedai.objects.select_related('kantin'), pk=kedai_id)
    if request.method == 'POST':
        menu = get_object_or_404(Menu, pk=request.POST.get('menu_id'), kedai=kedai)
        jumlah = _jumlah_valid(request.POST.get('jumlah'))
        data = _keranjang(request)
        if not jumlah:
            messages.error(request, 'Jumlah harus berupa angka minimal 1.')
        elif not menu.tersedia:
            messages.error(request, f'{menu.nama} sedang habis.')
        elif data['kedai'] not in (None, kedai.pk) and data['item']:
            messages.warning(request, 'Keranjang berisi pesanan dari kedai lain. Kosongkan keranjang dulu untuk memesan di kedai ini.')
        else:
            data['kedai'] = kedai.pk
            kunci = str(menu.pk)
            data['item'][kunci] = data['item'].get(kunci, 0) + jumlah
            _simpan(request, data)
            messages.success(request, f'{jumlah} × {menu.nama} masuk keranjang.')
        return redirect('customer:menu', kedai_id=kedai.pk)
    return render(request, 'customer/menu.html', {'kedai': kedai, 'daftar': kedai.menu.all()})


@login_required
def keranjang(request):
    data = _keranjang(request)
    if request.method == 'POST':
        aksi = request.POST.get('aksi')
        if aksi == 'kosongkan':
            request.session.pop('keranjang', None)
            return redirect('customer:keranjang')
        if aksi == 'ubah':
            kunci = request.POST.get('menu_id', '')
            jumlah = _jumlah_valid(request.POST.get('jumlah'))
            if kunci in data['item']:
                if jumlah is None:
                    messages.error(request, 'Jumlah harus berupa angka.')
                elif jumlah == 0:
                    del data['item'][kunci]
                else:
                    data['item'][kunci] = jumlah
                if not data['item']:
                    data = {'kedai': None, 'item': {}}
                _simpan(request, data)
            return redirect('customer:keranjang')
        if aksi == 'lanjut':
            meja = request.POST.get('nomor_meja', '').strip()
            if not meja.isdigit() or not 1 <= int(meja) <= 999:
                messages.error(request, 'Nomor meja harus berupa angka.')
                return redirect('customer:keranjang')
            request.session['meja'] = meja
            return redirect('customer:bayar')
    baris = _baris_keranjang(data)
    return render(request, 'customer/keranjang.html', {
        'baris': baris,
        'total': sum(b['subtotal'] for b in baris),
        'kedai': baris[0]['menu'].kedai if baris else None,
        'meja': request.session.get('meja', ''),
    })


@login_required
def bayar(request):
    data = _keranjang(request)
    baris = _baris_keranjang(data)
    meja = request.session.get('meja')
    if not baris or not meja:
        return redirect('customer:keranjang')
    total = sum(b['subtotal'] for b in baris)
    if request.method == 'POST':
        if request.POST.get('hasil') != 'berhasil':
            return render(request, 'customer/bayar_gagal.html', {'total': total})
        habis = [b['menu'].nama for b in baris if not b['menu'].tersedia]
        if habis:
            messages.error(request, 'Menu berikut baru saja habis: ' + ', '.join(habis))
            return redirect('customer:keranjang')
        with transaction.atomic():
            pesanan = Pesanan.objects.create(
                user=request.user, kedai=baris[0]['menu'].kedai, nomor_meja=meja, total=total)
            ItemPesanan.objects.bulk_create([
                ItemPesanan(pesanan=pesanan, menu=b['menu'], nama=b['menu'].nama,
                            harga=b['menu'].harga, jumlah=b['jumlah'])
                for b in baris
            ])
        request.session.pop('keranjang', None)
        return redirect('customer:pesanan_detail', pk=pesanan.pk)
    return render(request, 'customer/bayar.html', {'baris': baris, 'total': total, 'meja': meja})


@require_POST
def bayar_batal(request):
    request.session.pop('keranjang', None)
    messages.info(request, 'Pembayaran dibatalkan dan keranjang dikosongkan.')
    return redirect('customer:kantin')


@login_required
def pesanan_list(request):
    return render(request, 'customer/pesanan.html', {
        'daftar': request.user.pesanan.select_related('kedai__kantin').prefetch_related('item'),
    })


@login_required
def pesanan_detail(request, pk):
    pesanan = get_object_or_404(Pesanan.objects.select_related('kedai__kantin'), pk=pk, user=request.user)
    langkah = [Pesanan.DITERIMA, Pesanan.DIPROSES, Pesanan.SIAP, Pesanan.SELESAI]
    nama = dict(Pesanan.STATUS)
    indeks = langkah.index(pesanan.status) if pesanan.status in langkah else -1
    return render(request, 'customer/pesanan_detail.html', {
        'pesanan': pesanan,
        'langkah': [{'label': nama[k], 'aktif': i <= indeks} for i, k in enumerate(langkah)],
    })


@login_required
def pesanan_status(request, pk):
    pesanan = get_object_or_404(Pesanan, pk=pk, user=request.user)
    return JsonResponse({'status': pesanan.status, 'label': pesanan.get_status_display()})


@login_required
@require_POST
def pesanan_batal(request, pk):
    pesanan = get_object_or_404(Pesanan, pk=pk, user=request.user)
    if pesanan.ubah_status(Pesanan.DIBATALKAN):
        messages.success(request, 'Pesanan dibatalkan. Dana akan dikembalikan.')
    else:
        messages.error(request, 'Pesanan sudah diproses penjual dan tidak bisa dibatalkan.')
    return redirect('customer:pesanan_detail', pk=pesanan.pk)
