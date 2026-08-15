from django import forms
from .models import Wallpaper
from categories.models import Category
from taggit.forms import TagField

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB per file


class WallpaperForm(forms.ModelForm):
    tags = TagField(label="Tags", help_text="Pisahkan tag dengan koma", required=False)

    class Meta:
        model = Wallpaper
        fields = [
            'title',
            'description',
            'image',
            'category',
            'tags',
            'width',
            'height',
            'is_premium'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            return image

        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise forms.ValidationError(
                "Format file tidak didukung. Gunakan JPG, PNG, atau WEBP."
            )

        if image.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError(
                f"Ukuran file terlalu besar (maksimal {MAX_UPLOAD_SIZE // (1024 * 1024)}MB per file)."
            )

        return image
