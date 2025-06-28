from django.db import models
from categories.models import Category
from taggit.managers import TaggableManager
from django.utils.text import slugify
from django.conf import settings
from django.urls import reverse
from simple_history.models import HistoricalRecords
import os

app_name = 'wallpapers'

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

        if self.image and not self.file_size:
            self.file_size = self.image.size

        super().save(*args, **kwargs)

        if self.image and not self.thumbnail:
            self.generate_thumbnail()


    def generate_thumbnail(self):
        from PIL import Image, UnidentifiedImageError
        from io import BytesIO
        from django.core.files.base import ContentFile

        try:
            image = Image.open(self.image)
            image = image.convert('RGB')
            image.thumbnail((300, 300))

            thumb_name, thumb_extension = os.path.splitext(self.image.name)
            thumb_extension = thumb_extension.lower()
            thumb_filename = thumb_name + '_thumb' + thumb_extension

            FTYPE = 'JPEG' if thumb_extension in ['.jpg', '.jpeg'] else 'PNG'

            temp_thumb = BytesIO()
            image.save(temp_thumb, FTYPE)
            temp_thumb.seek(0)

            self.thumbnail.save(thumb_filename, ContentFile(temp_thumb.read()), save=False)
            temp_thumb.close()
            return True

        except UnidentifiedImageError:
            print("Thumbnail generation failed: UnidentifiedImageError")
            return False
        except Exception as e:
            print(f"[ERROR THUMBNAIL] {e}")

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