import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import accuracy_score, confusion_matrix


def train_model(file_path, title):
    # 1. Load Dataset Bersih
    df = pd.read_csv(file_path)

    # 2. Tentukan Fitur (X) dan Target (y)
    # Mengambil semua kolom yang mengandung kata 'NILAI' sebagai fitur
    feature_cols = [col for col in df.columns if "NILAI" in col]
    X = df[feature_cols]
    y = df["REKOMENDASI_MATERI"]

    # 3. Bagi Data (Split) - 70% Training, 30% Testing
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    # HYPERPARAMETER TUNING
    # Definisikan model
    dt = DecisionTreeClassifier(random_state=42)

    # Tentukan kandidat parameter yang mau dicoba
    param_grid = {
        "max_depth": [None, 5, 7, 10, 15],
        "min_samples_split": [2, 5, 10, 20],
        "criterion": ["gini", "entropy"],
    }

    # Mencari kombinasi terbaik
    grid_search = GridSearchCV(dt, param_grid, cv=5, scoring="accuracy")
    grid_search.fit(X_train, y_train)

    # Lihat hasil tuning
    print("Settingan Terbaik : ", grid_search.best_params_)
    print("Akurasi Terbaik   : ", grid_search.best_score_)

    # Gunakan model terbaik tersebut
    model = grid_search.best_estimator_

    # # 4. Latih Model
    # model = DecisionTreeClassifier(random_state=42, max_depth=5)
    # model.fit(X_train, y_train)

    # 5. Cek Akurasi
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Akurasi Model {title}: {acc*100:.1f}%")

    # # Cek Peta Kesalahan
    # cm = confusion_matrix(y_test, y_pred)

    # # Visualisasi Peta Kesalahan
    # plt.figure(figsize=(10, 8))
    # sns.heatmap(cm, annot=True, fmt='d', cmap='Reds',
    #             xticklabels=model.classes_,
    #             yticklabels=model.classes_)
    # plt.xlabel('Tebakan Model')
    # plt.ylabel('Kunci Jawaban Asli')
    # plt.title('Peta Kesalahan')
    # plt.show()
    # plt.savefig(f"Peta Kesalahan - {title}")

    # # 6. Visualisasi Pohon Keputusan
    # plt.figure(figsize=(100, 20))
    # plot_tree(model, feature_names=feature_cols,
    #           class_names=model.classes_, filled=True, rounded=True, fontsize=8)
    # plt.title(f"Decision Tree - {title}")
    # plt.savefig(f"Decision Tree - {title}")

    return model


# --- Jalankan Kode ---
# Pastikan file .csv berada di folder yang sama dengan script ini
file_kelas_2 = "dataset_dummy_kelas_2_v2.csv"
file_kelas_3 = "dataset_dummy_kelas_3_v2.csv"

print("--- Hasil Training ---")
model_kelas_2 = train_model(file_kelas_2, "Kelas 2")
model_kelas_3 = train_model(file_kelas_3, "Kelas 3")
