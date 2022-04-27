# posts/tests/test_urls.py
from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='auth',
                                            email='test@gmail.com',
                                            password='password',),
            text='Тестовая пост',
        )

        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_list(self):
        """
        Тестирование по списку, для анонимного пользователя,
        список URL, где ответ должен быть равен 200
        """
        url_list = ['/', '/group/test_slug/']
        for test_url in url_list:
            response = self.guest_client.get(test_url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_url(self):
        """без авторизации приватные URL недоступны"""
        url_names = (
            '/create/',
            '/admin/',
        )
        for adress in url_names:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_url_redirect_anonymous(self):
        """Страница /create/ перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_new_page_login_user(self):
        """
        Тестирование по списку, для авторизированного пользователя,
        список URL, где ответ должен быть равен 200
        """
        url_list = ['/', '/group/test_slug/', '/create/']
        for test_url in url_list:
            response = self.authorized_client.get(test_url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/create/': 'posts/post_create.html',
            '/profile/auth/': 'posts/profile.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_404_url_exists_at_desired_location(self):
        """Страница 404 доступна любому пользователю."""
        response = self.guest_client.get('/group/test/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
