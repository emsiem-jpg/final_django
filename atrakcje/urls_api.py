from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import AtrakcjaViewSet

router = DefaultRouter()
router.register(r'atrakcje', AtrakcjaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]