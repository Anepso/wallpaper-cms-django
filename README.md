📁 Struktur Folder Proyek CMS Django

🗂️ Root Project Directory

├── backend/             # Aplikasi backend Django (berisi app modular)

├── frontend/            # Project frontend 

├── var/                 # Custom folder (berisi logs, middleware, models)

├── venv/                # Virtual environment Python

├── .env                 # Konfigurasi environment (secrets, DB credentials, dll)

├── .gitignore           # File untuk mengecualikan file dari Git

├── manage.py            # Entrypoint manajemen Django

├── package.json         # Konfigurasi NPM (frontend/backend)

├── package-lock.json    # Lock file dependensi NPM

├── requirements.txt     # Daftar dependensi Python

├── urls.py              # Routing utama Django

└── README.md            # Dokumentasi proyek


📁 backend/
Folder ini menyimpan semua aplikasi (modular apps) untuk Django.

backend/
├── api/             # API layer (views, serializers, routers, dll)

├── categories/      # Modul manajemen kategori

├── core/            # Konfigurasi utama (settings tambahan)

├── media/           # Folder untuk menyimpan file media yang diupload

├── seo/             # Modul pengaturan SEO (meta tags, sitemap, dsb)

├── staticfiles/     # Static file hasil collectstatic (JS, CSS, gambar)

├── templates/       # Template HTML Django

├── users/           # Modul autentikasi / manajemen pengguna

├── wallpapers/      # Modul manajemen data wallpaper


📁 frontend/

frontend/

├── node_modules/        # Direktori dependensi frontend

├── static/              # Static assets frontend (JS, CSS, gambar)

├── package.json         # Konfigurasi proyek frontend

├── package-lock.json    # 


📁 var/

var/

├── logs/                # Folder untuk file log 

├── apps.py              # Custom apps registration 

├── middleware.py        # Custom middleware Django

├── models.py            # Model umum/base model


📁 venv/

venv/                    # Virtual environment Python


📝 Laporan Proyek
Nama Proyek: Wallpaper CMS (Content Management System)
Platform: Django (Backend) + Frontend (JS framework + python)
Tujuan:
Membangun sebuah CMS yang memungkinkan pengguna untuk mengelola koleksi wallpaper digital melalui antarmuka berbasis web yang modern dan responsif.

🔧 Teknologi yang Digunakan
Backend: Django 4+

Modular apps: api, users, wallpapers, categories, core, seo

Manajemen media dan static file

PostgreSQL

Frontend: JavaScript (Node.js-based, terindikasi dari package.json)

Database: PostgreSQL (dapat dikonfigurasi ulang ke MySQL)

Virtual Environment: venv (Python virtual environment)

Konfigurasi Rahasia: File .env

📁 Struktur Utama
backend/ – Semua aplikasi Django modular.

frontend/ – Berisi kode antarmuka pengguna (UI).

var/ – Modul tambahan seperti middleware, models, dan log.

staticfiles/ – Output dari collectstatic (untuk deploy).

templates/ – HTML templates untuk Django.

media/ – Penyimpanan file unggahan.

manage.py – Entry point proyek Django.

📌 Fitur-Fitur
Autentikasi pengguna (users)

Manajemen wallpaper dan kategori (wallpapers, categories)

SEO dan metadata halaman (seo)

REST API (api)

Custom middleware dan model dasar (var/)

Konfigurasi environment tersendiri melalui .env
