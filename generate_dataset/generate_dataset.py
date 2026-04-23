import pandas as pd
import random
import numpy as np

REKOMENDASI_MATERI_KELAS_2 = {
    1: "Materi 1: Perkalian sebagai Penjumlahan Berulang",
    2: "Materi 2: Sifat Komutatif (Sifat Pertukaran)",
    3: "Materi 3: Perkalian dengan 1 dan 0",
    4: "Materi 4: Perkalian dengan 2 dan 5",
    5: "Materi 5: Perkalian dengan 10",
    6: "Materi 6: Perkalian dengan 3, 4, 6, 7, 8, dan 9"
}

REKOMENDASI_MATERI_KELAS_3 = {
    1: "Materi 1: Perkalian dengan 0 dan 10",
    2: "Materi 2: Perkalian Bersusun",
    3: "Materi 3: Pembagian dengan 1 dan 0",
    4: "Materi 4: Pembagian Bersusun Dasar (Porogapit)",
    5: "Materi 5: Operasi Hitung Campuran Sederhana",
    6: "Materi 6: Penerapan Urutan Operasi Hitung Campuran dalam Soal Cerita"
}


def generate_dataset(output_filename, recommendation_list, nama_kelas, n_students=100):
    answer_key = ["A", "B", "C", "D", "A", "B", "C", "D", "A", "B", "C", "D", "A",
                  "B", "C", "D", "A", "B", "C", "D", "A", "B", "C", "D"]  # Contoh kunci jawaban
    options = ["A", "B", "C", "D"]

    data = []
    for i in range(n_students):
        student_id = i + 1

        # --- MENENTUKAN PROFIL KEMAMPUAN SISWA (RAHASIA DAPUR) ---
        # Kita acak, siswa ini tipe yang mana?

        # Skill Dasar (0.0 - 1.0): Seberapa pintar siswa ini secara umum?
        # Rata-rata siswa ada di 0.6 - 0.9. Ada sedikit siswa yang lemah (<0.5)
        # Distribusi condong ke kanan (pintar)
        base_skill = np.random.beta(5, 2)

        # Tentukan Kelemahan Spesifik (Satu materi yang dia paling gak bisa)
        weakness_idx = i % 6 + 1  # Pastikan ada distribusi kelemahan merata di 6 materi

        # Buat array probabilitas "Bisa Menjawab Benar" untuk tiap materi (1-6)
        probs_per_materi = {}

        for m in range(1, 7):
            skill = base_skill

            # Jika ini materi kelemahannya, kurangi skill secara drastis
            if m == weakness_idx:
                skill -= random.uniform(0.2, 0.5)

            # EFEK KORELASI (PENTING BUAT SKRIPSI!)
            # Jika lemah di materi awal, kemungkinan besar lemah di materi berikutnya (karena materi berikutnya butuh pemahaman materi awal)
            if m > weakness_idx:
                skill -= random.uniform(0.1, 0.3)

            # Batasi skill antara 0.1 (ngawur) sampai 0.98 (hampir sempurna)
            skill = max(0.1, min(0.98, skill))
            probs_per_materi[m] = skill

        # --- SIMULASI MENJAWAB SOAL ---
        student_answers = []
        scores = {}
        raw_scores_list = []
        for m in range(1, 7):
            # Ambil probabilitas benar untuk materi ini
            prob_correct = probs_per_materi[m]

            # Simulasi jawab 4 soal per materi
            correct_count = 0
            # Index soal di Excel (Q1-Q4 utk mat 1, Q5-Q8 utk mat 2, dst)
            start_idx = (m - 1) * 4

            for k in range(4):
                q_idx = start_idx + k
                correct_ans = answer_key[q_idx]

                # Roll dice: Benar atau Salah?
                if random.random() < prob_correct:
                    ans = correct_ans  # Jawab benar
                    correct_count += 1
                else:
                    # Jawab Salah (pilih acak opsi yang bukan jawaban benar)
                    wrong_opts = [o for o in options if o != correct_ans]
                    ans = random.choice(wrong_opts)

                student_answers.append(ans)

            # Hitung Nilai Per Materi
            score = round((correct_count / 4) * 100, 2)
            scores[f"NILAI_{m}"] = score
            raw_scores_list.append(score)

        # --- LOGIKA GURU (AUTO LABELING) ---
        # Disini kita tentukan label BUKAN secara acak, tapi berdasarkan nilai yang barusan terbentuk.
        min_val = min(raw_scores_list)

        # Cari materi apa saja yang nilainya terendah (bisa jadi ada 2 materi nilainya sama2 0)
        min_indices = [idx + 1 for idx,
                       v in enumerate(raw_scores_list) if v == min_val]

        # ATURAN PRIORITAS GURU:
        # Jika ada nilai yang sama rendahnya, prioritaskan materi yang lebih awal (Materi 1 > Materi 6)
        # Karena materi awal adalah fondasi.
        final_rec_idx = min_indices[0]
        final_rec = recommendation_list[final_rec_idx]

        # --- SUSUN DATASET ---
        row = {
            "NAMA": f"Siswa_Gen_{student_id}",
            "KELAS": f"{nama_kelas}"
        }

        # Masukkan Q1-Q24
        for idx, ans in enumerate(student_answers):
            row[f"Q{idx+1}"] = ans

        # Masukkan Nilai
        row.update(scores)

        # Masukkan Total & Label
        row["TOTAL_NILAI"] = round(sum(raw_scores_list) / 6, 2)
        row["REKOMENDASI_MATERI"] = final_rec

        data.append(row)

    df = pd.DataFrame(data)
    df.to_csv(output_filename, index=False)


if __name__ == "__main__":
    # Contoh penggunaan untuk Kelas 2
    generate_dataset("dataset_kelas_2.csv",
                     REKOMENDASI_MATERI_KELAS_2, "Kelas 2", 360)

    # Contoh penggunaan untuk Kelas 3
    generate_dataset("dataset_kelas_3.csv",
                     REKOMENDASI_MATERI_KELAS_3, "Kelas 3", 360)
