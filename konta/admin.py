import logging
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

logger = logging.getLogger(__name__)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for the custom User model.

    Extends Django's default UserAdmin to include additional fields:
    - 'role': indicates user type (tourist, guide, moderator, admin)
    - 'registration_date': the date the user registered

    Modifies:
        - fieldsets: Adds a section for custom fields in the user detail view.
        - list_display: Adds custom fields to the user list in the admin.
        - list_filter: Adds filtering options by role.
    """

    try:
        fieldsets = BaseUserAdmin.fieldsets + (
            ('Additional Information', {
                'fields': ('role', 'registration_date'),
            }),
        )

        list_display = ('username', 'email', 'role', 'is_staff', 'is_superuser')
        list_filter = BaseUserAdmin.list_filter + ('role',)
        readonly_fields = ('registration_date',)
        search_fields = ('username', 'email')

        logger.info("UserAdmin zarejestrowany z dodatkowymi polami: role, registration_date")
    except Exception as e:
        logger.error(f"Błąd podczas konfiguracji UserAdmin: {e}", exc_info=True)
