import pandas as pd


def clean_dataset(file_path):
    # 1. Load Dataset
    df = pd.read_csv(file_path)

    # Perbaikan nama kolom (Jika ada 'Unnamed: 0', ubah jadi 'NAMA')
    if "Unnamed: 0" in df.columns:
        df.rename(columns={"Unnamed: 0": "NAMA"}, inplace=True)

    # 2. Hapus Baris 'Kunci Jawaban'
    # Kita hanya mengambil baris di mana kolom NAMA TIDAK SAMA dengan 'Kunci Jawaban'
    df_clean = df[df["NAMA"] != "Kunci Jawaban"].copy()

    # 3. Konversi Kolom Nilai dari String ke Float
    # Daftar kolom fitur yang akan digunakan
    feature_cols = ["NILAI_1", "NILAI_2", "NILAI_3", "NILAI_4", "NILAI_5", "NILAI_6"]

    for col in feature_cols:
        # Ganti koma dengan titik, lalu ubah tipe data jadi float
        # errors='coerce' akan mengubah data non-angka menjadi NaN (untuk keamanan)
        df_clean[col] = (
            df_clean[col]
            .astype(str)
            .str.replace(",", ".")
            .apply(pd.to_numeric, errors="coerce")
        )

    # 4. Pilih Kolom Final untuk Dataset
    # X (Features) = NILAI_1 s/d NILAI_6
    # y (Target)   = REKOMENDASI_MATERI
    final_cols = feature_cols + ["REKOMENDASI_MATERI"]
    df_final = df_clean[final_cols]

    # Hapus baris jika masih ada yang kosong (opsional, untuk kebersihan data)
    df_final = df_final.dropna()

    return df_final


# --- PENGGUNAAN KODE ---


# Ganti nama file sesuai dengan file Anda
file_kelas_2 = "nilai_dummy_kelas_2_v2.csv"
file_kelas_3 = "nilai_dummy_kelas_3_v2.csv"

# Proses pembersihan
df_siap_kelas_2 = clean_dataset(file_kelas_2)
df_siap_kelas_3 = clean_dataset(file_kelas_3)

# Cek hasil 5 baris pertama
print("--- Data Kelas 2 Siap Pakai ---")
print(df_siap_kelas_2.head())

print("\n--- Data Kelas 3 Siap Pakai ---")
print(df_siap_kelas_3.head())

# (Opsional) Simpan ke file CSV baru
df_siap_kelas_2.to_csv("dataset_dummy_kelas_2_v2.csv", index=False)
df_siap_kelas_3.to_csv("dataset_dummy_kelas_3_v2.csv", index=False)
