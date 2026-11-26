from django import template

register = template.Library()


@register.filter
def rupiah(nilai):
    try:
        return 'Rp ' + f'{int(nilai):,}'.replace(',', '.')
    except (TypeError, ValueError):
        return 'Rp 0'


@register.simple_tag(takes_context=True)
def jumlah_keranjang(context):
    keranjang = context['request'].session.get('keranjang') or {}
    return sum(keranjang.get('item', {}).values())
