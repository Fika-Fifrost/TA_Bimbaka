from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    NilaiEvaluasi, NilaiEvaluasiPerMateri, JawabanEvaluasi,
    KemajuanBelajar, Profile, Kuis, SoalKuis, RiwayatKuis
)


class SoalKuisInline(admin.StackedInline):
    """Untuk input soal di dalam form Kuis"""
    model = SoalKuis
    extra = 1
    fields = ('pertanyaan', 'gambar', ('opsi_a', 'opsi_b'), ('opsi_c', 'opsi_d'), 'jawaban_benar')


class NilaiPerMateriInline(admin.TabularInline):
    """Rincian nilai materi (Hanya 6 baris, jadi tetap ringan)"""
    model = NilaiEvaluasiPerMateri
    extra = 0
    can_delete = False
    readonly_fields = ('materi', 'nilai', 'total_soal', 'jumlah_benar')



# ADMIN CLASSES

@admin.register(NilaiEvaluasi)
class NilaiEvaluasiAdmin(admin.ModelAdmin):
    list_display = ('user', 'nilai', 'get_grade', 'is_passed', 'lihat_jawaban_btn', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('created_at',)

    fieldsets = (
        ('Hasil Evaluasi', {
            'fields': (('user', 'nilai'), ('total_soal', 'jumlah_benar'), 'rekomendasi_materi')
        }),
        ('Aksi', {
            'fields': ('link_detail_jawaban',),  # Tombol untuk pindah ke halaman jawaban
        }),
        ('Data Waktu', {
            'classes': ('collapse',),
            'fields': ('durasi_menit', 'created_at', 'updated_at'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'link_detail_jawaban')

    inlines = [NilaiPerMateriInline]

    def lihat_jawaban_btn(self, obj):

        url = reverse('admin:belajar_jawabanevaluasi_changelist') + f'?evaluasi__id__exact={obj.id}'
        return format_html('<a class="button" href="{}">Lihat Jawaban</a>', url)

    lihat_jawaban_btn.short_description = 'Detail'

    def link_detail_jawaban(self, obj):

        url = reverse('admin:belajar_jawabanevaluasi_changelist') + f'?evaluasi__id__exact={obj.id}'
        return format_html(
            '<a href="{}" class="button" style="background: #417690; color: white; padding: 10px 15px;">'
            'Buka Daftar Seluruh Jawaban Siswa Ini ({})'
            '</a>',
            url, obj.jawaban_evaluasi.count()
        )

    link_detail_jawaban.short_description = 'Jawaban Detail'


@admin.register(JawabanEvaluasi)
class JawabanEvaluasiAdmin(admin.ModelAdmin):
    list_display = ('nomor_soal', 'materi_soal', 'pertanyaan_singkat', 'jawaban_user', 'jawaban_benar', 'is_correct')
    list_filter = ('evaluasi', 'materi_soal', 'is_correct')
    search_fields = ('soal_pertanyaan',)
    readonly_fields = ('evaluasi', 'nomor_soal', 'materi_soal', 'soal_pertanyaan', 'pilihan_jawaban', 'jawaban_user',
                       'jawaban_benar', 'is_correct', 'poin')

    def pertanyaan_singkat(self, obj):
        return f"{obj.soal_pertanyaan[:60]}..." if len(obj.soal_pertanyaan) > 60 else obj.soal_pertanyaan



@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'kelas', 'created_at')
    list_filter = ('kelas',)


@admin.register(Kuis)
class KuisAdmin(admin.ModelAdmin):
    list_display = ('judul', 'guru', 'kelas_target', 'is_active')
    inlines = [SoalKuisInline]


@admin.register(KemajuanBelajar)
class KemajuanBelajarAdmin(admin.ModelAdmin):
    list_display = ('user', 'materi', 'progress_persentase', 'is_selesai')


@admin.register(SoalKuis)
class SoalKuisAdmin(admin.ModelAdmin):
    list_display = ('kuis', 'pertanyaan', 'jawaban_benar')


@admin.register(RiwayatKuis)
class RiwayatKuisAdmin(admin.ModelAdmin):
    list_display = ('siswa', 'kuis', 'nilai', 'tanggal_mengerjakan')