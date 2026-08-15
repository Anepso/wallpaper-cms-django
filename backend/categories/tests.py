from django.test import TestCase
from django.urls import reverse

from categories.models import Category
from wallpapers.tests.helpers import MediaTestCase, create_user, create_wallpaper, make_image_file


class CategoryPermissionTests(MediaTestCase):
    """Uji kontrol akses halaman manajemen kategori."""

    def setUp(self):
        self.category = Category.objects.create(name='Nature')
        self.staff_user = create_user(username='staff', is_staff=True)
        self.regular_user = create_user(username='regular')

    def test_anonymous_redirected_from_add_category(self):
        response = self.client.get(reverse('categories:add'))
        self.assertEqual(response.status_code, 302)

    def test_regular_user_forbidden_from_add_category(self):
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('categories:add'))
        self.assertEqual(response.status_code, 403)

    def test_staff_can_open_add_category(self):
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('categories:add'))
        self.assertEqual(response.status_code, 200)

    def test_regular_user_forbidden_from_edit_category(self):
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(
            reverse('categories:edit', kwargs={'slug': self.category.slug})
        )
        self.assertEqual(response.status_code, 403)

    def test_regular_user_forbidden_from_delete_category(self):
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(
            reverse('categories:delete', kwargs={'slug': self.category.slug})
        )
        self.assertEqual(response.status_code, 403)

    def test_category_detail_page_renders(self):
        response = self.client.get(
            reverse('categories:detail', kwargs={'slug': self.category.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.name)


class CategoryCRUDTests(MediaTestCase):
    """Uji CRUD kategori: tambah, edit, hapus."""

    def setUp(self):
        self.staff_user = create_user(username='staff', is_staff=True)
        self.client.login(username='staff', password='testpass123')

    def test_add_category_creates_unique_slug(self):
        Category.objects.create(name='Alam')
        response = self.client.post(
            reverse('categories:add'),
            {'name': 'Alam', 'description': 'duplikat'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(name='Alam', slug='alam-1').exists())

    def test_edit_category_page_prefills_old_data(self):
        category = Category.objects.create(name='Lama', description='Deskripsi lama')
        response = self.client.get(
            reverse('categories:edit', kwargs={'slug': category.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Kategori')
        self.assertContains(response, 'value="Lama"')
        self.assertContains(response, 'Deskripsi lama')

    def test_edit_category_updates_data(self):
        category = Category.objects.create(name='Lama')
        response = self.client.post(
            reverse('categories:edit', kwargs={'slug': category.slug}),
            {'name': 'Baru', 'description': 'deskripsi baru'},
        )

        self.assertEqual(response.status_code, 302)
        category.refresh_from_db()
        self.assertEqual(category.name, 'Baru')
        self.assertEqual(category.description, 'deskripsi baru')
        # Slug tidak berubah saat edit
        self.assertEqual(category.slug, 'lama')

    def test_delete_category_clears_fk_and_removes_thumbnail_file(self):
        category = Category.objects.create(name='To Delete')
        category.thumbnail = make_image_file('cat_thumb.png', size=(200, 200))
        category.save()
        thumbnail_name = category.thumbnail.name
        wallpaper = create_wallpaper(title='In Category', category=category)

        response = self.client.post(
            reverse('categories:delete', kwargs={'slug': category.slug})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(slug='to-delete').exists())
        wallpaper.refresh_from_db()
        self.assertIsNone(wallpaper.category)
        self.assertFalse(category.thumbnail.storage.exists(thumbnail_name))
