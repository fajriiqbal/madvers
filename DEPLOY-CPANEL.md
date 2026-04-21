# Deploy Django ke cPanel

Dokumen ini disiapkan khusus untuk project ini supaya lebih mudah di-hosting secara online.

## 1. Siapkan repository GitHub

1. Buat repository baru di GitHub, sebaiknya `private`.
2. Dari folder project ini jalankan:

```powershell
git init
git add .
git commit -m "Initial deploy-ready project"
git branch -M main
git remote add origin https://github.com/USERNAME/NAMA-REPO.git
git push -u origin main
```

Catatan:
- File `venv/`, `db.sqlite3`, `media/`, dan `staticfiles/` sudah diabaikan oleh `.gitignore`.
- Jika data lokal penting, lakukan backup database sebelum hosting.

## 2. Cek fitur hosting cPanel

Pastikan hosting Anda memiliki:
- Python App / Setup Python App / Application Manager
- akses terminal atau setidaknya menu menjalankan perintah Python
- database MySQL

Kalau hosting tidak punya dukungan Python, jangan pakai cPanel itu untuk Django.

## 3. Buat aplikasi Python di cPanel

1. Buka `Setup Python App`.
2. Pilih versi Python yang tersedia.
3. Isi `Application root` ke folder project, misalnya:
   `/home/username/mts_bendahara`
4. Isi `Application URL`, misalnya:
   `domainanda.com`
5. Isi `Application startup file`:
   `passenger_wsgi.py`
6. Isi `Application Entry point`:
   `application`

## 4. Upload source code

Cara paling rapi:
- clone dari GitHub ke folder aplikasi di server

Kalau cPanel punya menu `Git Version Control`:
1. Hubungkan repository GitHub Anda.
2. Clone ke `Application root`.

Kalau tidak ada:
1. Upload project sebagai ZIP.
2. Extract ke `Application root`.

## 5. Install dependency

Masuk ke terminal cPanel atau gunakan virtual environment yang dibuat cPanel, lalu jalankan:

```bash
pip install -r requirements.txt
```

## 6. Isi konfigurasi production

Project ini memakai environment variable. Isi minimal:

```bash
DJANGO_SECRET_KEY=secret-production-anda
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=domainanda.com,www.domainanda.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://domainanda.com,https://www.domainanda.com
DJANGO_DB_ENGINE=mysql
DJANGO_DB_NAME=nama_database
DJANGO_DB_USER=user_database
DJANGO_DB_PASSWORD=password_database
DJANGO_DB_HOST=localhost
DJANGO_DB_PORT=3306
```

Jika cPanel tidak punya form environment variable, variabel ini bisa sementara ditaruh di `passenger_wsgi.py`.

## 7. Buat database

1. Buat database MySQL di cPanel.
2. Buat user database.
3. Hubungkan user ke database dengan semua privilege.

## 8. Jalankan migrasi dan static

Setelah environment dan dependency siap:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

## 9. Restart aplikasi

Di cPanel Python App, klik `Restart`.

## 10. Jika ingin bawa data lama dari SQLite

Pilihan aman:
1. Hosting dulu pakai MySQL kosong.
2. Export data dari lokal.
3. Import ke database hosting.

Contoh export lokal:

```powershell
venv\Scripts\python.exe manage.py dumpdata --exclude auth.permission --exclude contenttypes > data.json
```

Contoh import di server:

```bash
python manage.py loaddata data.json
```

## Catatan penting

- `DEBUG` harus `False` saat online.
- Jangan upload password dan `SECRET_KEY` ke GitHub.
- Untuk awal, domain dengan SSL aktif lebih aman.
- Jika hosting Anda hanya menyediakan Python 3.10 atau 3.11, requirement project ini tetap aman karena versi Django sudah dibuat fleksibel.
