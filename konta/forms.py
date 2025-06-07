from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Adres e-mail', widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Nazwa użytkownika",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wprowadź login'})
    )
    password = forms.CharField(
        label="Hasło",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Wprowadź hasło'})
    )