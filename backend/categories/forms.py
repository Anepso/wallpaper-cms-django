from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'thumbnail']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'placeholder': 'Contoh: Alam, Abstrak, Hewan'
        })

def clean_thumbnail(self):
    thumbnail = self.cleaned_data.get('thumbnail')
    if thumbnail:
        # Validasi ukuran file
        if thumbnail.size > 2 * 1024 * 1024:  # 2MB
            raise forms.ValidationError("Ukuran gambar terlalu besar (maksimal 2MB)")
        
        # Validasi rasio aspek
        from PIL import Image
        img = Image.open(thumbnail)
        if img.width != img.height:
            raise forms.ValidationError("Gambar harus memiliki rasio 1:1 (persegi)")
    
    return thumbnail