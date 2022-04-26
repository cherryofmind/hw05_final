from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='auth',
                                            email='test@gmail.com',
                                            password='password',),
            text='Тестовая пост'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

    def test_title_label_post(self):
        """ Проверка наличия verbose_name при создании поста """
        task = PostModelTest.post
        verbose = task._meta.get_field('group').verbose_name
        self.assertEqual(verbose, 'Группа')

    def test_title_help_text_post(self):
        """ Проверка наличия help_text (подсказки), при выборе группы """
        task = PostModelTest.post
        help_texts = task._meta.get_field('group').help_text
        self.assertEqual(help_texts, 'Выберите название группы')

    def test_title_label_group(self):
        """ Проверка наличия verbose_name при создании группы """
        task = PostModelTest.group
        verbose = task._meta.get_field('title').verbose_name
        self.assertEqual(verbose, 'Заголовок группы')

    def test_title_help_text_group(self):
        """ Проверка наличия help_text (подсказки), при создании группы """
        task = PostModelTest.group
        help_texts = task._meta.get_field('title').help_text
        self.assertEqual(help_texts, 'Укажите заголовок группы')

    def test_obj_name_title_field_group(self):
        """ Проверка наличия поля title в модели данных группы """
        task = PostModelTest.group
        expected_object_name = task.title
        self.assertEquals(expected_object_name, str(task))

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = self.post
        string = post.text[:15]
        self.assertEqual(string, str(post), 'Некорректная работа текста')
