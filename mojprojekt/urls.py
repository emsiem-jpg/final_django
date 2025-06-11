from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Debug toolbar (only loaded in DEBUG mode)
import debug_toolbar

# Regular views
from atrakcje.views import strona_glowna, lista_atrakcji, szczegoly_atrakcji

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # Public views
    path('', strona_glowna, name='strona_glowna'),
    path('atrakcje/', lista_atrakcji, name='lista_atrakcji'),
    path('atrakcja/<int:id>/', szczegoly_atrakcji, name='szczegoly'),
    
    # App-specific routes
    path('plany/', include('plany.urls')),
    path('konta/', include('konta.urls')),  # User auth/account management
]

# Serving media files in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Django Debug Toolbar (enabled only in DEBUG mode)
if settings.DEBUG:
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
