from django.apps import AppConfig

class SeoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'seo'
    verbose_name = 'SEO Management'

    def ready(self):
        # Jangan lakukan apapun yang membutuhkan model di sini
        pass