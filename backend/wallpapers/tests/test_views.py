from django.urls import reverse

from wallpapers.models import Wallpaper

from .helpers import (
    MediaTestCase,
    create_category,
    create_user,
    create_wallpaper,
    make_image_file,
)


class PublicPagesTests(MediaTestCase):
    """Uji halaman publik aplikasi wallpapers."""

    def test_home_page_returns_200(self):
        response = self.client.get(reverse('wallpapers:home'))
        self.assertEqual(response.status_code, 200)

    def test_root_home_page_requires_login_then_returns_200(self):
        create_user(username='guest')

        anonymous = self.client.get('/')
        self.assertEqual(anonymous.status_code, 302)
        self.assertIn(reverse('users:login'), anonymous.url)

        self.client.login(username='guest', password='testpass123')
        logged_in = self.client.get('/')
        self.assertEqual(logged_in.status_code, 200)

    def test_explore_page_returns_200(self):
        response = self.client.get(reverse('wallpapers:explore'))
        self.assertEqual(response.status_code, 200)

    def test_list_page_returns_200(self):
        response = self.client.get(reverse('wallpapers:list'))
        self.assertEqual(response.status_code, 200)

    def test_search_page_returns_200(self):
        create_wallpaper(title='Search Me Wallpaper')
        response = self.client.get(reverse('wallpapers:search'), {'q': 'search'})
        self.assertEqual(response.status_code, 200)

    def test_search_page_without_query_returns_200(self):
        response = self.client.get(reverse('wallpapers:search'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tidak ada wallpaper yang cocok')

    def test_category_page_returns_200(self):
        category = create_category(name='Nature')
        response = self.client.get(
            reverse('wallpapers:category', kwargs={'slug': category.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_detail_page_returns_200(self):
        wallpaper = create_wallpaper(title='Detail Page Wallpaper')
        response = self.client.get(
            reverse('wallpapers:detail', kwargs={'slug': wallpaper.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, wallpaper.title)

    def test_detail_page_returns_404_for_unknown_slug(self):
        response = self.client.get(
            reverse('wallpapers:detail', kwargs={'slug': 'does-not-exist'})
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_page_hides_inactive_wallpaper(self):
        wallpaper = create_wallpaper(title='Hidden Wallpaper', is_active=False)
        response = self.client.get(
            reverse('wallpapers:detail', kwargs={'slug': wallpaper.slug})
        )
        self.assertEqual(response.status_code, 404)


class AdminAccessTests(MediaTestCase):
    """Uji kontrol akses halaman pengelolaan admin."""

    def setUp(self):
        self.admin_user = create_user(username='admin', role='admin')
        self.staff_user = create_user(username='staff', is_staff=True)
        self.regular_user = create_user(username='regular')

    def test_anonymous_redirected_from_admin_list(self):
        response = self.client.get(reverse('wallpapers:wallpaper_admin_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_regular_user_forbidden_from_admin_list(self):
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('wallpapers:wallpaper_admin_list'))
        self.assertEqual(response.status_code, 403)

    def test_staff_user_can_access_admin_list(self):
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('wallpapers:wallpaper_admin_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_role_user_can_access_admin_list(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('wallpapers:wallpaper_admin_list'))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_redirected_from_upload_page(self):
        response = self.client.get(reverse('wallpapers:upload'))
        self.assertEqual(response.status_code, 302)

    def test_regular_user_forbidden_from_upload_page(self):
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('wallpapers:upload'))
        self.assertEqual(response.status_code, 403)

    def test_staff_user_can_open_upload_page(self):
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('wallpapers:upload'))
        self.assertEqual(response.status_code, 200)

    def test_regular_user_forbidden_from_add_page(self):
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('wallpapers:add'))
        self.assertEqual(response.status_code, 403)

    def test_users_dashboard_anonymous_redirected(self):
        response = self.client.get(reverse('users:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_regular_user_forbidden_from_users_dashboard(self):
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('users:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_regular_user_cannot_delete_foreign_wallpaper(self):
        uploader = create_user(username='uploader')
        wallpaper = create_wallpaper(title='Foreign Wallpaper', uploader=uploader)

        self.client.login(username='regular', password='testpass123')
        response = self.client.post(reverse('wallpapers:delete', kwargs={'pk': wallpaper.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Wallpaper.objects.filter(pk=wallpaper.pk).exists())

    def test_single_upload_via_view(self):
        self.client.login(username='admin', password='testpass123')
        category = create_category(name='Nature')
        data = {
            'title': 'Single Upload',
            'category': category.pk,
            'tags': 'alam',
            'image': make_image_file('single.png'),
        }
        response = self.client.post(reverse('wallpapers:upload'), data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Wallpaper.objects.count(), 1)
        wallpaper = Wallpaper.objects.get()
        self.assertEqual(wallpaper.uploader, self.admin_user)
        self.assertEqual(wallpaper.category, category)
        self.assertEqual(wallpaper.slug, 'single-upload')

    def test_bulk_upload_via_view(self):
        self.client.login(username='admin', password='testpass123')
        category = create_category(name='Nature')
        data = {
            'title': '',
            'category': category.pk,
            'image': [
                make_image_file('beach.png'),
                make_image_file('mountain.png'),
                make_image_file('forest.png'),
            ],
        }
        response = self.client.post(reverse('wallpapers:upload'), data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Wallpaper.objects.count(), 3)
        self.assertEqual(
            Wallpaper.objects.filter(category=category).count(),
            3,
        )
