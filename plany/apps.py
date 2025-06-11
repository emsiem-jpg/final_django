from django.apps import AppConfig

class PlanyConfig(AppConfig):
    """
    Configuration class for the 'plany' application.

    This class defines the default primary key field type and
    the name of the application module.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plany'
