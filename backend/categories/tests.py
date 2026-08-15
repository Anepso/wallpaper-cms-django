from django.test import TestCase
from django.urls import reverse

from categories.models import Category
from wallpapers.tests.helpers import MediaTestCase, create_user


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
