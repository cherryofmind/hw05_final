import tempfile
import shutil
from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache

from posts.models import Group, Post, User, Comment, Follow
from ..forms import PostForm
User = get_user_model()
ITEMS_PER_PAGE = 10
ITEMS_PER_PAGE_3 = 3


class PostPagesTests(TestCase):
    """Тестирование страниц во вью-функциях в приложении Posts"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='user',
            password='password'
        )
        cls.random_user = User.objects.create_user(
            username='user2',
            password='22227'
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовый текст',
        )
        cls.new_group = Group.objects.create(
            title='Тестовый заголовок 1',
            slug='test_slug_1',
            description='Тестовый текст 1',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='заголовок',
            pub_date='22.10.2022',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.author)

    def test_pages_uses_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.author}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': 1}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/post_create.html',
        }
        # Проверяем, что при обращении к name вызывается правильный HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_index_page_show_correct_context(self):
        """Шаблон главной страницы сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        context_objects = {
            self.author: first_object.author,
            self.post.text: first_object.text,
            self.group: first_object.group,
            self.post.id: first_object.id,
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_post_posts_groups_page_show_correct_context(self):
        """Проверяем Context страницы group_posts"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        first_object = response.context['group']
        context_objects = PostPagesTests.group
        self.assertEqual(first_object, context_objects)

    # Проверка словаря контекста страницы пользователя
    def test_post_profile_page_show_correct_context(self):
        """Шаблон страницы пользователя сформирован с правильным контекстом."""
        profile_url = reverse('posts:profile',
                              kwargs={'username': self.author.username})
        response = self.authorized_client.get(profile_url)
        first_object = response.context['page_obj'][0]
        context_objects = {
            self.author: first_object.author,
            self.post.text: first_object.text,
            self.group: first_object.group,
            self.post.id: first_object.id,
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    # Проверка словаря контекста страницы публикации
    def test_post_page_show_correct_context(self):
        """Шаблон страницы публикации сформирован с правильным контекстом."""
        post_url = reverse('posts:post_detail', kwargs={'post_id': 1})
        response = self.authorized_client.get(post_url)
        first_object = response.context['post']
        context_objects = {
            self.author: first_object.author,
            self.post.text: first_object.text,
            self.group: first_object.group,
            self.post.id: first_object.id,
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertTrue('is_edit' in response.context)

    def test_post_new_create_appears_on_correct_pages(self):
        """При создании поста он должен появляется на главной странице,
        на странице выбранной группы и в профиле пользователя"""
        exp_pages = [
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.author.username})
        ]
        for revers in exp_pages:
            with self.subTest(revers=revers):
                response = self.authorized_client.get(revers)
                self.assertIn(self.post, response.context['page_obj'])

    def test_posts_not_contain_in_wrong_group(self):
        """При создании поста он не появляется в другой группе"""
        post = Post.objects.get(pk=1)
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.new_group.slug})
        )
        self.assertNotIn(post, response.context['page_obj'].object_list)

    def test_new_post_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_index_cache(self):
        """ Получить текущее количество постов, создать новый пост,
        запросить страницу с постами и проверить что там нет нового поста,
        затем очистить кеш, снова запросить страницу с постами и увидеть,
        что там появился пост.
        """

        posts_in_bd = self.guest_client.get(reverse('posts:index')).content

        Post.objects.create(
            text='Тестовый текст нового поста',
            author=self.author,
        )

        posts_with_cache = self.guest_client.get(
            reverse('posts:index')).content

        self.assertEqual(
            posts_in_bd,
            posts_with_cache,
            'Количество постов отличается')

        cache.clear()

        posts_without_cache = self.guest_client.get(
            reverse('posts:index')).content

        self.assertNotEqual(
            posts_in_bd,
            posts_without_cache,
            'Количество постов одинаково')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовый текст',
        )

        objs = [
            Post(
                author=cls.author,
                group=cls.group,
                text='Заголовок',
                pub_date='23.10.2022',
            )
            for bulk in range(1, 14)
        ]
        cls.post = Post.objects.bulk_create(objs)

    def test_first_page_contains_ten_records(self):
        """Проверка: на первой странице должно быть 10 постов."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), ITEMS_PER_PAGE)

    def test_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), ITEMS_PER_PAGE_3)

    def test_group_list_contains_ten_pages(self):
        """Проверка: на  странице group_list должно быть 10 постов."""
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'})
        )
        self.assertEqual(len(response.context['page_obj']), ITEMS_PER_PAGE)

    def test_profile_contains_ten_records(self):
        """Проверка: на  странице профиля должно быть 10 постов."""
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.author.username}))
        self.assertEqual(len(response.context['page_obj']), ITEMS_PER_PAGE)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.MEDIA_ROOT)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание 1'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись для создания поста. Группа 1',
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        self.guest_client = Client()
        self.pages = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
                'posts/profile.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_content_contains_image(self):
        """Проверка вывода в контексте картинки на страницы main, group_list
         profile."""
        for reverse_name in self.pages.keys():
            response = self.authorized_client.get(reverse_name)
            image_file = response.context['page_obj'][0].image
            self.assertEqual(image_file, 'posts/small.gif')


class CommentTest(TestCase):
    """Проверка комментариев"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.postmaker = User.objects.create_user(username='postmaker')
        cls.postmaker_client = Client()
        cls.postmaker_client.force_login(cls.postmaker)
        cls.commentator = User.objects.create_user(username='commentator')
        cls.commentator_client = Client()
        cls.commentator_client.force_login(cls.commentator)
        cls.post = Post.objects.create(
            author=cls.postmaker,
            text='Тестовый текст',
        )

    def setUp(self):
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.commentator,
            text='Тестовый комментарий'
        )

    def test_comment_appear(self):
        """ Проверяем что коммент создан под постом """
        response = self.commentator_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        comment = response.context['comments'][0]
        text = comment.text
        self.assertEqual(text, self.comment.text)


class FollowerTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовая запись ленты',
        )
        self.follow_user = User.objects.create_user(username='follow')
        self.follow_client = Client()
        self.follow_client.force_login(self.follow_user)

    def test_follow_user_to_author(self):
        """Проверка подписки и отписки на авторов."""
        self.follow_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user}))
        follow = Follow.objects.filter(user=self.follow_user,
                                       author=self.user).exists()
        self.assertTrue(follow)
        self.follow_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.user}))
        follow = Follow.objects.filter(user=self.follow_user,
                                       author=self.user).exists()
        self.assertEqual(follow, False)

    def test_subscription_feed(self):
        """Запись появляется в ленте подписчиков."""
        Follow.objects.create(user=self.follow_user,
                              author=self.user)
        response = self.follow_client.get(reverse('posts:follow_index'))
        post_text_0 = response.context["page_obj"][0].text
        self.assertEqual(post_text_0, 'Тестовая запись ленты')
        # проверяем собственную ленту в качестве неподписанного пользователя
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, 'Тестовая запись ленты')
