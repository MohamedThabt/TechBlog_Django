from django.urls import path
from . import views
from blog import views as blog_views

app_name = 'blog'

urlpatterns = [
    path('', views.post_list, name='post_list'),  # Make post_list the main page
    path('home/', blog_views.home_view, name='home'),  # Moved home to a separate path
    path('register/', blog_views.register_view, name='register'),
    path('login/', blog_views.login_view, name='login'),
    path('logout/', blog_views.logout_view, name='logout'),
    path('dashboard/', blog_views.dashboard_view, name='dashboard'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/new/', views.post_create, name='post_create'),
    path('post/<int:pk>/edit/', views.post_update, name='post_update'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('post/<int:pk>/like/', views.like_post, name='like_post'),
    path('author/<str:username>/', views.author_posts, name='author_posts'),
    path('about/', views.about_us, name='about_us'),
]
