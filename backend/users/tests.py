from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from wallpapers.tests.helpers import MediaTestCase, create_user

User = get_user_model()


class UserManagementTests(MediaTestCase):
    """Uji manajemen pengguna (CRUD) di dashboard admin."""

    def setUp(self):
        self.staff_user = create_user(username='staff', is_staff=True)
        self.regular_user = create_user(username='regular')

    def test_anonymous_redirected_from_user_list(self):
        response = self.client.get(reverse('users:user-list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_regular_user_forbidden_from_user_list(self):
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('users:user-list'))
        self.assertEqual(response.status_code, 403)

    def test_staff_can_open_user_list(self):
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('users:user-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'regular')

    def test_user_add_creates_user(self):
        self.client.login(username='staff', password='testpass123')
        response = self.client.post(reverse('users:user-add'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'Str0ngPass123!',
            'password2': 'Str0ngPass123!',
            'role': 'admin',
        })

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newuser')
        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.check_password('Str0ngPass123!'))

    def test_user_add_rejects_password_mismatch(self):
        self.client.login(username='staff', password='testpass123')
        response = self.client.post(reverse('users:user-add'), {
            'username': 'baduser',
            'password1': 'Str0ngPass123!',
            'password2': 'different123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='baduser').exists())

    def test_toggle_user_status_bans_and_reactivates(self):
        self.client.login(username='staff', password='testpass123')
        target = create_user(username='target')

        response = self.client.post(
            reverse('users:toggle-user-status', kwargs={'user_id': target.pk})
        )
        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        self.assertFalse(target.is_active)

        response = self.client.post(
            reverse('users:toggle-user-status', kwargs={'user_id': target.pk})
        )
        target.refresh_from_db()
        self.assertTrue(target.is_active)

    def test_cannot_toggle_own_status(self):
        self.client.login(username='staff', password='testpass123')
        response = self.client.post(
            reverse('users:toggle-user-status', kwargs={'user_id': self.staff_user.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.staff_user.refresh_from_db()
        self.assertTrue(self.staff_user.is_active)
