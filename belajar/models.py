from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

# --- HAPUS CLASS PROFILE YANG PERTAMA DI SINI ---


class NilaiEvaluasi(models.Model):
    """Model untuk menyimpan nilai evaluasi akhir (keseluruhan materi)"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="nilai_evaluasi"
    )
    nilai = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Nilai",
    )
    total_soal = models.IntegerField(
        default=0, validators=[MinValueValidator(0)], verbose_name="Total Soal"
    )
    jumlah_benar = models.IntegerField(
        default=0, validators=[MinValueValidator(0)], verbose_name="Jumlah Benar"
    )
    # ADD: Durasi pengerjaan untuk analytics
    durasi_menit = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Durasi Pengerjaan (menit)"
    )
    # ADD: Field untuk menyimpan hasil rekomendasi AI
    rekomendasi_materi = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Rekomendasi AI"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nilai Evaluasi Akhir"
        verbose_name_plural = "Nilai Evaluasi Akhir"
        db_table = "nilai_evaluasi"
        ordering = ["-created_at"]

    def __str__(self):
        nilai_str = f"{self.nilai:.1f}" if self.nilai else "Belum Ada"
        nama = self.user.get_full_name() or self.user.username
        return f"{nama} - Evaluasi Akhir - {nilai_str}"

    def get_grade(self):
        """Return letter grade based on score"""
        if not self.nilai:
            return "N/A"
        if self.nilai >= 90:
            return "A"
        elif self.nilai >= 80:
            return "B"
        elif self.nilai >= 70:
            return "C"
        elif self.nilai >= 60:
            return "D"
        else:
            return "E"

    def get_grade_color(self):
        """Return color for grade display"""
        grade = self.get_grade()
        colors = {
            "A": "green",
            "B": "blue",
            "C": "yellow",
            "D": "orange",
            "E": "red",
            "N/A": "gray",
        }
        return colors.get(grade, "gray")

    def is_passed(self):
        """Check if evaluation is passed (>= 70)"""
        return self.nilai and self.nilai >= 70

    def calculate_material_breakdown(self):
        """Calculate and save material breakdown after evaluation"""
        from collections import defaultdict

        # Group answers by material
        material_stats = defaultdict(lambda: {"benar": 0, "total": 0})

        for jawaban in self.jawaban_evaluasi.all():
            material_stats[jawaban.materi_soal]["total"] += 1
            if jawaban.is_correct:
                material_stats[jawaban.materi_soal]["benar"] += 1

        # Create or update NilaiEvaluasiPerMateri records
        for materi, stats in material_stats.items():
            if stats["total"] > 0:
                nilai_persen = (stats["benar"] / stats["total"]) * 100

                nilai_per_materi, created = (
                    NilaiEvaluasiPerMateri.objects.update_or_create(
                        evaluasi_utama=self,
                        materi=materi,
                        defaults={
                            "nilai": nilai_persen,
                            "total_soal": stats["total"],
                            "jumlah_benar": stats["benar"],
                        },
                    )
                )


class NilaiEvaluasiPerMateri(models.Model):
    """Model untuk menyimpan breakdown nilai per materi dari evaluasi akhir"""

    MATERI_CHOICES = [
        ("materi_1", "Materi 1"),
        ("materi_2", "Materi 2"),
        ("materi_3", "Materi 3"),
        ("materi_4", "Materi 4"),
        ("materi_5", "Materi 5"),
        ("materi_6", "Materi 6"),
    ]

    # CHANGE: Link to main evaluation instead of user directly
    evaluasi_utama = models.ForeignKey(
        NilaiEvaluasi,
        on_delete=models.CASCADE,
        related_name="breakdown_per_materi",
        verbose_name="Evaluasi Utama",
    )
    materi = models.CharField(
        max_length=50, choices=MATERI_CHOICES, verbose_name="Materi"
    )
    nilai = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Nilai (%)",
    )
    total_soal = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Total Soal Materi Ini",
    )
    jumlah_benar = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Jumlah Benar Materi Ini",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Breakdown Nilai Per Materi"
        verbose_name_plural = "Breakdown Nilai Per Materi"
        db_table = "nilai_evaluasi_per_materi"
        # CHANGE: Unique together should include evaluasi_utama
        unique_together = ["evaluasi_utama", "materi"]
        ordering = ["evaluasi_utama", "materi"]

    def __str__(self):
        nilai_str = f"{self.nilai:.1f}%" if self.nilai else "Belum Ada"
        return f"Evaluasi {self.evaluasi_utama.id} - {self.get_materi_display()} - {nilai_str}"

    def get_performance_status(self):
        """Get performance status for this material"""
        if not self.nilai:
            return "Belum Ada Data"
        elif self.nilai >= 80:
            return "Sangat Baik"
        elif self.nilai >= 70:
            return "Baik"
        elif self.nilai >= 60:
            return "Cukup"
        else:
            return "Perlu Perbaikan"

    def get_status_color(self):
        """Get color for status display"""
        if not self.nilai:
            return "gray"
        elif self.nilai >= 80:
            return "green"
        elif self.nilai >= 70:
            return "blue"
        elif self.nilai >= 60:
            return "yellow"
        else:
            return "red"


class JawabanEvaluasi(models.Model):
    """Model untuk menyimpan detail jawaban evaluasi"""

    MATERI_CHOICES = [
        ("materi_1", "Materi 1"),
        ("materi_2", "Materi 2"),
        ("materi_3", "Materi 3"),
        ("materi_4", "Materi 4"),
        ("materi_5", "Materi 5"),
        ("materi_6", "Materi 6"),
    ]

    evaluasi = models.ForeignKey(
        NilaiEvaluasi, on_delete=models.CASCADE, related_name="jawaban_evaluasi"
    )
    nomor_soal = models.IntegerField(
        validators=[MinValueValidator(1)], verbose_name="Nomor Soal"
    )
    materi_soal = models.CharField(
        max_length=50,
        choices=MATERI_CHOICES,
        verbose_name="Materi Soal",
        help_text="Materi asal dari soal ini",
    )
    soal_pertanyaan = models.TextField(verbose_name="Soal Pertanyaan")
    # ADD: Store answer choices for better review
    pilihan_jawaban = models.JSONField(
        default=list,
        verbose_name="Pilihan Jawaban",
        help_text="Array pilihan jawaban yang tersedia",
    )
    jawaban_user = models.TextField(blank=True, verbose_name="Jawaban User")
    jawaban_benar = models.TextField(verbose_name="Jawaban Benar")
    is_correct = models.BooleanField(default=False, verbose_name="Benar/Tidak")
    poin = models.FloatField(
        default=1.0, validators=[MinValueValidator(0.0)], verbose_name="Poin"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Jawaban Evaluasi"
        verbose_name_plural = "Jawaban Evaluasi"
        db_table = "jawaban_evaluasi"
        unique_together = ["evaluasi", "nomor_soal"]
        ordering = ["evaluasi", "nomor_soal"]

    def __str__(self):
        status = "Benar" if self.is_correct else "Salah"
        return (
            f"Evaluasi ID: {self.evaluasi.id} - Soal No: {self.nomor_soal} - {status}"
        )

    def get_materi_display_short(self):
        """Get short material name for display"""
        return (
            self.get_materi_soal_display().split(":")[0]
            if ":" in self.get_materi_soal_display()
            else self.get_materi_soal_display()
        )


class KemajuanBelajar(models.Model):
    """Model untuk tracking progress belajar per materi"""

    MATERI_CHOICES = [
        ("materi_1", "Materi 1"),
        ("materi_2", "Materi 2"),
        ("materi_3", "Materi 3"),
        ("materi_4", "Materi 4"),
        ("materi_5", "Materi 5"),
        ("materi_6", "Materi 6"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="kemajuan_belajar"
    )
    materi = models.CharField(
        max_length=50, choices=MATERI_CHOICES, verbose_name="Materi"
    )
    is_selesai = models.BooleanField(default=False, verbose_name="Selesai")
    progress_persentase = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Progress (%)",
    )
    waktu_mulai = models.DateTimeField(auto_now_add=True)
    waktu_selesai = models.DateTimeField(null=True, blank=True)
    catatan = models.TextField(blank=True, verbose_name="Catatan")

    class Meta:
        verbose_name = "Kemajuan Belajar"
        verbose_name_plural = "Kemajuan Belajar"
        unique_together = ["user", "materi"]
        db_table = "kemajuan_belajar"
        ordering = ["user", "materi"]

    def mark_completed(self):
        """Mark materi as completed"""
        self.is_selesai = True
        self.progress_persentase = 100.0
        self.waktu_selesai = timezone.now()
        self.save()

    def update_progress(self, persentase):
        """Update progress percentage"""
        if 0 <= persentase <= 100:
            self.progress_persentase = persentase
            if persentase >= 100:
                self.mark_completed()
            else:
                self.save()

    @classmethod
    def get_user_summary(cls, user):
        """Get summary of user's learning progress"""
        total_materi = len(cls.MATERI_CHOICES)
        selesai = cls.objects.filter(user=user, is_selesai=True).count()
        avg_progress = (
            cls.objects.filter(user=user).aggregate(models.Avg("progress_persentase"))[
                "progress_persentase__avg"
            ]
            or 0
        )

        return {
            "total_materi": total_materi,
            "materi_selesai": selesai,
            "persentase_keseluruhan": round((selesai / total_materi) * 100, 2),
            "rata_rata_progress": round(avg_progress, 2),
        }

    @classmethod
    def user_ready_for_evaluation(cls, user):
        """Check if user has completed all materials and ready for evaluation"""
        total_materi = len(cls.MATERI_CHOICES)
        selesai = cls.objects.filter(user=user, is_selesai=True).count()
        return selesai >= total_materi

    @classmethod
    def get_weak_materials(cls, user):
        """Get materials where user has low evaluation scores"""
        weak_materials = []

        # Get latest evaluation breakdown
        latest_eval = (
            NilaiEvaluasi.objects.filter(user=user).order_by("-created_at").first()
        )
        if latest_eval:
            for breakdown in latest_eval.breakdown_per_materi.filter(nilai__lt=70):
                weak_materials.append(
                    {
                        "materi": breakdown.get_materi_display(),
                        "materi_code": breakdown.materi,
                        "nilai": breakdown.nilai,
                        "status": breakdown.get_performance_status(),
                    }
                )

        return weak_materials

    def __str__(self):
        status = "Selesai" if self.is_selesai else f"{self.progress_persentase}%"
        nama = self.user.get_full_name() or self.user.username
        return f"{nama} - {self.get_materi_display()} ({status})"


class Profile(models.Model):
    KELAS_CHOICES = [
        ("kelas_2", "Kelas 2"),
        ("kelas_3", "Kelas 3"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    kelas = models.CharField(
        max_length=50,
        choices=KELAS_CHOICES,
        blank=True,
        null=True,
        verbose_name="Kelas",
    )
    # Ini yang benar, ada field foto-nya
    foto = models.ImageField(
        upload_to="profile_pics", blank=True, null=True, verbose_name="Foto Profil"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil Pengguna"
        verbose_name_plural = "Profil Pengguna"
        db_table = "profile"

    def __str__(self):
        kelas_display = self.get_kelas_display() if self.kelas else "Belum Set Kelas"
        nama = self.user.get_full_name() or self.user.username
        return f"{nama} - {kelas_display}"


class Kuis(models.Model):
    KELAS_CHOICES = [
        ("kelas_2", "Kelas 2"),
        ("kelas_3", "Kelas 3"),
    ]

    judul = models.CharField(max_length=200, verbose_name="Judul Kuis")
    deskripsi = models.TextField(blank=True, verbose_name="Deskripsi Singkat")
    guru = models.ForeignKey(User, on_delete=models.CASCADE, related_name="kuis_dibuat")
    kelas_target = models.CharField(
        max_length=20, choices=KELAS_CHOICES, verbose_name="Untuk Kelas"
    )
    durasi_menit = models.IntegerField(default=10, help_text="Durasi dalam menit")
    is_active = models.BooleanField(default=True, verbose_name="Aktifkan Kuis")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.judul} ({self.get_kelas_target_display()})"


class SoalKuis(models.Model):
    JAWABAN_CHOICES = [
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
    ]

    kuis = models.ForeignKey(Kuis, on_delete=models.CASCADE, related_name="daftar_soal")
    pertanyaan = models.TextField()

    gambar = models.ImageField(
        upload_to="soal_images/",
        blank=True,
        null=True,
        verbose_name="Gambar Soal",
        help_text="Upload gambar jika soal membutuhkan ilustrasi visual",
    )

    opsi_a = models.CharField(max_length=200, verbose_name="Pilihan A")
    opsi_b = models.CharField(max_length=200, verbose_name="Pilihan B")
    opsi_c = models.CharField(max_length=200, verbose_name="Pilihan C")
    opsi_d = models.CharField(max_length=200, verbose_name="Pilihan D")
    jawaban_benar = models.CharField(max_length=1, choices=JAWABAN_CHOICES)

    def __str__(self):
        return f"Soal: {self.pertanyaan[:50]}..."


class RiwayatKuis(models.Model):
    kuis = models.ForeignKey(Kuis, on_delete=models.CASCADE)
    siswa = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="riwayat_kuis"
    )
    nilai = models.FloatField()
    benar = models.IntegerField()
    salah = models.IntegerField()
    tanggal_mengerjakan = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.siswa.username} - {self.kuis.judul} - {self.nilai}"
