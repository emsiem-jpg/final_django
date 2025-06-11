from django.contrib import admin
from .models import PlanZwiedzania, PlanUzytkownika, EtapPlanu, ElementEtapu

@admin.register(PlanZwiedzania)
class PlanZwiedzaniaAdmin(admin.ModelAdmin):
    """
    Admin configuration for the PlanZwiedzania model.

    Displays basic metadata such as name, status, visibility, and timestamps.
    Allows filtering and searching by status, visibility, name, and description.
    """
    list_display = ('nazwa', 'status', 'is_public', 'data_utworzenia', 'data_modyfikacji')
    list_filter = ('status', 'is_public')
    search_fields = ('nazwa', 'opis')


@admin.register(PlanUzytkownika)
class PlanUzytkownikaAdmin(admin.ModelAdmin):
    """
    Admin configuration for the PlanUzytkownika model.

    Allows management of user-plan relationships and ownership status.
    """
    list_display = ('uzytkownik', 'plan', 'jest_wlascicielem')
    list_filter = ('jest_wlascicielem',)
    search_fields = ('uzytkownik__username', 'plan__nazwa')


@admin.register(EtapPlanu)
class EtapPlanuAdmin(admin.ModelAdmin):
    """
    Admin configuration for the EtapPlanu model.

    Displays stages of plans with order and allows searching by stage or plan name.
    """
    list_display = ('plan', 'nazwa', 'kolejnosc')
    search_fields = ('nazwa', 'plan__nazwa')


@admin.register(ElementEtapu)
class ElementEtapuAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ElementEtapu model.

    Manages attractions within each stage, showing timing and order details.
    """
    list_display = ('etap', 'atrakcja', 'kolejnosc', 'planowana_data', 'czas_wizyty', 'czas_dojazdu')
    list_filter = ('etap__plan',)
    search_fields = ('etap__nazwa', 'atrakcja__nazwa')
