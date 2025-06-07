from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_atrakcji, name='lista_atrakcji'),
    path('<int:id>/', views.szczegoly_atrakcji, name='szczegoly_atrakcji'),
    path('dodaj/', views.dodaj_atrakcje, name='dodaj_atrakcje'),
]