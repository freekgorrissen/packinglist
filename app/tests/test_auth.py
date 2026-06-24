from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse


class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = 'testpass123'
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password=self.password,
        )

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse('home'))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('home')}",
        )

    def test_login_success(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'testuser', 'password': self.password},
        )
        self.assertRedirects(response, reverse('home'))

    def test_login_failure(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'testuser', 'password': 'wrong'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_logout(self):
        self.client.login(username='testuser', password=self.password)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

        response = self.client.get(reverse('home'))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('home')}",
        )


class ProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = 'testpass123'
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password=self.password,
        )
        self.client.login(username='testuser', password=self.password)

    def test_profile_page_loads(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'Change password')

    def test_change_password(self):
        response = self.client.post(
            reverse('profile'),
            {
                'old_password': self.password,
                'new_password1': 'newpass456!',
                'new_password2': 'newpass456!',
                'save_password': '1',
            },
        )
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass456!'))

    def test_change_password_wrong_old_password(self):
        response = self.client.post(
            reverse('profile'),
            {
                'old_password': 'wrong',
                'new_password1': 'newpass456!',
                'new_password2': 'newpass456!',
                'save_password': '1',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.check_password(self.password))


class EnsureUserCommandTests(TestCase):
    def test_creates_user_from_options(self):
        call_command('ensure_user', username='admin', password='secret123')
        user = get_user_model().objects.get(username='admin')
        self.assertTrue(user.check_password('secret123'))

    def test_skips_existing_user(self):
        get_user_model().objects.create_user(username='admin', password='old')
        call_command('ensure_user', username='admin', password='new')
        user = get_user_model().objects.get(username='admin')
        self.assertTrue(user.check_password('old'))

    def test_skips_when_credentials_missing(self):
        call_command('ensure_user', username=None, password=None)
        self.assertEqual(get_user_model().objects.count(), 0)
