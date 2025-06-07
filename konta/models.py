from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('tourist', 'Tourist'),
        ('guide', 'Guide'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin')
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='tourist',
        verbose_name="Rola użytkownika"
    )
    registration_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data rejestracji"
    )

    class Meta:
        verbose_name = "Użytkownik"
        verbose_name_plural = "Użytkownicy"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
