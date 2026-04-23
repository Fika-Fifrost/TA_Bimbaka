from django import forms
from django.contrib.auth.models import User
from .models import Profile
from .models import Kuis, SoalKuis


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(UserUpdateForm, self).__init__(*args, **kwargs)

        # Jika user yang sedang login adalah Siswa, hapus field email dari form
        if self.user and self.user.groups.filter(name="Siswa").exists():
            if 'email' in self.fields:
                del self.fields['email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        # HAPUS 'kelas' dari sini, sisakan 'foto' saja
        fields = ["foto"]
        widgets = {
            "foto": forms.FileInput(
                attrs={"class": "hidden"}
            ),  # Class 'hidden' karena kita pakai tombol custom di UI
        }


class KuisForm(forms.ModelForm):
    class Meta:
        model = Kuis
        fields = ["judul", "deskripsi", "kelas_target", "durasi_menit", "is_active"]
        widgets = {
            "judul": forms.TextInput(attrs={"class": "w-full p-2 border rounded"}),
            "deskripsi": forms.Textarea(
                attrs={"class": "w-full p-2 border rounded", "rows": 3}
            ),
            "kelas_target": forms.Select(attrs={"class": "w-full p-2 border rounded"}),
            "durasi_menit": forms.NumberInput(
                attrs={"class": "w-full p-2 border rounded"}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "w-5 h-5"}),
        }


class SoalKuisForm(forms.ModelForm):
    class Meta:
        model = SoalKuis
        fields = [
            "pertanyaan",
            "gambar",
            "opsi_a",
            "opsi_b",
            "opsi_c",
            "opsi_d",
            "jawaban_benar",
        ]
        widgets = {
            "pertanyaan": forms.Textarea(
                attrs={"class": "w-full p-2 border rounded", "rows": 3}
            ),
            "opsi_a": forms.TextInput(attrs={"class": "w-full p-2 border rounded"}),
            "opsi_b": forms.TextInput(attrs={"class": "w-full p-2 border rounded"}),
            "opsi_c": forms.TextInput(attrs={"class": "w-full p-2 border rounded"}),
            "opsi_d": forms.TextInput(attrs={"class": "w-full p-2 border rounded"}),
            "jawaban_benar": forms.Select(
                attrs={"class": "w-full p-2 border rounded bg-green-50"}
            ),
        }
