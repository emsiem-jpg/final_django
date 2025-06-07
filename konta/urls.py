from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import register_view, CustomLoginView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name="login"),
    path('profile/', views.profile, name='profile'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', register_view, name='register'),
]
