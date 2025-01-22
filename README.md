ALUR KERJA PERANGKAT IOT

1. Inisialisasi:
    - Sambungkan perangkat ke WiFI
    - Sambungkan ke Broker MQTT
    - Matikan semua LED, merah dan biru

2. Loop utama:
    - Periksa pesan kontrol dari topik IoT/Control
    - baca data dari sensor DHT22
    - Jika ada perubahan data, kirim ke broker pada topik IoT/telemetry

3. Respon pesan ke MQTT:
    - jika ada perintah, sesuaikan status LED dan kirim pembaruan status ke broker