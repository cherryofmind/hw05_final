import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from http import HTTPStatus

from ..forms import PostForm
from ..models import Group, Post
import shutil
from django.conf import settings

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


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
        upload = SimpleUploadedFile(
            name='small_for_create.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст из формы',
            'group': PostCreateFormTests.group.pk,
            'image': upload,
        }
        response = self.new_user_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            Post.objects.count(),
            posts_count,
            'Не удалось создать новый пост'
        )
        tested_post = Post.objects.first()
        self.assertEqual(tested_post.group.id, form_data['group'])
        self.assertEqual(tested_post.text, form_data['text'])
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={
                'username': PostCreateFormTests.new_user}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.latest('pk').text, form_data['text'])
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                image='posts/small_for_create.gif'
            ).first()
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
