from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import register_view, CustomLoginView

app_name = 'konta'

urlpatterns = [
    # Custom login view with logging
    path('login/', CustomLoginView.as_view(), name="login"),

    # User profile page (requires login)
    path('profil/', views.profile, name='profile'),

    # Logout view with redirection to login
    path('logout/', auth_views.LogoutView.as_view(next_page='konta:login'), name='logout'),

    # User registration view
    path('register/', register_view, name='register'),

    path('test-email/', views.test_email_view, name='test_email'),

    path('aktywuj/<uidb64>/<token>/', views.activate_account, name='activate'),
]
