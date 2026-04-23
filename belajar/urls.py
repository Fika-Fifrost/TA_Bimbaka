from django.urls import path
from . import views

urlpatterns = [
    # --- HALAMAN UTAMA ---
    path("", views.beranda, name="beranda"),
    # --- MATERI ---
    path("materi/", views.materi, name="materi"),
    path("materi/<int:materi_id>/", views.materi_detail, name="materi_detail"),
    path(
        "selesai-materi/<int:materi_id>/",
        views.mark_materi_completed,
        name="mark_materi_completed",
    ),
    # --- FITUR KUIS (GURU & SISWA)
    path("guru/kuis/", views.daftar_kuis_guru, name="daftar_kuis_guru"),
    path("guru/kuis/buat/", views.buat_kuis, name="buat_kuis"),
    path("guru/kuis/<int:kuis_id>/soal/", views.tambah_soal, name="tambah_soal"),
    path("guru/kuis/<int:kuis_id>/hapus/", views.hapus_kuis, name="hapus_kuis"),
    path("kuis/<int:kuis_id>/kerjakan/", views.kerjakan_kuis, name="kerjakan_kuis"),
    # --- EVALUASI ---
    path("evaluasi/", views.evaluasi, name="evaluasi"),
    path("hasil-evaluasi/", views.hasil_evaluasi, name="hasil_evaluasi"),
    path("riwayat-evaluasi/", views.riwayat_evaluasi, name="riwayat_evaluasi"),
    path("export-nilai-excel/", views.export_nilai_excel, name="export_nilai_excel"),
    # --- FITUR GURU ---
    path("guru-nilai/", views.guru_nilai, name="guru_nilai"),
    path(
        "riwayat-siswa/<int:siswa_id>/",
        views.guru_riwayat_siswa,
        name="guru_riwayat_siswa",
    ),
    path("guru/siswa/", views.guru_daftar_siswa, name="guru_daftar_siswa"),
    path("guru/siswa/tambah/", views.tambah_siswa, name="tambah_siswa"),
    path("guru/siswa/<int:siswa_id>/edit/", views.edit_siswa, name="edit_siswa"),
    path("guru/siswa/<int:siswa_id>/hapus/", views.hapus_siswa, name="hapus_siswa"),
    path(
        "guru/kuis/<int:kuis_id>/nilai/",
        views.lihat_nilai_kuis,
        name="lihat_nilai_kuis",
    ),
    path(
        "guru/kuis/<int:kuis_id>/toggle/",
        views.toggle_status_kuis,
        name="toggle_status_kuis",
    ),
    # --- AUTHENTICATION ---
    path("masuk/", views.masuk, name="masuk"),
    path("daftar/", views.daftar, name="daftar"),
    path("keluar/", views.keluar, name="keluar"),
    path("profil/edit/", views.edit_profile, name="edit_profile"),
    path("profil/hapus-foto/", views.hapus_foto_profil, name="hapus_foto_profil"),
]
