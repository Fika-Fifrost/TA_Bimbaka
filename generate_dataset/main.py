import pandas as pd
import random
import numpy as np


def generate_dummy_data_robust(original_file_path, output_filename, n_per_class=25):
    # 1. Load Data Asli untuk mengambil Kunci Jawaban & Nama Materi
    df = pd.read_csv(original_file_path)

    # Menangani nama kolom pertama jika berbeda
    if "NAMA" not in df.columns:
        df.rename(columns={df.columns[0]: "NAMA"}, inplace=True)

    # Ambil Kunci Jawaban
    key_row = df[
        df["NAMA"].astype(str).str.contains("Kunci", case=False, na=False)
    ].iloc[0]
    q_cols = [f"Q{i}" for i in range(1, 19)]
    answer_key = key_row[q_cols].values
    options = ["A", "B", "C", "D"]

    # Mapping Nama Materi yang ada (Materi 1 s/d 6)
    existing_recs = df["REKOMENDASI_MATERI"].dropna().unique()
    material_map = {}
    for rec in existing_recs:
        for i in range(1, 7):
            if f"Materi {i}" in rec:
                material_map[i] = rec

    # Isi nama materi default jika ada yang hilang di data asli
    for i in range(1, 7):
        if i not in material_map:
            material_map[i] = f"Materi {i}: Topik Tambahan"

    dummy_data = []

    # 2. Mulai Generate Data
    # Loop untuk setiap materi target (1 s/d 6) agar data seimbang
    for target_materi_idx in range(1, 7):
        target_materi_name = material_map[target_materi_idx]

        # Generate n siswa untuk setiap target materi
        for i in range(n_per_class):
            student_answers = []

            # Tentukan soal mana yang harus "salah" (Weakness Area)
            # Asumsi: Nilai 1 = Q1-Q3, Nilai 2 = Q4-Q6, dst.
            start_idx = (target_materi_idx - 1) * 3
            end_idx = start_idx + 3
            weak_indices = range(start_idx, end_idx)

            for q_idx in range(18):
                correct_ans = answer_key[q_idx]

                # Logika Probabilitas:
                # Jika soal termasuk materi kelemahan siswa, peluang benar kecil (15%)
                # Jika soal materi lain, peluang benar besar (90%)
                is_weak_area = q_idx in weak_indices
                prob_correct = 0.15 if is_weak_area else 0.90

                if random.random() < prob_correct:
                    ans = correct_ans
                else:
                    # Pilih jawaban salah secara acak
                    wrong_options = [o for o in options if o != correct_ans]
                    if not wrong_options:
                        wrong_options = ["A"]
                    ans = random.choice(wrong_options)

                student_answers.append(ans)

            # 3. Hitung Nilai & Label Otomatis
            scores = {}
            score_values = []

            for m in range(1, 7):
                s_idx = (m - 1) * 3
                correct_count = sum(
                    [
                        1
                        for k in range(s_idx, s_idx + 3)
                        if student_answers[k] == answer_key[k]
                    ]
                )
                score = round((correct_count / 3) * 100, 2)
                scores[f"NILAI_{m}"] = score
                score_values.append(score)

            # Tentukan Rekomendasi berdasarkan nilai terendah
            min_val = min(score_values)
            min_indices = [
                idx + 1 for idx, v in enumerate(score_values) if v == min_val
            ]

            # Prioritaskan target kita jika ada di minimum (untuk menjaga label tetap konsisten)
            final_rec = (
                material_map[target_materi_idx]
                if target_materi_idx in min_indices
                else material_map[min_indices[0]]
            )

            # Susun Baris Data
            row = {
                "NAMA": f"Siswa_{target_materi_idx}_{i+1}",
                "KELAS": df["KELAS"].mode()[0] if not df["KELAS"].mode().empty else "-",
            }
            for idx, ans in enumerate(student_answers):
                row[f"Q{idx+1}"] = ans
            row.update(scores)
            row["TOTAL_NILAI"] = round(sum(score_values) / 6, 2)
            row["REKOMENDASI_MATERI"] = final_rec

            dummy_data.append(row)

    # Simpan ke CSV
    df_dummy = pd.DataFrame(dummy_data)
    df_dummy.to_csv(output_filename, index=False)
    print(f"File {output_filename} berhasil dibuat dengan {len(df_dummy)} data.")


# Cara Pakai:
# generate_dummy_data_robust("Data_Asli.csv", "Data_Dummy_Baru.csv")
generate_dummy_data_robust("nilai_kelas_3.csv", "nilai_dummy_kelas_3.csv", 50)
