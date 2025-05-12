from django.shortcuts import render  # Added render back
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from .models import Post, Like, Comment  # Added Comment
from .forms import PostForm, CommentForm  # Added CommentForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Create your views here.

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    ordering = ['-created_at']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add liked posts to context if user is authenticated
        if self.request.user.is_authenticated:
            user_likes = Like.objects.filter(user=self.request.user).values_list('post_id', flat=True)
            context['user_likes'] = user_likes
        return context

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        # Check if user liked this post
        if self.request.user.is_authenticated:
            context['user_liked'] = Like.objects.filter(
                user=self.request.user, 
                post=post
            ).exists()
            context['likes_count'] = post.likes.count()
        
        context['comment_form'] = CommentForm()
        context['comments'] = post.comments.all().order_by('-created_at')  # Get comments for the post
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to comment.")
            return redirect('login')  # Or wherever your login URL is

        post = self.get_object()
        comment_form = CommentForm(request.POST)

        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.user = request.user
            new_comment.save()
            messages.success(request, "Your comment has been added.")
            return redirect('blog:post_detail', pk=post.pk)
        else:
            # If form is not valid, re-render the page with the form and errors
            context = self.get_context_data()
            context['comment_form'] = comment_form  # Pass the form with errors
            messages.error(request, "There was an error with your comment. Please check the form.")
            return self.render_to_response(context)

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    success_url = reverse_lazy('blog:post_list')  # Redirect to post_list after successful creation

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    success_url = reverse_lazy('blog:post_list')  # Redirect to post_list after successful update

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/post_confirm_delete.html'
    success_url = reverse_lazy('blog:post_list')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class LikePostView(LoginRequiredMixin, View):
    """
    View for handling post likes
    """
    def post(self, request, pk):
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
