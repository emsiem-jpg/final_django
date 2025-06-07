from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from plany.views_api import PlanViewSet
from atrakcje.views_api import CennikViewSet

from atrakcje.views import strona_glowna, lista_atrakcji, szczegoly_atrakcji
from plany.views import podglad_planu

from rest_framework.routers import DefaultRouter
from atrakcje.views_api import AtrakcjaViewSet

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Swagger schema config
schema_view = get_schema_view(
    openapi.Info(
        title="Przewodnik API",
        default_version='v1',
        description="Dokumentacja API aplikacji",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# API router
router = DefaultRouter()
router.register(r'api/atrakcje', AtrakcjaViewSet, basename='atrakcje')
router.register(r'api/plany', PlanViewSet)
router.register(r'api/cennik', CennikViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', strona_glowna, name='strona_glowna'),
    path('atrakcje/', lista_atrakcji, name='lista_atrakcji'),
    path('atrakcja/<int:id>/', szczegoly_atrakcji, name='szczegoly'),
    path('plany/', include('plany.urls')),
    path('konta/', include('konta.urls')),
     # autoryzacja

    # Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/schema/', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    path('plany/podglad/', podglad_planu, name='podglad_planu'),

    # API endpoints
    path('', include(router.urls)),
    path('api/', include('atrakcje.urls_api')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
