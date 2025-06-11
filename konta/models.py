import logging
from django.db import models
from django.contrib.auth.models import AbstractUser

logger = logging.getLogger(__name__)

class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Adds user role and registration date fields.

    Attributes:
        role (str): The role of the user (e.g. Tourist, Guide, etc.).
        registration_date (datetime): Timestamp when the user registered.
    """

    ROLE_CHOICES = [
        ('tourist', 'Tourist'),
        ('guide', 'Guide'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
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
        user_str = f"{self.username} ({self.get_role_display()})"
        logger.debug(f"__str__ wywołane dla użytkownika: {user_str}")
        return user_str

    def save(self, *args, **kwargs):
        is_created = self._state.adding
        super().save(*args, **kwargs)
        if is_created:
            logger.info(f"Zarejestrowano nowego użytkownika: {self.username} jako {self.role}")
