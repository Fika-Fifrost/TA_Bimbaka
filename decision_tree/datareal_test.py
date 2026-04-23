import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import joblib
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# =========================================================
# 1. FUNGSI UNTUK MEMBERSIHKAN DATA RIIL
# =========================================================


def load_and_prep_real_data(file_path):
    print(f"📂 Membaca file data riil: {file_path}...")

    # Deteksi format file
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    # Pastikan nama kolom standar (Case insensitive)
    df.columns = df.columns.str.upper()  # Ubah jadi huruf besar semua biar aman

    # Cek kolom wajib
    feature_cols = ["NILAI_1", "NILAI_2", "NILAI_3", "NILAI_4", "NILAI_5", "NILAI_6"]
    target_col = "REKOMENDASI_MATERI"

    # Bersihkan Format Angka (Koma jadi Titik)
    for col in feature_cols:
        if col in df.columns:
            if df[col].dtype == "object":
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(",", ".")
                    .apply(pd.to_numeric, errors="coerce")
                )

    # Hapus baris yang nilainya kosong
    df = df.dropna(subset=feature_cols)

    print(f"✅ Data siap! Jumlah siswa: {len(df)}")
    return df, feature_cols, target_col


# =========================================================
# 2. FUNGSI TEST MODEL
# =========================================================


def test_model_on_real_data(model_path, data_path, title="Pengujian Data Riil"):
    print(f"\n{'='*50}")
    print(f"🚀 {title}")
    print(f"{'='*50}")

    # A. Load Model
    try:
        model = joblib.load(model_path)
        print("🧠 Model berhasil dimuat.")
    except FileNotFoundError:
        print("❌ Error: File model (.joblib) tidak ditemukan. Upload dulu!")
        return

    # B. Load Data Riil
    try:
        df, features, target = load_and_prep_real_data(data_path)
    except Exception as e:
        print(f"❌ Error baca data: {e}")
        return

    # C. Cek apakah ada Kunci Jawaban (Label Guru) untuk hitung akurasi?
    if target in df.columns:
        # --- SKENARIO 1: ADA KUNCI JAWABAN GURU ---
        X_real = df[features]
        y_real_guru = df[target]  # Ini pendapat Guru

        # Prediksi AI
        y_pred_ai = model.predict(X_real)

        # Hitung Akurasi
        acc = accuracy_score(y_real_guru, y_pred_ai)
        print(f"\n🎯 AKURASI PADA DATA RIIL: {acc*100:.2f}%")
        print("(Persentase kesamaan antara pendapat AI vs Pendapat Guru)")

        print("\n📋 Detail Laporan:")
        print(classification_report(y_real_guru, y_pred_ai, zero_division=0))

        # Visualisasi Perbandingan (Confusion Matrix)
        plt.figure(figsize=(10, 8))
        cm = confusion_matrix(y_real_guru, y_pred_ai)
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Greens",
            xticklabels=model.classes_,
            yticklabels=model.classes_,
        )
        plt.xlabel("Saran AI")
        plt.ylabel("Saran Guru (Asli)")
        plt.title(f"Confusion Matrix: AI vs Guru ({title})")
        plt.show()

        # Simpan Hasil Prediksi ke Excel baru (Side by side)
        df["PREDIKSI_AI"] = y_pred_ai
        df["SESUAI_GURU"] = df[target] == df["PREDIKSI_AI"]
        output_name = f"hasil_test_{title.replace(' ', '_')}.csv"
        df.to_csv(output_name, index=False)
        print(f"💾 File hasil perbandingan disimpan: {output_name}")

    else:
        # --- SKENARIO 2: TIDAK ADA LABEL GURU (Hanya Prediksi) ---
        print("\n⚠️ Tidak ditemukan kolom 'REKOMENDASI_MATERI' dari Guru.")
        print("   -> Sistem hanya akan melakukan prediksi.")

        X_real = df[features]
        y_pred_ai = model.predict(X_real)

        # Simpan Hasil Prediksi ke Excel baru
        df["PREDIKSI_AI"] = y_pred_ai
        print("✅ Prediksi selesai.")
        print(df[["NAMA", "PREDIKSI_AI"]].head())
        output_name = f"hasil_prediksi_{title.replace(' ', '_')}.csv"
        df.to_csv(output_name, index=False)
        print(f"💾 File hasil prediksi disimpan: {output_name}")


# =========================================================
# 3. CARA MENJALANKAN
# =========================================================
# Upload file .joblib dan file data riil (.csv) ke Colab dulu!

# Contoh pemakaian (Sesuaikan nama file Anda):
test_model_on_real_data(
    "model_dummy_kelas_2.joblib", "dataset_kelas_2.csv", "Validasi Kelas 2"
)
