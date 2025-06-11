from django.urls import path
from . import views

urlpatterns = [
    # Displays a paginated list of attractions, optionally filtered by city
    path('', views.lista_atrakcji, name='lista_atrakcji'),

    # Displays details for a specific attraction by ID
    path('<int:id>/', views.szczegoly_atrakcji, name='szczegoly_atrakcji'),
]
