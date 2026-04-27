import random
import os
import joblib
import pandas as pd
from openpyxl import Workbook

from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Avg, Count, Q
from django.contrib.auth import update_session_auth_hash

# --- IMPORT FORMS (Pastikan forms.py sudah diupdate) ---
from .forms import UserUpdateForm, ProfileUpdateForm, KuisForm, SoalKuisForm

# --- IMPORT MODELS (LENGKAP) ---
from .models import (
    Profile,
    NilaiEvaluasi,
    JawabanEvaluasi,
    KemajuanBelajar,
    NilaiEvaluasiPerMateri,
    Kuis,
    SoalKuis,
    RiwayatKuis,
)


# --- FUNGSI HELPER ---
def is_guru(user):
    """Cek apakah user ada di grup 'Guru'"""
    return user.is_authenticated and user.groups.filter(name="Guru").exists()


def generate_soal_evaluasi_akhir(jumlah_soal=24, kelas="kelas_2"):
    """
    KELAS 2: 4 soal per materi (24 total)
    - Materi 1: Penjumlahan Berulang (visual + text)
    - Materi 2: Sifat Komutatif (a×b dan b×a)
    - Materi 3: Perkalian 1 & 0 (fokus pada 1 dan 0)
    - Materi 4: Perkalian 2 & 5 (hanya 2 atau 5)
    - Materi 5: Perkalian 10 (hanya ×10)
    - Materi 6: Tabel Perkalian (random 3-9)

    KELAS 3: 4 soal per materi (24 total)
    - Materi 1: Perkalian 0, 10, 100
    - Materi 2: Perkalian Bersusun (2 digit × 1 digit)
    - Materi 3: Pembagian 1 & 0
    - Materi 4: Pembagian Bersusun (2+ digit ÷ 1 digit)
    - Materi 5: Operasi Campuran (a×b)+c
    - Materi 6: Soal Cerita
    """
    soal = []

    # SOAL KELAS 2 - SPESIFIK PER MATERI
    if kelas == "kelas_2":
        for materi_id in range(1, 7):
            for _ in range(4):  # 4 soal per materi
                question_data = {}
                jawaban = 0

                if materi_id == 1:
                    # MATERI 1: Penjumlahan Berulang (Visual + Text)
                    if random.choice([True, False]):
                        # Soal Visual
                        a = random.randint(2, 5)
                        b = random.randint(2, 4)
                        jawaban = a * b
                        question_data = {
                            "type": "visual",
                            "question_text": "Berapa hasil dari apel di atas?",
                            "a_range": [1] * a,
                            "b_range": [1] * b,
                            # TAMBAHKAN DUA BARIS DI BAWAH INI:
                            "bilangan_1": a,
                            "bilangan_2": b,
                            "op": "×",
                            "icon": "🍎",
                        }


                    else:
                        # Soal Text
                        a = random.randint(2, 5)
                        b = random.randint(2, 4)
                        jawaban = a * b
                        # Membuat deret "4 + 4 + 4" secara dinamis
                        penjumlahan_str = " + ".join([str(b)] * a)
                        # Menampilkan perkalian dan penjumlahannya sekaligus
                        question_data = {
                            "type": "text",
                            "question_text": f"Berapakah {a} × {b} = {penjumlahan_str} = ?",
                        }

                elif materi_id == 2:
                    # MATERI 2: Sifat Komutatif (a×b = b×a)
                    # Fokus pada pertukaran angka
                    a = random.randint(3, 9)
                    b = random.randint(2, 8)
                    jawaban = a * b

                    if random.choice([True, False]):
                        # Soal dalam urutan a × b
                        question_data = {
                            "type": "text",
                            "question_text": f"Berapakah {a} × {b}?",
                        }
                    else:
                        # Soal dalam urutan b × a (terbalik)
                        question_data = {
                            "type": "text",
                            "question_text": f"Berapakah {b} × {a}?",
                        }

                elif materi_id == 3:
                    # MATERI 3: Perkalian 1 & 0
                    # 2 soal dengan ×1 dan 2 soal dengan ×0
                    pengali = random.choice([0, 1])
                    a = random.randint(5, 20)
                    jawaban = a * pengali

                    if pengali == 1:
                        question_data = {
                            "type": "text",
                            "question_text": f"Berapakah {a} × 1?",
                        }
                    else:
                        question_data = {
                            "type": "text",
                            "question_text": f"Berapakah {a} × 0?",
                        }

                elif materi_id == 4:
                    # MATERI 4: Perkalian 2 & 5
                    # Hanya perkalian dengan 2 atau 5
                    pengali = random.choice([2, 5])
                    a = random.randint(3, 9)
                    jawaban = a * pengali
                    question_data = {
                        "type": "text",
                        "question_text": f"Berapakah {a} × {pengali}?",
                    }

                elif materi_id == 5:
                    # MATERI 5: Perkalian 10
                    # Semua soal ×10
                    a = random.randint(2, 9)
                    jawaban = a * 10
                    question_data = {
                        "type": "text",
                        "question_text": f"Berapakah {a} × 10?",
                    }

                else:  # materi_id == 6
                    # MATERI 6: Tabel Perkalian (3-9)
                    a = random.randint(3, 9)
                    b = random.randint(3, 9)
                    jawaban = a * b
                    question_data = {
                        "type": "text",
                        "question_text": f"Berapakah {a} × {b}?",
                    }

                # Buat pilihan jawaban
                pilihan = [str(jawaban)]
                while len(pilihan) < 4:
                    wrong = jawaban + random.randint(-5, 5)
                    if wrong != jawaban and wrong >= 0 and str(wrong) not in pilihan:
                        pilihan.append(str(wrong))
                random.shuffle(pilihan)

                # Tambahkan pilihan dan materi ke soal
                question_data.update(
                    {
                        "choices": pilihan,
                        "correct_answer": str(jawaban),
                        "materi": f"materi_{materi_id}",
                    }
                )
                soal.append(question_data)

    # SOAL KELAS 3 - SPESIFIK PER MATERI
    elif kelas == "kelas_3":
        for materi_id in range(1, 7):
            for _ in range(4):  # 4 soal per materi
                question_data = {}
                jawaban = 0

                if materi_id == 1:
                    # MATERI 1: Perkalian 0, 10, 100
                    a = random.randint(1, 12)
                    b = random.choice([0, 10, 100])
                    jawaban = a * b
                    question_data = {
                        "type": "text",
                        "question_text": f"Berapakah {a} × {b}?",
                    }

                elif materi_id == 2:
                    # MATERI 2: Perkalian Bersusun (2 digit × 1 digit)
                    # Hasil tidak lebih dari 200
                    b = random.randint(2, 9)  # Pengali 2-9
                    a = random.randint(10, int(200 / b))
                    jawaban = a * b

                    question_data = {
                        "type": "susun_multiply",
                        "question_text": "Berapakah hasil perkalian di bawah?",
                        "bilangan_1": a,
                        "bilangan_2": b,
                    }


                elif materi_id == 3:
                    # MATERI 3: Pembagian 1 & 0
                    # 2 soal dengan ÷1 dan 2 soal dengan ÷ (dengan hasil menunjukkan sifat 0)
                    if random.choice([True, False]):
                        # Pembagian dengan 1
                        a = random.randint(5, 50)
                        jawaban = a // 1
                        question_data = {
                            "type": "text",
                            "question_text": f"Berapakah {a} ÷ 1?",
                        }
                    else:
                        # Pembagian 0 dibagi bilangan apapun = 0
                        b = random.randint(2, 9)
                        jawaban = 0
                        question_data = {
                            "type": "text",
                            "question_text": f"Berapakah 0 ÷ {b}?",
                        }



                elif materi_id == 4:

                    # MATERI 4: Pembagian Bersusun POROGAPIT
                    # Hasil bagi (quotient) dibatasi 11-20 agar sangat ramah untuk anak kelas 3
                    divisor = random.randint(2, 5)  # Pembagi 2-5
                    quotient = random.randint(11, 20)  # Hasil belasan sampai 20 saja
                    dividend = divisor * quotient
                    jawaban = quotient
                    question_data = {
                        "type": "susun_divide",
                        "question_text": "Berapakah hasil pembagian di bawah?",
                        "dividend": dividend,
                        "divisor": divisor,
                    }

                elif materi_id == 5:
                    # MATERI 5: Operasi Campuran (a×b)+c
                    a = random.randint(2, 9)
                    b = random.randint(2, 9)
                    c = random.randint(1, 20)
                    jawaban = (a * b) + c
                    question_data = {
                        "type": "text",
                        "question_text": f"Berapakah ({a} × {b}) + {c}?",
                    }

                else:  # materi_id == 6
                    # MATERI 6: Soal Cerita
                    items = random.randint(3, 8)
                    per_group = random.randint(2, 6)
                    given_away = random.randint(1, items * per_group // 2)
                    jawaban = (items * per_group) - given_away
                    question_data = {
                        "type": "text",
                        "question_text": f"Ana punya {items} kotak. Tiap kotak isi {per_group} permen. Diberikan {given_away}. Berapa sisanya?",
                    }

                # Buat pilihan jawaban
                pilihan = [str(jawaban)]
                while len(pilihan) < 4:
                    wrong = jawaban + random.randint(-10, 10)
                    if wrong != jawaban and wrong >= 0 and str(wrong) not in pilihan:
                        pilihan.append(str(wrong))
                random.shuffle(pilihan)

                # Tambahkan pilihan dan materi ke soal
                question_data.update(
                    {
                        "choices": pilihan,
                        "correct_answer": str(jawaban),
                        "materi": f"materi_{materi_id}",
                    }
                )
                soal.append(question_data)

    random.shuffle(soal)
    return soal


# --- HELPER MINI QUIZ (DRAG & DROP) ---
def get_mini_quiz(kelas, materi_id):
    pairs = []
    generated_answers = set()
    target_pairs = 3
    attempts = 0

    while len(pairs) < target_pairs and attempts < 20:
        attempts += 1
        q_text = ""
        a_text = ""

        if kelas == "kelas_2":
            if materi_id == 1:
                n = random.randint(2, 5)
                val = random.randint(2, 5)
                q_text = " + ".join([str(val)] * n)
                a_text = f"{n} × {val}"
            elif materi_id == 2:
                a = random.randint(3, 9)
                b = random.randint(2, 8)
                q_text = f"{a} × {b}"
                a_text = f"{b} × {a}"
            elif materi_id == 3:
                val = random.randint(5, 20)
                pengali = random.choice([0, 1])
                q_text = f"{val} × {pengali}"
                a_text = str(val * pengali)
            elif materi_id == 4:
                a = random.randint(3, 9)
                b = random.choice([2, 5])
                q_text = f"{a} × {b}"
                a_text = str(a * b)
            elif materi_id == 5:
                a = random.randint(2, 9)
                q_text = f"{a} × 10"
                a_text = f"{a}0"
            else:
                a = random.randint(3, 8)
                b = random.randint(3, 8)
                q_text = f"{a} × {b}"
                a_text = str(a * b)

        elif kelas == "kelas_3":
            if materi_id == 1:
                a = random.randint(2, 9)
                b = random.choice([10, 100])
                q_text = f"{a} × {b}"
                a_text = str(a * b)
            elif materi_id == 2:
                a = random.randint(11, 20)
                b = random.choice([2, 3])
                q_text = f"{a} × {b}"
                a_text = str(a * b)
            elif materi_id == 3:
                if random.choice([True, False]):
                    q_text = f"0 ÷ {random.randint(2, 9)}"
                    a_text = "0"
                else:
                    val = random.randint(5, 20)
                    q_text = f"{val} ÷ 1"
                    a_text = str(val)
            elif materi_id == 4:
                res = random.randint(10, 20)
                div = random.randint(2, 3)
                q_text = f"{res * div} ÷ {div}"
                a_text = str(res)
            elif materi_id == 5:
                a = random.randint(2, 5)
                b = random.randint(2, 4)
                c = random.randint(1, 5)
                q_text = f"({a}×{b}) + {c}"
                a_text = str((a * b) + c)
            else:
                item = random.randint(3, 6)
                price = random.randint(2, 5)
                q_text = f"{item} kotak isi {price}"
                a_text = str(item * price)

        if a_text not in generated_answers:
            generated_answers.add(a_text)
            pairs.append({"id": len(pairs) + 1, "question": q_text, "answer": a_text})

    questions = pairs[:]
    answers = pairs[:]
    random.shuffle(answers)
    return {
        "type": "drag_drop",
        "questions": questions,
        "answers": answers,
        "total_pairs": len(pairs),
    }


# --- VIEW BERANDA (GABUNGAN + KUIS) ---
@login_required
def beranda(request):
    # 1. LOGIKA GURU
    if is_guru(request.user):
        try:
            guru_kelas = request.user.profile.kelas
        except Profile.DoesNotExist:
            guru_kelas = None

        if guru_kelas:
            siswa_list = User.objects.filter(
                groups__name="Siswa", profile__kelas=guru_kelas
            )
            total_siswa = siswa_list.count()
            siswa_lulus = (
                NilaiEvaluasi.objects.filter(user__in=siswa_list, nilai__gte=70)
                .values("user")
                .distinct()
                .count()
            )
            siswa_aktif = (
                KemajuanBelajar.objects.filter(user__in=siswa_list)
                .values("user")
                .distinct()
                .count()
            )
            recent_evals = NilaiEvaluasi.objects.filter(user__in=siswa_list).order_by(
                "-created_at"
            )[:5]
            breakdown_stats = (
                NilaiEvaluasiPerMateri.objects.filter(
                    evaluasi_utama__user__in=siswa_list
                )
                .values("materi")
                .annotate(avg_nilai=Avg("nilai"))
                .order_by("materi")
            )
            chart_labels = [
                item["materi"].replace("_", " ").title() for item in breakdown_stats
            ]
            chart_data = [round(item["avg_nilai"], 1) for item in breakdown_stats]
            if not chart_labels:
                chart_labels = [
                    "Materi 1",
                    "Materi 2",
                    "Materi 3",
                    "Materi 4",
                    "Materi 5",
                    "Materi 6",
                ]
                chart_data = [0, 0, 0, 0, 0, 0]
        else:
            siswa_list = User.objects.none()
            total_siswa = 0
            siswa_lulus = 0
            siswa_aktif = 0
            recent_evals = []
            chart_labels = []
            chart_data = []

        context = {
            "total_siswa": total_siswa,
            "siswa_lulus": siswa_lulus,
            "siswa_aktif": siswa_aktif,
            "siswa_list": siswa_list,
            "guru_kelas": guru_kelas,
            "recent_evals": recent_evals,
            "chart_labels": chart_labels,
            "chart_data": chart_data,
        }
        return render(request, "pages/dasbor_guru.html", context)

    # 2. LOGIKA SISWA
    else:
        progress_summary = KemajuanBelajar.get_user_summary(request.user)
        ready_for_evaluation = KemajuanBelajar.user_ready_for_evaluation(request.user)
        recent_evals = NilaiEvaluasi.objects.filter(user=request.user).order_by(
            "-created_at"
        )[:5]
        recent_progress = KemajuanBelajar.objects.filter(
            user=request.user, is_selesai=True
        ).order_by("-waktu_selesai")[:5]

        activities = []
        for e in recent_evals:
            activities.append(
                {
                    "type": "evaluasi",
                    "time": e.created_at,
                    "nilai": e.nilai,
                    "judul": "Evaluasi Akhir",
                    "desc": f"Mendapat nilai {int(e.nilai)}",
                }
            )
        for p in recent_progress:
            activities.append(
                {
                    "type": "materi",
                    "time": p.waktu_selesai,
                    "nilai": None,
                    "judul": p.get_materi_display(),
                    "desc": "Telah menyelesaikan materi ini",
                }
            )

        activities.sort(key=lambda x: x["time"], reverse=True)
        recent_activities = activities[:5]
        latest_evaluation = (
            NilaiEvaluasi.objects.filter(user=request.user)
            .order_by("-created_at")
            .first()
        )

        # LOGIKA KUIS SISWA
        try:
            kelas_siswa = request.user.profile.kelas
        except AttributeError:
            kelas_siswa = None

        daftar_kuis = []
        if kelas_siswa:
            daftar_kuis = Kuis.objects.filter(
                kelas_target=kelas_siswa, is_active=True
            ).order_by("-created_at")
            riwayat_user = RiwayatKuis.objects.filter(siswa=request.user)
            riwayat_map = {r.kuis_id: r.nilai for r in riwayat_user}

            for k in daftar_kuis:
                if k.id in riwayat_map:
                    k.sudah_dikerjakan = True
                    k.nilai_kamu = riwayat_map[k.id]
                else:
                    k.sudah_dikerjakan = False
                    k.nilai_kamu = None

        context = {
            "progress_summary": progress_summary,
            "ready_for_evaluation": ready_for_evaluation,
            "latest_evaluation": latest_evaluation,
            "recent_activities": recent_activities,
            "daftar_kuis": daftar_kuis,
        }
        return render(request, "pages/beranda.html", context)


# --- VIEW MATERI ---
@login_required
def materi(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    kelas = profile.kelas or "kelas_2"
    if kelas == "kelas_3":
        materi_info = {
            "materi_1": {"id": 1, "title": "Perkalian 0, 10, 100", "icon": "💯"},
            "materi_2": {"id": 2, "title": "Perkalian Bersusun", "icon": "📝"},
            "materi_3": {"id": 3, "title": "Pembagian 1 & 0", "icon": "🧠"},
            "materi_4": {"id": 4, "title": "Pembagian Bersusun", "icon": "🏠"},
            "materi_5": {"id": 5, "title": "Operasi Campuran", "icon": "🧮"},
            "materi_6": {"id": 6, "title": "Soal Cerita", "icon": "🌍"},
        }
        header_title = "Matematika Kelas 3"
        header_desc = "Pilih materi untuk melanjutkan petualanganmu!"
    else:
        materi_info = {
            "materi_1": {"id": 1, "title": "Penjumlahan Berulang", "icon": "🍎"},
            "materi_2": {"id": 2, "title": "Sifat Komutatif", "icon": "🔄"},
            "materi_3": {"id": 3, "title": "Perkalian 1 & 0", "icon": "⭕"},
            "materi_4": {"id": 4, "title": "Perkalian 2 & 5", "icon": "✌️"},
            "materi_5": {"id": 5, "title": "Perkalian 10", "icon": "🔟"},
            "materi_6": {"id": 6, "title": "Tabel Perkalian", "icon": "📊"},
        }
        header_title = "Matematika Kelas 2"
        header_desc = "Belajar matematika yang menyenangkan! Mulai dari sini!"

    progress_db = KemajuanBelajar.objects.filter(user=request.user)
    progress_data = {p.materi: p for p in progress_db}
    learning_path = []
    active_lesson_found = False
    total_selesai = 0

    for key in sorted(materi_info.keys()):
        info = materi_info[key]
        progress = progress_data.get(key)
        is_selesai = progress.is_selesai if progress else False
        status = "locked"
        if is_selesai:
            status = "completed"
            total_selesai += 1
        elif not active_lesson_found:
            status = "active"
            active_lesson_found = True
        info["status"] = status
        info["key"] = key
        learning_path.append(info)

    total_materi = len(materi_info)
    progress_percentage = (
        (total_selesai / total_materi) * 100 if total_materi > 0 else 0
    )
    context = {
        "learning_path": learning_path,
        "header_title": header_title,
        "header_desc": header_desc,
        "total_selesai": total_selesai,
        "total_materi": total_materi,
        "progress_percentage": progress_percentage,
    }
    return render(request, "pages/materi.html", context)


@login_required
def materi_detail(request, materi_id):
    if materi_id not in range(1, 7):
        messages.error(request, "Materi tidak ditemukan!")
        return redirect("materi")

    profile, created = Profile.objects.get_or_create(user=request.user)
    kelas = profile.kelas or "kelas_2"

    kemajuan, created = KemajuanBelajar.objects.get_or_create(
        user=request.user,
        materi=f"materi_{materi_id}",
        defaults={"progress_persentase": 50.0},
    )
    if created or kemajuan.progress_persentase < 50:
        kemajuan.progress_persentase = 50.0
        kemajuan.save()

    template_name = f"pages/materi/{kelas}/materi_{materi_id}.html"
    quiz_data = get_mini_quiz(kelas, materi_id)

    context = {"materi_id": materi_id, "quiz_data": quiz_data}
    return render(request, template_name, context)


@login_required
def mark_materi_completed(request, materi_id):
    if materi_id not in range(1, 7):
        messages.error(request, "Materi tidak ditemukan!")
        return redirect("materi")
    kemajuan, created = KemajuanBelajar.objects.get_or_create(
        user=request.user,
        materi=f"materi_{materi_id}",
        defaults={"progress_persentase": 0.0},
    )
    kemajuan.mark_completed()
    messages.success(request, f"Materi {materi_id} berhasil ditandai sebagai selesai!")
    return redirect("materi")


# --- MANAJEMEN KUIS (GURU) ---
@login_required
@user_passes_test(is_guru, login_url="beranda")
def daftar_kuis_guru(request):
    """Halaman untuk guru melihat kuis yang dibuatnya"""
    kuis_list = Kuis.objects.filter(guru=request.user).order_by("-created_at")
    return render(request, "pages/guru/daftar_kuis.html", {"kuis_list": kuis_list})


@login_required
@user_passes_test(is_guru, login_url="beranda")
def buat_kuis(request):
    """Halaman membuat kuis baru"""
    if request.method == "POST":
        form = KuisForm(request.POST)
        if form.is_valid():
            kuis = form.save(commit=False)
            kuis.guru = request.user
            kuis.save()
            messages.success(request, "Kuis berhasil dibuat! Silakan tambah soal.")
            return redirect("tambah_soal", kuis_id=kuis.id)
    else:
        form = KuisForm()
    return render(
        request, "pages/guru/form_kuis.html", {"form": form, "title": "Buat Kuis Baru"}
    )


@login_required
@user_passes_test(is_guru, login_url="beranda")
def tambah_soal(request, kuis_id):
    """Halaman menambah soal ke dalam kuis"""
    kuis = get_object_or_404(Kuis, id=kuis_id, guru=request.user)
    soal_list = kuis.daftar_soal.all()
    if request.method == "POST":
        form = SoalKuisForm(request.POST, request.FILES)
        if form.is_valid():
            soal = form.save(commit=False)
            soal.kuis = kuis
            soal.save()
            messages.success(request, "Soal berhasil ditambahkan!")
            return redirect("tambah_soal", kuis_id=kuis.id)
    else:
        form = SoalKuisForm()
    context = {"kuis": kuis, "form": form, "soal_list": soal_list}
    return render(request, "pages/guru/tambah_soal.html", context)


@login_required
@user_passes_test(is_guru, login_url="beranda")
def edit_soal(request, kuis_id, soal_id):
    """Halaman untuk mengedit soal kuis"""
    kuis = get_object_or_404(Kuis, id=kuis_id, guru=request.user)
    soal = get_object_or_404(SoalKuis, id=soal_id, kuis=kuis)
    soal_list = kuis.daftar_soal.all()  # Opsional jika ingin tetap menampilkan daftar soal

    if request.method == "POST":
        form = SoalKuisForm(request.POST, request.FILES, instance=soal)
        if form.is_valid():
            form.save()
            messages.success(request, "Soal berhasil diperbarui!")
            # Setelah berhasil edit, kembali ke halaman tambah soal untuk melihat daftarnya
            return redirect("tambah_soal", kuis_id=kuis.id)
    else:
        # Isi form dengan data soal yang sudah ada
        form = SoalKuisForm(instance=soal)

    context = {"kuis": kuis, "form": form, "soal": soal, "soal_list": soal_list}
    return render(request, "pages/guru/edit_soal.html", context)


@login_required
@user_passes_test(is_guru, login_url="beranda")
def hapus_soal(request, kuis_id, soal_id):
    """Fungsi untuk menghapus soal kuis"""
    kuis = get_object_or_404(Kuis, id=kuis_id, guru=request.user)
    soal = get_object_or_404(SoalKuis, id=soal_id, kuis=kuis)

    soal.delete()
    messages.success(request, "Soal berhasil dihapus!")
    return redirect("tambah_soal", kuis_id=kuis.id)

@login_required
@user_passes_test(is_guru, login_url="beranda")
def hapus_kuis(request, kuis_id):
    kuis = get_object_or_404(Kuis, id=kuis_id, guru=request.user)
    kuis.delete()
    messages.success(request, "Kuis berhasil dihapus.")
    return redirect("daftar_kuis_guru")


@login_required
@user_passes_test(is_guru, login_url="beranda")
def toggle_status_kuis(request, kuis_id):
    """Mengubah status aktif/non-aktif kuis"""
    kuis = get_object_or_404(Kuis, id=kuis_id, guru=request.user)

    # Balik statusnya (True jadi False, False jadi True)
    kuis.is_active = not kuis.is_active
    kuis.save()

    status_msg = "diaktifkan" if kuis.is_active else "dinonaktifkan"
    messages.success(request, f'Kuis "{kuis.judul}" berhasil {status_msg}.')
    return redirect("daftar_kuis_guru")


@login_required
@user_passes_test(is_guru, login_url="beranda")
def lihat_nilai_kuis(request, kuis_id):
    """Halaman untuk melihat hasil pengerjaan siswa pada kuis tertentu"""
    kuis = get_object_or_404(Kuis, id=kuis_id, guru=request.user)

    # Ambil semua riwayat pengerjaan untuk kuis ini
    riwayat_list = (
        RiwayatKuis.objects.filter(kuis=kuis).select_related("siswa").order_by("-nilai")
    )

    context = {
        "kuis": kuis,
        "riwayat_list": riwayat_list,
        "total_responden": riwayat_list.count(),
    }
    return render(request, "pages/guru/lihat_nilai_kuis.html", context)


# --- KERJAKAN KUIS (SISWA) ---
@login_required
def kerjakan_kuis(request, kuis_id):
    kuis = get_object_or_404(Kuis, id=kuis_id)
    cek_riwayat = RiwayatKuis.objects.filter(kuis=kuis, siswa=request.user).exists()
    if cek_riwayat:
        messages.info(request, "Kamu sudah mengerjakan kuis ini sebelumnya.")
        return redirect("beranda")

    if request.method == "POST":
        score = 0
        benar = 0
        salah = 0
        total_soal = kuis.daftar_soal.count()
        for soal in kuis.daftar_soal.all():
            if request.POST.get(f"soal_{soal.id}") == soal.jawaban_benar:
                benar += 1
            else:
                salah += 1
        if total_soal > 0:
            score = (benar / total_soal) * 100
        RiwayatKuis.objects.create(
            kuis=kuis, siswa=request.user, nilai=score, benar=benar, salah=salah
        )
        messages.success(request, f"Kuis Selesai! Nilai kamu: {score:.1f}")
        return redirect("beranda")

    return render(request, "pages/siswa/kerjakan_kuis.html", {"kuis": kuis})


# --- EVALUASI & AI REKOMENDASI ---
@login_required
@login_required
def evaluasi(request):
    if not KemajuanBelajar.user_ready_for_evaluation(request.user):
        messages.error(
            request,
            "Ups! Kamu harus menyelesaikan semua materi dulu sebelum ikut Evaluasi Akhir. Semangat! 🚀",
        )
        return redirect("materi")
    latest_evaluasi = (
        NilaiEvaluasi.objects.filter(user=request.user).order_by("-created_at").first()
    )
    try:
        profile = request.user.profile
        kelas_siswa = profile.kelas
    except Profile.DoesNotExist:
        kelas_siswa = "kelas_2"

    if request.method == "GET":
        if "page" not in request.GET or request.GET.get("start") == "1":
            soal = generate_soal_evaluasi_akhir(jumlah_soal=24, kelas=kelas_siswa)  # UBAH KE 24
            request.session["soal_evaluasi"] = soal
            request.session["jawaban_evaluasi"] = []
        soal = request.session.get("soal_evaluasi", [])
        if not soal:
            return redirect("/evaluasi/?start=1")
        paginator = Paginator(soal, 1)
        page_obj = paginator.get_page(request.GET.get("page", 1))
        progress_percentage = int((page_obj.number / len(soal)) * 100)
        jawaban_user = request.session.get("jawaban_evaluasi", [])
        jawaban_chosen = (
            jawaban_user[page_obj.number - 1]
            if page_obj.number <= len(jawaban_user)
            else None
        )
        context = {
            "page_obj": page_obj,
            "progress_percentage": progress_percentage,
            "jawaban_chosen": jawaban_chosen,
            "latest_evaluasi": latest_evaluasi,
        }
        return render(request, "pages/evaluasi.html", context)

    elif request.method == "POST":
        jawaban = request.POST.get("jawaban")
        current_page = int(request.GET.get("page", 1))
        if jawaban:
            jawaban_user = request.session.get("jawaban_evaluasi", [])
            while len(jawaban_user) < current_page:
                jawaban_user.append(None)
            jawaban_user[current_page - 1] = jawaban
            request.session["jawaban_evaluasi"] = jawaban_user
        soal = request.session.get("soal_evaluasi", [])
        if current_page >= len(soal):
            return finalize_evaluasi(request)
        else:
            return redirect(f"/evaluasi/?page={current_page + 1}")

def get_ai_recommendation(evaluasi, kelas_siswa):
    try:
        model_filename = ""
        if kelas_siswa == "kelas_2":
            model_filename = "model_kelas_2.joblib"
        elif kelas_siswa == "kelas_3":
            model_filename = "model_kelas_3.joblib"
        else:
            return "Kelas tidak dikenali"

        model_path = os.path.join(
            settings.BASE_DIR, "belajar", "ml_models", model_filename
        )
        if not os.path.exists(model_path):
            return f"Model tidak ditemukan: {model_filename}"

        model = joblib.load(model_path)
        breakdown = NilaiEvaluasiPerMateri.objects.filter(evaluasi_utama=evaluasi)
        nilai_map = {item.materi: item.nilai for item in breakdown}

        input_features = []
        for i in range(1, 7):
            materi_key = f"materi_{i}"
            nilai = nilai_map.get(materi_key, 0.0)
            input_features.append(nilai)

        feature_names = [f"NILAI_{i}" for i in range(1, 7)]
        X_input = pd.DataFrame([input_features], columns=feature_names)
        prediction = model.predict(X_input)
        return prediction[0]

    except Exception as e:
        print(f"Error Prediction: {e}")
        return "Gagal memproses rekomendasi"


def finalize_evaluasi(request):
    soal = request.session.get("soal_evaluasi", [])
    jawaban_user = request.session.get("jawaban_evaluasi", [])
    if not soal or not jawaban_user:
        messages.error(request, "Data evaluasi tidak ditemukan!")
        return redirect("materi")
    total_soal = len(soal)
    jumlah_benar = 0
    evaluasi = NilaiEvaluasi.objects.create(
        user=request.user, total_soal=total_soal, jumlah_benar=0, nilai=0.0
    )
    for i, soal_item in enumerate(soal):
        user_answer = jawaban_user[i] if i < len(jawaban_user) else None
        correct_answer = soal_item["correct_answer"]
        is_correct = str(user_answer) == str(correct_answer)
        if is_correct:
            jumlah_benar += 1
        JawabanEvaluasi.objects.create(
            evaluasi=evaluasi,
            nomor_soal=i + 1,
            materi_soal=soal_item["materi"],
            soal_pertanyaan=soal_item["question_text"],
            pilihan_jawaban=soal_item["choices"],
            jawaban_user=user_answer or "",
            jawaban_benar=correct_answer,
            is_correct=is_correct,
            poin=1.0 if is_correct else 0.0,
        )
    evaluasi.jumlah_benar = jumlah_benar
    evaluasi.nilai = (jumlah_benar / total_soal) * 100
    evaluasi.save()
    evaluasi.calculate_material_breakdown()
    try:
        profile = request.user.profile
        kelas_siswa = profile.kelas
        rekomendasi = get_ai_recommendation(evaluasi, kelas_siswa)
        evaluasi.rekomendasi_materi = rekomendasi
        evaluasi.save()
    except Exception as e:
        print(f"Error saat menjalankan ML: {e}")
    request.session["evaluasi_id"] = evaluasi.id
    for key in ["soal_evaluasi", "jawaban_evaluasi"]:
        if key in request.session:
            del request.session[key]
    return redirect("hasil_evaluasi")


@login_required
def hasil_evaluasi(request):
    evaluasi_id = request.session.get("evaluasi_id")
    if not evaluasi_id:
        messages.error(request, "Hasil evaluasi tidak ditemukan!")
        return redirect("materi")
    evaluasi = get_object_or_404(NilaiEvaluasi, id=evaluasi_id, user=request.user)
    jawaban_detail = JawabanEvaluasi.objects.filter(evaluasi=evaluasi).order_by(
        "nomor_soal"
    )
    breakdown_per_materi = NilaiEvaluasiPerMateri.objects.filter(
        evaluasi_utama=evaluasi
    ).order_by("materi")
    benar = evaluasi.jumlah_benar
    salah = evaluasi.total_soal - evaluasi.jumlah_benar
    percentage = int(evaluasi.nilai)
    grade = evaluasi.get_grade()
    grade_color = evaluasi.get_grade_color()
    if percentage >= 90:
        message = "🎉 Excellent! Pemahaman kamu sangat luar biasa!"
    elif percentage >= 80:
        message = "👏 Very Good! Kamu sudah memahami materi dengan sangat baik!"
    elif percentage >= 70:
        message = "👍 Good! Hasil yang cukup memuaskan!"
    elif percentage >= 60:
        message = "😐 Perlu improvement. Coba pelajari materi yang masih kurang!"
    else:
        message = "😟 Perlu belajar lebih giat. Jangan menyerah, ulangi lagi!"
        # MENGUBAH LOGIKA WEAK MATERIALS (Menghitung tingkat kesalahan)
    weak_materials = []
    for b in breakdown_per_materi:
        if b.nilai < 70:
            # Hitung persentase kesalahan (100 - skor nilai materi)
            b.tingkat_kesalahan = 100 - b.nilai
            weak_materials.append(b)
    if "evaluasi_id" in request.session:
        del request.session["evaluasi_id"]
    context = {
        "evaluasi": evaluasi,
        "jawaban_detail": jawaban_detail,
        "breakdown_per_materi": breakdown_per_materi,
        "weak_materials": weak_materials,
        "benar": benar,
        "salah": salah,
        "total": evaluasi.total_soal,
        "percentage": percentage,
        "benar_width": int((benar / evaluasi.total_soal) * 100),
        "salah_width": int((salah / evaluasi.total_soal) * 100),
        "grade": grade,
        "grade_color": grade_color,
        "message": message,
    }
    return render(request, "pages/hasil_evaluasi.html", context)


# --- HALAMAN GURU ---

@login_required
@user_passes_test(is_guru, login_url="beranda")
def tambah_siswa(request):
    try:
        guru_kelas = request.user.profile.kelas
    except Profile.DoesNotExist:
        messages.error(request, "Profil guru tidak ditemukan.")
        return redirect("beranda")

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username sudah digunakan!")
        else:
            # Email dikosongkan (string kosong) karena Django User model mengizinkannya
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=""
            )

            group, _ = Group.objects.get_or_create(name="Siswa")
            user.groups.add(group)

            Profile.objects.create(user=user, kelas=guru_kelas)

            messages.success(request,
                             f"Akun siswa {first_name} berhasil dibuat untuk {request.user.profile.get_kelas_display()}!")
            return redirect("guru_daftar_siswa")

    return render(request, "pages/guru/tambah_siswa.html")


# Tambahkan fungsi ini di bawah def tambah_siswa(request):

@login_required
@user_passes_test(is_guru, login_url="beranda")
def edit_siswa(request, siswa_id):
    try:
        guru_kelas = request.user.profile.kelas
    except Profile.DoesNotExist:
        messages.error(request, "Profil guru tidak ditemukan.")
        return redirect("beranda")

    # Pastikan guru hanya bisa mengedit siswa di kelasnya
    siswa = get_object_or_404(User, id=siswa_id, groups__name="Siswa", profile__kelas=guru_kelas)

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Cek apakah username dipakai oleh orang lain (bukan dirinya sendiri)
        if User.objects.filter(username=username).exclude(id=siswa.id).exists():
            messages.error(request, "Username sudah digunakan oleh siswa lain!")
        else:
            siswa.first_name = first_name
            siswa.last_name = last_name
            siswa.username = username

            # Jika field password diisi, berarti guru ingin mereset password siswa
            if password and password.strip() != "":
                siswa.set_password(password)

            siswa.save()
            messages.success(request, f"Data siswa {first_name} berhasil diperbarui!")
            return redirect("guru_daftar_siswa")

    return render(request, "pages/guru/edit_siswa.html", {"siswa": siswa})


@login_required
@user_passes_test(is_guru, login_url="beranda")
def hapus_siswa(request, siswa_id):
    try:
        guru_kelas = request.user.profile.kelas
    except Profile.DoesNotExist:
        return redirect("beranda")

    # Pastikan guru hanya bisa menghapus siswa di kelasnya
    siswa = get_object_or_404(User, id=siswa_id, groups__name="Siswa", profile__kelas=guru_kelas)
    nama_siswa = siswa.get_full_name()

    siswa.delete()
    messages.success(request, f"Siswa {nama_siswa} beserta riwayat belajarnya berhasil dihapus.")
    return redirect("guru_daftar_siswa")


@login_required
@user_passes_test(is_guru, login_url="beranda")
def guru_nilai(request):
    try:
        guru_kelas = request.user.profile.kelas
    except Profile.DoesNotExist:
        guru_kelas = None
    if guru_kelas:
        students = User.objects.filter(
            groups__name="Siswa", profile__kelas=guru_kelas
        ).prefetch_related(
            "profile", "nilai_evaluasi", "nilai_evaluasi__breakdown_per_materi"
        )
    else:
        students = User.objects.none()
    student_grades = []
    for student in students:
        latest_eval = student.nilai_evaluasi.order_by("-created_at").first()
        grades = {
            "materi_1": None,
            "materi_2": None,
            "materi_3": None,
            "materi_4": None,
            "materi_5": None,
            "materi_6": None,
        }
        final_score = None
        if latest_eval:
            final_score = latest_eval.nilai
            breakdown = latest_eval.breakdown_per_materi.all()
            for b in breakdown:
                if b.materi in grades:
                    grades[b.materi] = b.nilai
        student_grades.append(
            {"student": student, "final_score": final_score, "grades": grades}
        )
    return render(
        request,
        "pages/guru_nilai.html",
        {"student_data": student_grades, "guru_kelas": guru_kelas},
    )


@login_required
@user_passes_test(is_guru, login_url="beranda")
def guru_riwayat_siswa(request, siswa_id):
    try:
        guru_kelas = request.user.profile.kelas
    except Profile.DoesNotExist:
        messages.error(request, "Profil guru tidak ditemukan.")
        return redirect("beranda")
    siswa = get_object_or_404(User, id=siswa_id, groups__name="Siswa")
    if siswa.profile.kelas != guru_kelas:
        messages.error(request, "Anda tidak memiliki izin untuk melihat siswa ini.")
        return redirect("guru_nilai")
    evaluasi_list = (
        NilaiEvaluasi.objects.filter(user=siswa)
        .prefetch_related("jawaban_evaluasi")
        .order_by("-created_at")
    )
    return render(
        request,
        "pages/guru_riwayat_siswa.html",
        {"siswa": siswa, "evaluasi_list": evaluasi_list},
    )


@login_required
@user_passes_test(is_guru, login_url="beranda")
def guru_daftar_siswa(request):
    try:
        guru_kelas = request.user.profile.kelas
    except Profile.DoesNotExist:
        guru_kelas = None
    siswa_list = (
        User.objects.filter(groups__name="Siswa", profile__kelas=guru_kelas)
        if guru_kelas
        else User.objects.none()
    )
    return render(
        request,
        "pages/guru_daftar_siswa.html",
        {"siswa_list": siswa_list, "total_siswa": siswa_list.count()},
    )


@login_required
@user_passes_test(is_guru, login_url="beranda")
def export_nilai_excel(request):
    try:
        guru_kelas = request.user.profile.kelas
    except Profile.DoesNotExist:
        messages.error(request, "Profil guru tidak ditemukan.")
        return redirect("guru_nilai")
    wb = Workbook()
    ws = wb.active
    ws.title = f"Nilai {request.user.profile.get_kelas_display()}"
    headers = [
        "Nama Siswa",
        "Username",
        "Materi 1",
        "Materi 2",
        "Materi 3",
        "Materi 4",
        "Materi 5",
        "Materi 6",
        "Nilai Akhir",
    ]
    ws.append(headers)
    students = (
        User.objects.filter(
            groups__name="Siswa", profile__kelas=guru_kelas
        ).prefetch_related(
            "profile", "nilai_evaluasi", "nilai_evaluasi__breakdown_per_materi"
        )
        if guru_kelas
        else User.objects.none()
    )
    for student in students:
        latest_eval = student.nilai_evaluasi.order_by("-created_at").first()
        grades = {
            "materi_1": None,
            "materi_2": None,
            "materi_3": None,
            "materi_4": None,
            "materi_5": None,
            "materi_6": None,
        }
        final_score = None
        if latest_eval:
            final_score = latest_eval.nilai
            breakdown = latest_eval.breakdown_per_materi.all()
            for b in breakdown:
                if b.materi in grades:
                    grades[b.materi] = b.nilai
        row_data = [
            student.get_full_name(),
            student.username,
            grades["materi_1"],
            grades["materi_2"],
            grades["materi_3"],
            grades["materi_4"],
            grades["materi_5"],
            grades["materi_6"],
            final_score,
        ]
        ws.append(row_data)
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = (
        f'attachment; filename="daftar_nilai_{guru_kelas}.xlsx"'
    )
    wb.save(response)
    return response


# --- AUTH & PROFIL ---
def masuk(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        peran = request.POST.get("peran")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            is_siswa = user.groups.filter(name="Siswa").exists()
            is_guru_check = is_guru(user)
            if peran == "siswa" and is_siswa:
                login(request, user)
                return redirect("beranda")
            elif peran == "guru" and is_guru_check:
                login(request, user)
                return redirect("beranda")
            elif peran == "siswa" and not is_siswa:
                messages.error(
                    request,
                    "Akun ini bukan akun Siswa. Silakan gunakan tab Login Guru.",
                )
            elif peran == "guru" and not is_guru_check:
                messages.error(
                    request,
                    "Akun ini bukan akun Guru. Silakan gunakan tab Login Siswa.",
                )
            else:
                messages.error(request, "Peran akun Anda tidak terdefinisi.")
        else:
            messages.error(request, "Username atau password salah!")
    return render(request, "pages/auth/masuk.html")


def daftar(request):
    SECRET_TEACHER_CODE = "BIMBAKA2025"
    if request.method == "POST":
        # 1. Ambil data dari POST
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email", "")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        kelas = request.POST.get("kelas")
        kode_guru = request.POST.get("kode_guru")

        # 2. Validasi dasar
        if password != confirm_password:
            messages.error(request, "Password tidak sesuai!")
            return redirect("daftar")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username sudah terdaftar!")
            return redirect("daftar")

        if not kelas:
            messages.error(request, "Silakan pilih kelas Anda!")
            return redirect("daftar")

        # 3. Logika pendaftaran Guru
        if kode_guru == SECRET_TEACHER_CODE:
            if not email:
                messages.error(request, "Email wajib diisi untuk Guru!")
                return redirect("daftar")

            if User.objects.filter(email=email).exists():
                messages.error(request, "Email sudah terdaftar!")
                return redirect("daftar")

            # Buat akun guru
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

            # Masukkan ke grup dan buat profil
            group, _ = Group.objects.get_or_create(name="Guru")
            user.groups.add(group)
            Profile.objects.create(user=user, kelas=kelas)

            messages.success(request, "Akun Guru berhasil dibuat! Silakan masuk.")
            return redirect("masuk")
        else:
            messages.error(request, "Kode Pendaftaran Guru salah!")
            return redirect("daftar")

    return render(request, "pages/auth/daftar.html")


def keluar(request):
    logout(request)
    return redirect("masuk")


@login_required
def riwayat_evaluasi(request):
    if is_guru(request.user):
        return redirect("beranda")
    riwayat_evaluasi = (
        NilaiEvaluasi.objects.filter(user=request.user)
        .prefetch_related("jawaban_evaluasi")
        .order_by("-created_at")
    )
    riwayat_materi = KemajuanBelajar.objects.filter(
        user=request.user, is_selesai=True
    ).order_by("-waktu_selesai")
    return render(
        request,
        "pages/riwayat_evaluasi.html",
        {"riwayat_evaluasi": riwayat_evaluasi, "riwayat_materi": riwayat_materi},
    )


@login_required
def edit_profile(request):
    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user, user=request.user)
        profile, created = Profile.objects.get_or_create(user=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if u_form.is_valid() and p_form.is_valid():
            user = u_form.save()
            p_form.save()

            # Agar guru tidak perlu login ulang setelah ganti password
            update_session_auth_hash(request, user)

            messages.success(request, "Profil berhasil diperbarui!")
            return redirect("edit_profile")
    else:
        profile, created = Profile.objects.get_or_create(user=request.user)
        u_form = UserUpdateForm(instance=request.user, user=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    return render(
        request, "pages/auth/edit_profile.html", {"u_form": u_form, "p_form": p_form}
    )

@login_required
def hapus_foto_profil(request):
    try:
        profile = request.user.profile
        if profile.foto:
            profile.foto.delete(save=False)
            profile.foto = None
            profile.save()
            messages.success(request, "Foto profil berhasil dihapus.")
        else:
            messages.warning(request, "Anda belum memiliki foto profil.")
    except Profile.DoesNotExist:
        messages.error(request, "Profil tidak ditemukan.")
    return redirect("edit_profile")
