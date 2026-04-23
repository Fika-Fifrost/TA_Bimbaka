from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.filter(name="has_group")
def has_group(user, group_name):
    """
    Cek apakah user termasuk dalam grup tertentu.
    Penggunaan di template: {% if user|has_group:"NamaGrup" %}
    """
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        return False

    return group in user.groups.all()


@register.filter(name="to_terbilang")
def to_terbilang(value):
    """Mengubah angka (string or int) menjadi teks bahasa Indonesia."""
    try:
        num = int(value)
    except (ValueError, TypeError):
        return value  # Kembalikan nilai asli jika bukan angka

    satuan = [
        "Nol",
        "Satu",
        "Dua",
        "Tiga",
        "Empat",
        "Lima",
        "Enam",
        "Tujuh",
        "Delapan",
        "Sembilan",
    ]

    if 0 <= num < 10:
        return satuan[num]
    elif num == 10:
        return "Sepuluh"
    elif num == 11:
        return "Sebelas"
    elif 12 <= num <= 19:
        return satuan[num - 10] + " Belas"
    elif 20 <= num <= 99:
        puluhan = num // 10
        sisa = num % 10
        return satuan[puluhan] + " Puluh" + (" " + satuan[sisa] if sisa > 0 else "")
    elif 100 <= num <= 199:
        return "Seratus" + (" " + to_terbilang(num - 100) if (num - 100) > 0 else "")
    # Batasi sampai 199 untuk kebutuhan kuis ini
    return str(value)
