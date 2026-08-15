from wallpapers.models import Wallpaper

from .helpers import (
    MediaTestCase,
    create_category,
    create_user,
    create_wallpaper,
    make_image_file,
)


class CategoryModelTests(MediaTestCase):
    """Uji model Category, khususnya pembuatan slug otomatis."""

    def test_slug_auto_generated_from_name(self):
        category = create_category(name='Nature Scenery')
        category.refresh_from_db()
        self.assertEqual(category.slug, 'nature-scenery')

    def test_slug_unique_when_duplicate_name(self):
        create_category(name='Scenery')
        second = create_category(name='Scenery')
        self.assertEqual(second.slug, 'scenery-1')

    def test_explicit_slug_is_preserved(self):
        category = create_category(name='Nature', slug='custom-nature')
        self.assertEqual(category.slug, 'custom-nature')

    def test_string_representation(self):
        category = create_category(name='Animals')
        self.assertEqual(str(category), 'Animals')


class WallpaperModelTests(MediaTestCase):
    """Uji model Wallpaper: relasi, slug, thumbnail, dan metadata."""

    def test_wallpaper_creation_with_relations(self):
        uploader = create_user()
        category = create_category()
        wallpaper = create_wallpaper(
            title='Sunset Over Ocean',
            category=category,
            uploader=uploader,
        )

        self.assertEqual(wallpaper.category, category)
        self.assertEqual(wallpaper.uploader, uploader)
        self.assertEqual(wallpaper.slug, 'sunset-over-ocean')
        self.assertTrue(wallpaper.is_active)
        self.assertFalse(wallpaper.is_premium)
        self.assertEqual(wallpaper.width, 1920)
        self.assertEqual(wallpaper.height, 1080)
        self.assertEqual(wallpaper.downloads, 0)
        self.assertEqual(wallpaper.views, 0)
        self.assertIsNotNone(wallpaper.file_size)

    def test_slug_unique_when_duplicate_title(self):
        create_wallpaper(title='Same Title')
        second = create_wallpaper(title='Same Title')
        self.assertEqual(second.slug, 'same-title-1')

    def test_slug_preserved_when_title_changed(self):
        wallpaper = create_wallpaper(title='Original Title')
        original_slug = wallpaper.slug
        wallpaper.title = 'Changed Title'
        wallpaper.save()
        wallpaper.refresh_from_db()
        self.assertEqual(wallpaper.slug, original_slug)

    def test_wallpaper_without_category_and_uploader(self):
        wallpaper = Wallpaper.objects.create(
            title='Orphan Wallpaper',
            image=make_image_file(),
        )
        self.assertIsNone(wallpaper.category)
        self.assertIsNone(wallpaper.uploader)

    def test_thumbnail_generated_on_save(self):
        wallpaper = create_wallpaper(title='Thumbnail Test')
        self.assertTrue(wallpaper.thumbnail)
        self.assertTrue(wallpaper.thumbnail.storage.exists(wallpaper.thumbnail.name))

    def test_thumbnail_stored_in_clean_thumbnails_folder(self):
        wallpaper = create_wallpaper(title='Path Check')
        self.assertRegex(
            wallpaper.thumbnail.name,
            r'^thumbnails/\d{4}/\d{2}/\d{2}/[^/]+$',
        )

    def test_thumbnail_width_capped_and_ratio_preserved(self):
        wallpaper = Wallpaper(title='Wide Image', image=make_image_file('wide.png', size=(800, 400)))
        wallpaper.save()

        from PIL import Image
        thumb = Image.open(wallpaper.thumbnail.path)
        self.assertLessEqual(thumb.width, 400)
        self.assertEqual(thumb.width / thumb.height, 2.0)

    def test_thumbnail_regenerated_when_image_replaced(self):
        wallpaper = create_wallpaper(title='Replace Image')
        old_thumb_name = wallpaper.thumbnail.name
        self.assertTrue(wallpaper.thumbnail.storage.exists(old_thumb_name))

        wallpaper.image = make_image_file('new_image.png', color='green', size=(600, 600))
        wallpaper.save()
        wallpaper.refresh_from_db()

        self.assertIsNotNone(wallpaper.thumbnail)
        self.assertNotEqual(wallpaper.thumbnail.name, old_thumb_name)
        self.assertFalse(wallpaper.thumbnail.storage.exists(old_thumb_name))

    def test_thumbnail_not_regenerated_when_metadata_only(self):
        wallpaper = create_wallpaper(title='Metadata Only')
        thumbnail_name = wallpaper.thumbnail.name

        wallpaper.title = 'Metadata Only Updated'
        wallpaper.save()

        wallpaper.refresh_from_db()
        self.assertEqual(wallpaper.thumbnail.name, thumbnail_name)

    def test_file_size_populated_automatically(self):
        wallpaper = create_wallpaper(title='Size Check')
        self.assertIsNotNone(wallpaper.file_size)
        self.assertGreater(wallpaper.file_size, 0)

    def test_tags_can_be_assigned(self):
        wallpaper = create_wallpaper(title='Tagged Wallpaper')
        wallpaper.tags.add('alam', 'pemandangan')
        self.assertEqual(wallpaper.tags.count(), 2)

    def test_resolution_property(self):
        wallpaper = create_wallpaper(title='Resolution Check')
        self.assertEqual(wallpaper.resolution, '1920x1080')

    def test_orientation_auto_detected_landscape(self):
        wallpaper = create_wallpaper(title='Landscape Orientation', width=2000, height=1000)
        self.assertEqual(wallpaper.orientation, 'landscape')

    def test_orientation_auto_detected_portrait(self):
        wallpaper = create_wallpaper(title='Portrait Orientation', width=800, height=1200)
        self.assertEqual(wallpaper.orientation, 'portrait')

    def test_orientation_auto_detected_square(self):
        wallpaper = create_wallpaper(title='Square Orientation', width=1000, height=1000)
        self.assertEqual(wallpaper.orientation, 'square')

    def test_favorites_many_to_many(self):
        user = create_user(username='favoriter')
        wallpaper = create_wallpaper(title='Favorited Wallpaper')
        wallpaper.favorites.add(user)
        self.assertEqual(user.favorite_wallpapers.count(), 1)
        self.assertEqual(wallpaper.favorites.count(), 1)

    def test_extension_property(self):
        wallpaper = create_wallpaper(title='Extension Check')
        self.assertEqual(wallpaper.extension, 'PNG')

    def test_file_size_mb_property(self):
        wallpaper = create_wallpaper(title='MB Check')
        expected = round(wallpaper.file_size / (1024 * 1024), 2)
        self.assertEqual(wallpaper.file_size_mb, expected)

    def test_string_representation(self):
        wallpaper = create_wallpaper(title='String Representation')
        self.assertEqual(str(wallpaper), 'String Representation')

    def test_get_absolute_url(self):
        wallpaper = create_wallpaper(title='URL Check')
        self.assertEqual(
            wallpaper.get_absolute_url(),
            f'/wallpapers/{wallpaper.slug}/',
        )
