from django.urls import path
from . import views

app_name = 'plany'

urlpatterns = [
    path('koszyk/', views.koszyk, name='koszyk'),
    path('dodaj-do-koszyka/<int:atrakcja_id>/', views.dodaj_do_koszyka, name='dodaj_do_koszyka'),
    path('usun-z-koszyka/<int:atrakcja_id>/', views.usun_z_koszyka, name='usun_z_koszyka'),
    path('zapisz/', views.zapisz_plan, name='zapisz_plan'),
    path('plan/<int:id>/', views.szczegoly_planu, name='szczegoly_planu'),
    path('export/pdf/<int:id>/', views.export_plan_pdf, name='export_plan_pdf'),
    path('usun/<int:id>/', views.usun_plan, name='usun_plan'),
    path('podglad/', views.podglad_planu, name='podglad_planu'),
]
