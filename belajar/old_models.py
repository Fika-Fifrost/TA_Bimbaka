from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil Pengguna"
        verbose_name_plural = "Profil Pengguna"
        db_table = "profile"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_kelas_display()}"


class Materi(models.Model):
    KELAS_CHOICES = [
        ("kelas_2", "Kelas 2"),
        ("kelas_3", "Kelas 3"),
    ]

    nomor = models.IntegerField(
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Nomor Materi",
    )
    nama = models.CharField(max_length=100, verbose_name="Nama Materi")
    kelas = models.CharField(
        max_length=50,
        choices=KELAS_CHOICES,
        blank=True,
        null=True,
        verbose_name="Kelas",
    )
    deskripsi = models.TextField(blank=True, verbose_name="Deskripsi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")

    class Meta:
        verbose_name = "Materi"
        verbose_name_plural = "Materi"
        ordering = ["nomor"]
        db_table = "materi"

    def __str__(self):
        return f"Materi {self.nomor} Kelas {self.get_kelas_display()}: {self.nama}"


class KemajuanBelajar(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="kemajuan_belajar"
    )
    materi = models.ForeignKey(
        Materi, on_delete=models.CASCADE, related_name="kemajuan"
    )
    is_selesai = models.BooleanField(default=False, verbose_name="Selesai")
    tanggal_mulai = models.DateTimeField(auto_now_add=True)
    tanggal_selesai = models.DateTimeField(null=True, blank=True)
    progress_persentase = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Progress (%)",
    )

    class Meta:
        verbose_name = "Kemajuan Belajar"
        verbose_name_plural = "Kemajuan Belajar"
        unique_together = ["user", "materi"]
        ordering = ["user", "materi__nomor"]
        db_table = "kemajuan_belajar"

    def __str__(self):
        status = "Selesai" if self.is_selesai else f"{self.progress_persentase}%"
        return f"{self.user.get_full_name()} - {self.materi.nama} ({status})"

    def mark_completed(self):
        """Mark materi as completed"""
        from django.utils import timezone

        self.is_selesai = True
        self.progress_persentase = 100.0
        self.tanggal_selesai = timezone.now()
        self.save()

    @classmethod
    def get_user_progress_summary(cls, user):
        """Get summary of user's learning progress"""
        total_materi = Materi.objects.filter(is_active=True).count()
        selesai = cls.objects.filter(user=user, is_selesai=True).count()
        return {
            "total_materi": total_materi,
            "materi_selesai": selesai,
            "persentase_keseluruhan": (
                (selesai / total_materi * 100) if total_materi > 0 else 0
            ),
        }


class NilaiEvaluasi(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="nilai_evaluasi"
    )
    materi = models.ForeignKey(
        Materi, on_delete=models.CASCADE, related_name="evaluasi"
    )
    nilai = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Nilai",
    )
    jumlah_soal = models.IntegerField(
        validators=[MinValueValidator(1)], verbose_name="Jumlah Soal"
    )
    jumlah_benar = models.IntegerField(
        validators=[MinValueValidator(0)], verbose_name="Jumlah Benar"
    )
    waktu_pengerjaan = models.DurationField(null=True, blank=True)
    tanggal_evaluasi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Nilai Evaluasi"
        verbose_name_plural = "Nilai Evaluasi"
        unique_together = ["user", "materi"]
        ordering = ["-tanggal_evaluasi"]
        db_table = "nilai_evaluasi"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.materi.nama} - Nilai: {self.nilai}"

    def clean(self):
        if self.jumlah_benar > self.jumlah_soal:
            raise ValidationError("Jumlah benar tidak boleh lebih dari jumlah soal")

    def save(self, *args, **kwargs):
        # Auto calculate nilai based on correct answers
        if self.jumlah_soal > 0:
            self.nilai = (self.jumlah_benar / self.jumlah_soal) * 100
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_lulus(self):
        """Check if user passed the evaluation (>= 70)"""
        return self.nilai >= 70.0

    @classmethod
    def get_user_average(cls, user):
        """Get user's average score across all evaluations"""
        evaluations = cls.objects.filter(user=user)
        if evaluations.exists():
            return evaluations.aggregate(models.Avg("nilai"))["nilai__avg"]
        return 0.0


class HasilJawabanEvaluasi(models.Model):
    evaluasi = models.ForeignKey(
        NilaiEvaluasi, on_delete=models.CASCADE, related_name="jawaban_detail"
    )
    nomor_soal = models.IntegerField(
        validators=[MinValueValidator(1)], verbose_name="Nomor Soal"
    )
    soal = models.TextField(verbose_name="Soal")
    jawaban_user = models.CharField(max_length=255, verbose_name="Jawaban User")
    jawaban_benar = models.CharField(max_length=255, verbose_name="Jawaban Benar")
    is_benar = models.BooleanField(default=False, verbose_name="Benar")
    poin = models.FloatField(default=1.0, verbose_name="Poin")
    tanggal_jawaban = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Detail Jawaban Evaluasi"
        verbose_name_plural = "Detail Jawaban Evaluasi"
        unique_together = ["evaluasi", "nomor_soal"]
        ordering = ["evaluasi", "nomor_soal"]
        db_table = "hasil_jawaban_evaluasi"

    def __str__(self):
        status = "Benar" if self.is_benar else "Salah"
        return f"{self.evaluasi.user.get_full_name()} - {self.evaluasi.materi.nama} - Soal {self.nomor_soal} ({status})"

    def save(self, *args, **kwargs):
        # Auto check if answer is correct
        self.is_benar = (
            self.jawaban_user.strip().lower() == self.jawaban_benar.strip().lower()
        )
        super().save(*args, **kwargs)

    @property
    def user(self):
        """Get user from related evaluasi"""
        return self.evaluasi.user

    @property
    def materi(self):
        """Get materi from related evaluasi"""
        return self.evaluasi.materi


# Helper model for statistics
class StatistikPengguna(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="statistik"
    )
    total_waktu_belajar = models.DurationField(default="0:00:00")
    materi_favorit = models.ForeignKey(
        Materi, on_delete=models.SET_NULL, null=True, blank=True, related_name="fans"
    )
    streak_hari = models.IntegerField(default=0, verbose_name="Streak Belajar (Hari)")
    terakhir_aktif = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Statistik Pengguna"
        verbose_name_plural = "Statistik Pengguna"
        db_table = "statistik_pengguna"

    def __str__(self):
        return f"Statistik {self.user.get_full_name()}"
