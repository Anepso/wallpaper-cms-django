from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

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

    def test_home_page_tag_filter(self):
        wp1 = create_wallpaper(title='Red Sunset')
        wp2 = create_wallpaper(title='Blue Mountain')
        wp1.tags.add('merah')
        wp2.tags.add('biru')

        response = self.client.get(reverse('wallpapers:home'), {'tag': 'merah'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Red Sunset')
        self.assertNotContains(response, 'Blue Mountain')
        self.assertContains(response, 'Wallpaper dengan Tag "merah"')

    def test_home_page_renders_tag_buttons(self):
        wallpaper = create_wallpaper(title='Tagged Wallpaper')
        wallpaper.tags.add('alam')

        response = self.client.get(reverse('wallpapers:home'))

        self.assertContains(response, 'Semua')
        self.assertContains(response, '?tag=alam')

    def test_home_page_invalid_tag_returns_all(self):
        wp1 = create_wallpaper(title='First Wallpaper')
        wp1.tags.add('alam')

        response = self.client.get(reverse('wallpapers:home'), {'tag': 'tidak-ada'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Wallpaper')
        self.assertNotContains(response, 'Wallpaper dengan Tag')

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


class InteractiveFeaturesTests(MediaTestCase):
    """Uji fitur interaktif: favorit, download counter, dan pencarian lanjutan."""

    def setUp(self):
        self.user = create_user(username='fan')

    def test_toggle_favorite_adds_and_removes(self):
        wallpaper = create_wallpaper(title='Heart Me')
        self.client.login(username='fan', password='testpass123')

        response = self.client.post(
            reverse('wallpapers:toggle_favorite', kwargs={'slug': wallpaper.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(wallpaper, self.user.favorite_wallpapers.all())

        response = self.client.post(
            reverse('wallpapers:toggle_favorite', kwargs={'slug': wallpaper.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(wallpaper, self.user.favorite_wallpapers.all())

    def test_toggle_favorite_anonymous_redirects_to_login(self):
        wallpaper = create_wallpaper(title='Secret Heart')
        response = self.client.post(
            reverse('wallpapers:toggle_favorite', kwargs={'slug': wallpaper.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_home_page_renders_heart_button_for_authenticated(self):
        wallpaper = create_wallpaper(title='Heart Page')
        self.client.login(username='fan', password='testpass123')

        response = self.client.get(reverse('wallpapers:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse('wallpapers:toggle_favorite', kwargs={'slug': wallpaper.slug})
        )

    def test_favorites_page_requires_login(self):
        response = self.client.get(reverse('wallpapers:favorites'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_favorites_page_lists_favorited(self):
        wallpaper = create_wallpaper(title='My Favorite')
        wallpaper.favorites.add(self.user)
        self.client.login(username='fan', password='testpass123')

        response = self.client.get(reverse('wallpapers:favorites'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Favorite')

    def test_download_increments_counter_and_serves_file(self):
        wallpaper = create_wallpaper(title='Download Me')

        response = self.client.get(
            reverse('wallpapers:download', kwargs={'slug': wallpaper.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])

        wallpaper.refresh_from_db()
        self.assertEqual(wallpaper.downloads, 1)

    def test_search_by_orientation(self):
        create_wallpaper(title='Wide Shot', width=2000, height=1000)
        create_wallpaper(title='Tall Shot', width=800, height=1200)

        response = self.client.get(
            reverse('wallpapers:search'),
            {'q': 'shot', 'orientation': 'portrait'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tall Shot')
        self.assertNotContains(response, 'Wide Shot')

    def test_search_by_date_range(self):
        old = create_wallpaper(title='Old Wallpaper')
        old.created_at = timezone.now() - timedelta(days=10)
        old.save(update_fields=['created_at'])
        create_wallpaper(title='Fresh Wallpaper')

        response = self.client.get(
            reverse('wallpapers:search'),
            {'date_range': 'minggu_ini'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fresh Wallpaper')
        self.assertNotContains(response, 'Old Wallpaper')

    def test_search_page_renders_filter_dropdowns(self):
        response = self.client.get(reverse('wallpapers:search'))
        self.assertContains(response, 'Semua Orientasi')
        self.assertContains(response, 'Semua Waktu')
        self.assertContains(response, 'Landscape')
        self.assertContains(response, 'Portrait')


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

    def test_upload_rejects_oversized_file(self):
        self.client.login(username='admin', password='testpass123')
        category = create_category(name='Nature')
        from django.core.files.uploadedfile import SimpleUploadedFile
        big = SimpleUploadedFile('big.png', b'\x00' * (10 * 1024 * 1024 + 1024), content_type='image/png')
        response = self.client.post(reverse('wallpapers:upload'), {
            'title': 'Big File',
            'category': category.pk,
            'image': big,
        })

        # Validasi gagal -> redirect dengan flash error, tidak ada yang tersimpan
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Wallpaper.objects.count(), 0)

    def test_admin_list_search_filters_results(self):
        self.client.login(username='admin', password='testpass123')
        create_wallpaper(title='Sunset Beach')
        create_wallpaper(title='Mountain Peak')

        response = self.client.get(
            reverse('wallpapers:wallpaper_admin_list'),
            {'q': 'sunset'},
        )

        self.assertContains(response, 'Sunset Beach')
        self.assertNotContains(response, 'Mountain Peak')

    def test_admin_list_category_filter(self):
        self.client.login(username='admin', password='testpass123')
        nature = create_category(name='Nature')
        city = create_category(name='City')
        create_wallpaper(title='Forest Wallpaper', category=nature)
        create_wallpaper(title='Skyline Wallpaper', category=city)

        response = self.client.get(
            reverse('wallpapers:wallpaper_admin_list'),
            {'category': nature.slug},
        )

        self.assertContains(response, 'Forest Wallpaper')
        self.assertNotContains(response, 'Skyline Wallpaper')

    def test_edit_wallpaper_preserves_existing_data(self):
        self.client.login(username='admin', password='testpass123')
        category = create_category(name='Nature')
        wallpaper = create_wallpaper(
            title='Original Title',
            category=category,
            description='Deskripsi asli',
            width=1000,
            height=2000,
            is_premium=True,
        )
        wallpaper.tags.add('alam', 'indah')
        new_category = create_category(name='Abstrak')

        response = self.client.post(
            reverse('wallpapers:edit', kwargs={'pk': wallpaper.pk}),
            {'title': 'Judul Baru', 'category': new_category.pk},
        )

        self.assertEqual(response.status_code, 302)
        wallpaper.refresh_from_db()
        self.assertEqual(wallpaper.title, 'Judul Baru')
        self.assertEqual(wallpaper.category, new_category)
        self.assertEqual(wallpaper.description, 'Deskripsi asli')
        self.assertEqual(wallpaper.width, 1000)
        self.assertEqual(wallpaper.height, 2000)
        self.assertTrue(wallpaper.is_premium)
        self.assertEqual(list(wallpaper.tags.names()), ['alam', 'indah'])

    def test_edit_wallpaper_allows_removing_category(self):
        self.client.login(username='admin', password='testpass123')
        category = create_category(name='Nature')
        wallpaper = create_wallpaper(title='With Category', category=category)

        response = self.client.post(
            reverse('wallpapers:edit', kwargs={'pk': wallpaper.pk}),
            {'title': 'Without Category', 'category': ''},
        )

        self.assertEqual(response.status_code, 302)
        wallpaper.refresh_from_db()
        self.assertIsNone(wallpaper.category)

    def test_delete_removes_image_and_thumbnail_files(self):
        self.client.login(username='admin', password='testpass123')
        wallpaper = create_wallpaper(title='File Cleanup Wallpaper')
        image_name = wallpaper.image.name
        thumbnail_name = wallpaper.thumbnail.name if wallpaper.thumbnail else None
        self.assertTrue(wallpaper.image.storage.exists(image_name))
        if thumbnail_name:
            self.assertTrue(wallpaper.thumbnail.storage.exists(thumbnail_name))

        response = self.client.post(reverse('wallpapers:delete', kwargs={'pk': wallpaper.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Wallpaper.objects.filter(pk=wallpaper.pk).exists())
        self.assertFalse(wallpaper.image.storage.exists(image_name))
        if thumbnail_name:
            self.assertFalse(wallpaper.thumbnail.storage.exists(thumbnail_name))

    def test_bulk_delete_removes_files(self):
        self.client.login(username='admin', password='testpass123')
        wp1 = create_wallpaper(title='Bulk One')
        wp2 = create_wallpaper(title='Bulk Two')
        names = [wp1.image.name, wp2.image.name]

        response = self.client.post(
            reverse('wallpapers:delete_multiple'),
            {'selected_wallpapers': [str(wp1.pk), str(wp2.pk)]},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Wallpaper.objects.count(), 0)
        self.assertFalse(wp1.image.storage.exists(names[0]))
        self.assertFalse(wp2.image.storage.exists(names[1]))
