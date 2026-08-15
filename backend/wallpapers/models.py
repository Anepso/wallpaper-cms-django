from django.db import models
from categories.models import Category
from taggit.managers import TaggableManager
from django.utils.text import slugify
from django.conf import settings
from django.urls import reverse
from simple_history.models import HistoricalRecords
import os

app_name = 'wallpapers'


class Orientation(models.TextChoices):
    LANDSCAPE = 'landscape', 'Landscape'
    PORTRAIT = 'portrait', 'Portrait'
    SQUARE = 'square', 'Square'


class Wallpaper(models.Model):
    history = HistoricalRecords()
    title = models.CharField(
        max_length=255,
        verbose_name='Title',
        help_text='Enter a descriptive title for the wallpaper'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description',
        help_text='Optional description of the wallpaper'
    )
    image = models.ImageField(
        upload_to='wallpapers/%Y/%m/%d/',
        verbose_name='Image File',
        help_text='Upload high-quality wallpaper image'
    )
    thumbnail = models.ImageField(
        upload_to='thumbnails/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name='Thumbnail',
        help_text='Auto-generated thumbnail if not provided'
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_wallpapers',
        verbose_name='Uploaded By'
    )
    category = models.ForeignKey(
        'categories.Category', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='wallpapers',
        verbose_name='Category'
    )
    tags = TaggableManager(
        blank=True,
        verbose_name='Tags',
        help_text='Comma-separated tags for this wallpaper'
    )
    width = models.PositiveIntegerField(
        default=1920,
        verbose_name='Width (px)'
    )
    height = models.PositiveIntegerField(
        default=1080,
        verbose_name='Height (px)'
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='File Size (bytes)'
    )
    downloads = models.PositiveIntegerField(
        default=0,
        verbose_name='Download Count'
    )
    views = models.PositiveIntegerField(
        default=0,
        verbose_name='View Count'
    )
    orientation = models.CharField(
        max_length=20,
        choices=Orientation.choices,
        default=Orientation.LANDSCAPE,
        verbose_name='Orientation',
        help_text='Auto-detected from image dimensions'
    )
    favorites = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='favorite_wallpapers',
        blank=True,
        verbose_name='Favorited By',
        help_text='Users who bookmarked this wallpaper'
    )
    is_premium = models.BooleanField(
        default=False,
        verbose_name='Premium Content',
        help_text='Mark if this is premium content'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active',
        help_text='Designates whether this wallpaper should be shown publicly'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    slug = models.SlugField(
        unique=True,
        blank=True,
        verbose_name='Slug',
        help_text='Auto-generated from title if left blank'
    )
    
    class Meta:
        db_table = 'wallpapers_wallpaper'
        verbose_name = 'Wallpaper'
        verbose_name_plural = 'Wallpapers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_premium']),
            models.Index(fields=['created_at']),
            models.Index(fields=['orientation']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug or self.slug == '':
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Wallpaper.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Deteksi orientasi otomatis dari dimensi gambar
        if self.width and self.height:
            if self.width > self.height:
                self.orientation = Orientation.LANDSCAPE
            elif self.width < self.height:
                self.orientation = Orientation.PORTRAIT
            else:
                self.orientation = Orientation.SQUARE

        # Deteksi apakah gambar baru/berubah (untuk update file_size & thumbnail)
        is_new = self._state.adding
        old_image_name = None
        if not is_new:
            try:
                old_image_name = Wallpaper.objects.filter(pk=self.pk).values_list('image', flat=True).first()
            except Exception:
                old_image_name = None

        image_changed = False
        if self.image:
            image_changed = is_new or self.image.name != old_image_name
            if image_changed:
                self.file_size = self.image.size

        super().save(*args, **kwargs)

        # Regenerasi thumbnail jika gambar baru atau diganti.
        # Thumbnail lama hanya dihapus jika thumbnail baru berhasil dibuat.
        if self.image and image_changed:
            old_thumbnail_name = self.thumbnail.name if self.thumbnail else None
            self.thumbnail = None
            if self.generate_thumbnail():
                if old_thumbnail_name:
                    try:
                        self.thumbnail.storage.delete(old_thumbnail_name)
                    except Exception:
                        pass
                self.save(update_fields=['thumbnail'])


    def generate_thumbnail(self):
        """Buat thumbnail berkualitas tinggi, proporsional, dan ringan.

        - Lebar maksimal MAX_THUMB_WIDTH px, tinggi menyesuaikan (rasio aspek terjaga).
        - Resampling LANCZOS untuk hasil tajam.
        - Kompresi optimal per format (JPEG quality=85, PNG optimize, WEBP quality=85).
        - Disimpan rapi di `thumbnails/%Y/%m/%d/<nama>_thumb.<ext>`.
        """
        from PIL import Image, UnidentifiedImageError
        from io import BytesIO
        from django.core.files.base import ContentFile

        # Batas aman: cegah decompression bomb / OOM pada gambar raksasa
        MAX_IMAGE_PIXELS = 60_000_000  # 60MP
        MAX_THUMB_WIDTH = 400

        if not self.image or not self.image.name:
            return False

        try:
            if not self.image.storage.exists(self.image.name):
                return False

            with Image.open(self.image) as img:
                if img.width * img.height > MAX_IMAGE_PIXELS:
                    return False

                img = img.convert('RGB')

                if img.width > MAX_THUMB_WIDTH:
                    new_height = max(1, round(img.height * MAX_THUMB_WIDTH / img.width))
                    img = img.resize((MAX_THUMB_WIDTH, new_height), Image.Resampling.LANCZOS)
                else:
                    # Gambar kecil: jangan diperbesar, cukup pastikan terbaca penuh
                    img.load()

                # Pilih format output sesuai ekstensi asli
                ext = os.path.splitext(self.image.name)[1].lower()
                if ext in ('.jpg', '.jpeg'):
                    ftype, save_kwargs, out_ext = 'JPEG', {'quality': 85, 'optimize': True, 'progressive': True}, 'jpg'
                elif ext == '.webp':
                    ftype, save_kwargs, out_ext = 'WEBP', {'quality': 85}, 'webp'
                elif ext == '.png':
                    ftype, save_kwargs, out_ext = 'PNG', {'optimize': True}, 'png'
                else:
                    ftype, save_kwargs, out_ext = 'JPEG', {'quality': 85, 'optimize': True, 'progressive': True}, 'jpg'

                buffer = BytesIO()
                img.save(buffer, ftype, **save_kwargs)
                buffer.seek(0)

                base_name = os.path.splitext(os.path.basename(self.image.name))[0]
                # upload_to='thumbnails/%Y/%m/%d/' otomatis menambahkan tanggal
                thumb_filename = f'{base_name}_thumb.{out_ext}'

                self.thumbnail.save(thumb_filename, ContentFile(buffer.read()), save=False)
                buffer.close()
                return True

        except (UnidentifiedImageError, OSError, ValueError, KeyError):
            return False

    def get_absolute_url(self):
        return reverse('wallpapers:detail', kwargs={'slug': self.slug})

    @property
    def resolution(self):
        return f"{self.width}x{self.height}"

    @property
    def file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0

    @property
    def extension(self):
        if self.image:
            return os.path.splitext(self.image.name)[1][1:].upper()
        return 