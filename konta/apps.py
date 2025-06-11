from django.apps import AppConfig

class KontaConfig(AppConfig):
    """
    Configuration class for the 'konta' app.

    Sets the default primary key type and specifies the application name.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'konta'
