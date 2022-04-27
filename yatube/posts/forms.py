from django import forms
from django.forms import ModelForm, Textarea
from .models import Post, Comment


class PostForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea, required=True)

    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        label = {
            'text': ('Текст поста'),
            'group': ('Группа поста'),
            'image': ('Изображение')
        }
        help_texts = {
            'text': ('Текст нового поста'),
            'group': ('Группа, к которой будет относиться пост'),
            'image': ('Выберите изображение')
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Добавить комментарий'}
        help_texts = {'text': 'Текст комментария'}
        widgets = {'text': Textarea(attrs={'class': 'form-control'})}
