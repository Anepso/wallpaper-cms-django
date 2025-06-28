from django import forms
from .models import Wallpaper
from categories.models import Category
from taggit.forms import TagField

class WallpaperForm(forms.ModelForm):
    tags = TagField(label="Tags", help_text="Pisahkan tag dengan koma")

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
