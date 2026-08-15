from io import BytesIO
import shutil
import tempfile

from PIL import Image

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from categories.models import Category
from wallpapers.models import Wallpaper


def make_image_file(name='test.png', color='red', size=(400, 300)):
    """Buat file gambar PNG kecil yang valid untuk keperluan pengujian."""
    buffer = BytesIO()
    Image.new('RGB', size, color).save(buffer, 'PNG')
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type='image/png')


def create_user(username='testuser', password='testpass123', role='user', **extra):
    User = get_user_model()
    return User.objects.create_user(username=username, password=password, role=role, **extra)


def create_category(name='Nature', **extra):
    return Category.objects.create(name=name, **extra)


def create_wallpaper(title='Sunset Beach', category=None, uploader=None, with_image=True, **extra):
    wallpaper = Wallpaper(title=title, category=category, uploader=uploader, **extra)
    if with_image:
        wallpaper.image = make_image_file(name=title.replace(' ', '_') + '.png')
    wallpaper.save()
    return wallpaper


class MediaTestCase(TestCase):
    """TestCase dasar dengan MEDIA_ROOT sementara agar file yang dibuat
    selama pengujian tidak mencemari folder media produksi.

    Cookie sesi/CSRF di-nonaktifkan pengamanannya agar autentikasi via
    Django test client berjalan normal (login) tanpa HTTPS.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_root = tempfile.mkdtemp(prefix='wallpaper_test_media_')
        cls._settings_override = override_settings(
            MEDIA_ROOT=cls._media_root,
            SESSION_COOKIE_SECURE=False,
            CSRF_COOKIE_SECURE=False,
        )
        cls._settings_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._settings_override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()
