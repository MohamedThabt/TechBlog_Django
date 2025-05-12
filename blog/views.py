from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Post, Like
from django.contrib.auth.models import User
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required

# Create your views here.

def author_posts(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(post_list, 6)  # Show 6 posts per page
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'posts': posts,
        'author': author,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': posts,  # For compatibility with pagination template
    }
    
    # Add liked posts to context if user is authenticated
    if request.user.is_authenticated:
        user_likes = Like.objects.filter(user=request.user).values_list('post_id', flat=True)
        context['user_likes'] = user_likes
        
    return render(request, 'blog/author_posts.html', context)

def post_list(request):
    post_list = Post.objects.all().order_by('-created_at')
    
    # Handle search queries
    query = request.GET.get('q')
    if query:
        post_list = post_list.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )
    
    context = {
        'posts': post_list
    }
    
    # Add liked posts to context if user is authenticated
    if request.user.is_authenticated:
        user_likes = Like.objects.filter(user=request.user).values_list('post_id', flat=True)
        context['user_likes'] = user_likes
    
    return render(request, 'blog/post_list.html', context)

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all().order_by('-created_at')
    
    context = {
        'object': post,  # Using object for template compatibility
        'comments': comments
    }
    
    # Check if user liked this post
    if request.user.is_authenticated:
        context['user_liked'] = Like.objects.filter(
            user=request.user, 
            post=post
        ).exists()
        context['likes_count'] = post.likes.count()
    
    # Handle comment form
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to comment.")
            return redirect('login')
            
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.user = request.user
            new_comment.save()
            messages.success(request, "Your comment has been added.")
            return redirect('blog:post_detail', pk=post.pk)
        else:
            context['comment_form'] = comment_form
            messages.error(request, "There was an error with your comment. Please check the form.")
    else:
        context['comment_form'] = CommentForm()
    
    return render(request, 'blog/post_detail.html', context)

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Your post has been created.")
            return redirect('blog:post_list')
    else:
        form = PostForm()
    
    return render(request, 'blog/post_form.html', {'form': form})

@login_required
def post_update(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user is the author
    if request.user != post.author:
        messages.error(request, "You cannot edit this post.")
        return redirect('blog:post_detail', pk=post.pk)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Your post has been updated.")
            return redirect('blog:post_list')
    else:
        form = PostForm(instance=post)
    
    return render(request, 'blog/post_form.html', {'form': form})

@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user is the author
    if request.user != post.author:
        messages.error(request, "You cannot delete this post.")
        return redirect('blog:post_detail', pk=post.pk)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Your post has been deleted.")
        return redirect('blog:post_list')
    
    return render(request, 'blog/post_confirm_delete.html', {'object': post})

@login_required
def like_post(request, pk):
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=pk)
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        
        # If like existed and this is a toggle (unlike), delete it
        if not created:
            like.delete()
            messages.success(request, f"You've unliked '{post.title}'")
        else:
            messages.success(request, f"You've liked '{post.title}'")
        
        # Redirect back to the page user came from
        next_url = request.POST.get('next', 'blog:post_list')
        if next_url == 'detail':
            return redirect('blog:post_detail', pk=post.pk)
        return redirect('blog:post_list')

def about_us(request):
    return render(request, 'blog/about_us.html')
