import os
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mts_website.settings")

# Jika cPanel tidak menyediakan pengaturan environment,
# Anda bisa set sementara variabel penting di sini.
# os.environ.setdefault("DJANGO_DEBUG", "False")
# os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "domainanda.com,www.domainanda.com")
# os.environ.setdefault("DJANGO_CSRF_TRUSTED_ORIGINS", "https://domainanda.com,https://www.domainanda.com")

from mts_website.wsgi import application
