from django.shortcuts import render, get_object_or_404, redirect
from .models import Follow, Post, Group, User
from .forms import PostForm
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.core.cache import cache

from .forms import PostForm, CommentForm

@require_GET
def index(request):
    posts = cache.get('posts:main')
    if posts is None:
        posts = Post.objects.select_related('group').all()
        cache.set('posts:main', posts, timeout=20)
    
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Отдаем в словаре контекста
    context = {
        'page_obj': page_obj,
        'posts': post_list,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all().order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'group': group,
        'posts': post_list,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = User.objects.get(username=username)
    author_post = Post.objects.filter(author=author).order_by('-pub_date')
    posts_numbers = author_post.count()
    paginator = Paginator(author_post, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = author.following.all()
    follower = author.follower.all()
    count_follower = follower.count()
    count_following = following.count()
    context = {
        'page_obj': page_obj,
        'author': author,
        'author_post': author_post,
        'posts_numbers': posts_numbers,
        'count_following': count_following,
        'count_follower': count_follower,
        'following': following}

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    form = CommentForm(request.POST or None, files=request.FILES or None)
    post = Post.objects.select_related('author', 'group').get(id=post_id)
    post_count = Post.objects.filter(author=post.author).count()
    post_list = post.author.posts.all()
    comments = post.comments.all()
    context = {
        'post_list': post_list,
        'post': post,
        'post_count': post_count,
        'form': form,
        'comments': comments,

    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', str(request.user))
    return render(request, 'posts/post_create.html', {'form': form})

@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_edit = True
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)

    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/post_create.html', {'form': form,
                  'is_edit': is_edit})

@login_required
def add_comment(request, post_id):
    # Получите пост 
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)

@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page}
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)

    if request.user != author:
        Follow.objects.get_or_create(
            author=author,
            user=request.user
        )

    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author, user=request.user).delete()

    return redirect('posts:profile', username)
