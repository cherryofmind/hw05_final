from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post
import shutil
import tempfile
from django.conf import settings

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.new_user = User.objects.create_user(username='auth')
        cls.new_user_client = Client()
        cls.new_user_client.force_login(cls.new_user)

        cls.group = Group.objects.create(
            title='group',
            slug='test_slug',
            description='Описание',
        )
        cls.post = Post.objects.create(
            author=cls.new_user,
            text='Тестовый пост',
            group=cls.group,
        )
        # Создаем форму, если нужна проверка атрибутов
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_form_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count() + 1
        form_data = {
            'text': 'Текст из формы',
            'group': PostCreateFormTests.group.pk,
        }
        self.new_user_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            Post.objects.count(),
            posts_count,
            'Не удалось создать новый пост'
        )

    def test_post_edit(self):
        """При отправке формы происходит изменение поста с post_id в базе данных.
        """
        form_data = {
            'text': 'Пост который отредактировали',
            'group': self.group.pk,
        }

        self.new_user_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )

        self.assertEqual(
            Post.objects.get(
                pk=self.post.pk
            ).text,
            'Пост который отредактировали',
            'Ожидаемый текст не подходит'
        )

        self.assertEqual(
            Post.objects.get(
                pk=self.post.pk
            ).group,
            self.group,
            'Ожидаемая группа не подходит'
        )
