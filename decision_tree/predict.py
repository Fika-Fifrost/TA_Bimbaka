import joblib
import pandas as pd

# 1. Load model yang sudah jadi
model_siap_pakai = joblib.load("model_dummy_kelas_2.joblib")

# 2. Data nilai siswa baru (contoh input)
# Urutan harus sama: [NILAI_1, NILAI_2, NILAI_3, NILAI_4, NILAI_5, NILAI_6]
nilai_siswa_baru = [[80, 70, 60, 50, 40, 90]]

# 3. Prediksi
hasil_rekomendasi = model_siap_pakai.predict(nilai_siswa_baru)

print("Saran Materi:", hasil_rekomendasi[0])
