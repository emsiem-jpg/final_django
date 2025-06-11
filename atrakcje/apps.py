from django.apps import AppConfig

class AtrakcjeConfig(AppConfig):
    """
    Configuration class for the 'atrakcje' application.
    
    This class defines metadata and default settings for the attractions app,
    such as the default auto primary key field and the app name.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'atrakcje'
