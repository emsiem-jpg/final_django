from django.urls import path
from . import views

# Namespace for URL namespacing in templates and reverse() calls
app_name = 'plany'

urlpatterns = [
    # Displays the cart content and day assignment form
    path('koszyk/', views.koszyk, name='koszyk'),

    # Adds an attraction to the user's session-based cart
    path('dodaj-do-koszyka/<int:atrakcja_id>/', views.dodaj_do_koszyka, name='dodaj_do_koszyka'),

    # Removes an attraction from the user's cart
    path('usun-z-koszyka/<int:atrakcja_id>/', views.usun_z_koszyka, name='usun_z_koszyka'),

    # Saves the sightseeing plan based on the cart contents
    path('zapisz/', views.zapisz_plan, name='zapisz_plan'),

    # Shows the detailed view of a sightseeing plan (with stage maps)
    path('plan/<int:id>/', views.szczegoly_planu, name='szczegoly_planu'),

    # Exports the sightseeing plan to a downloadable PDF
    path('export/pdf/<int:id>/', views.export_plan_pdf, name='export_plan_pdf'),

    # Deletes a plan if the current user is the owner
    path('usun/<int:id>/', views.usun_plan, name='usun_plan'),

]
