import pandas as pd
import joblib  # Library untuk menyimpan model
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

# --- Fungsi Pelatihan & Export ---


def train_and_export(file_path, class_name, output_filename):
    print(f"Sedang memproses {class_name}...")

    # 1. Load Data
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(
            f"Error: File {file_path} tidak ditemukan. Pastikan sudah di-upload ke Colab!"
        )
        return

    # 2. Fitur & Target
    feature_cols = [c for c in df.columns if "NILAI" in c]
    X = df[feature_cols]
    y = df["REKOMENDASI_MATERI"]

    # 3. Split Data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    # 4. Training
    model = DecisionTreeClassifier(random_state=42, max_depth=5)
    model.fit(X_train, y_train)

    # 5. Cek Akurasi
    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"✅ Akurasi {class_name}: {acc*100:.1f}%")

    # 6. EXPORT MODEL (Simpan ke file .joblib)
    joblib.dump(model, output_filename)
    print(f"💾 Model disimpan sebagai: {output_filename}")
    print("------------------------------------------------")


# --- Eksekusi ---
# Pastikan nama file csv sesuai dengan yang Anda upload
train_and_export("dataset_dummy_kelas_2.csv", "Kelas 2", "model_dummy_kelas_2.joblib")
train_and_export("dataset_dummy_kelas_3.csv", "Kelas 3", "model_dummy_kelas_3.joblib")
