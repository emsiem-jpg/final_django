import logging
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user registration form based on Django's UserCreationForm.

    Adds an email field with validation and custom styling.

    Fields:
        - username
        - email (required)
        - password1
        - password2
    """
    email = forms.EmailField(
        required=True,
        label='Adres e-mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'np. email@example.com'
        })
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        """Applies consistent Bootstrap styling to all fields."""
        super().__init__(*args, **kwargs)
        try:
            for field in self.fields.values():
                field.widget.attrs.setdefault('class', 'form-control')
            logger.debug("Zainicjalizowano CustomUserCreationForm")
        except Exception as e:
            logger.error(f"Błąd inicjalizacji CustomUserCreationForm: {e}", exc_info=True)


class LoginForm(AuthenticationForm):
    """
    Custom login form extending Django's built-in AuthenticationForm.

    Adds Bootstrap styling and placeholders.
    """
    username = forms.CharField(
        label="Nazwa użytkownika",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Wprowadź login'
        })
    )

    password = forms.CharField(
        label="Hasło",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Wprowadź hasło'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug("Zainicjalizowano LoginForm")
