from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    text = models.TextField(verbose_name='Текст сообщения',
                            help_text=('Обязательное поле,'
                                       'не должно быть пустым'))
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
        help_text='Выберите имя автора')
    group = models.ForeignKey(
        'Group',
        blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Выберите название группы')
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        # выводим текст поста
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок группы',
                             help_text='Укажите заголовок группы')
    slug = models.SlugField(unique=True, verbose_name="URL",
                            help_text='Slug это уникальная строка,'
                                      'понятная человеку')
    description = models.TextField(verbose_name='Описание',
                                   help_text='У группы должно быть описание')

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments', verbose_name='Пост',
                             help_text='Под каким постом оставлен комментарий')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name='Автор комментария',
                               help_text='Автор отображается на сайте')
    text = models.TextField(verbose_name='Текст комментария',
                            help_text=('Обязательное поле,'
                                       'не должно быть пустым'))
    created = models.DateTimeField(verbose_name='Дата публикации',
                                   help_text='Дата публикации',
                                   auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower')

    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following')

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='uniq_follow'),
        )

    def __str__(self):
        return f'{self.user}'
