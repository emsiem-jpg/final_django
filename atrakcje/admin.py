import logging
from django.contrib import admin
from .models import (
    Kategoria, Lokalizacja, Atrakcja, StatusAtrakcji,
    ZdjecieAtrakcji, GodzinyOtwarcia, RodzajBiletu, Cennik
)

from django import forms

logger = logging.getLogger(__name__)

class LokalizacjaInline(admin.StackedInline):
    """Inline for entering the location of an attraction."""
    model = Lokalizacja
    extra = 0
    min_num = 1
    max_num = 1


class ZdjecieAtrakcjiInline(admin.TabularInline):
    """Inline for adding multiple photos of the attraction."""
    model = ZdjecieAtrakcji
    extra = 1


class GodzinyOtwarciaInline(admin.TabularInline):
    """Inline for entering weekly opening hours."""
    model = GodzinyOtwarcia
    extra = 7


class LokalizacjaForm(forms.ModelForm):
    """Custom form for Lokalizacja with placeholders for easier input."""
    class Meta:
        model = Lokalizacja
        fields = '__all__'
        widgets = {
            'miasto': forms.TextInput(attrs={'placeholder': 'e.g. Warsaw'}),
            'ulica': forms.TextInput(attrs={'placeholder': 'e.g. Main Square'}),
            'numer_budynku': forms.TextInput(attrs={'placeholder': 'e.g. 1'}),
            'kod_pocztowy': forms.TextInput(attrs={'placeholder': 'e.g. 00-001'}),
        }


class KategoriaAdmin(admin.ModelAdmin):
    """Admin interface for Kategoria."""
    pass


class AtrakcjaAdmin(admin.ModelAdmin):
    """Admin interface for Atrakcja, including inlines for related models."""
    inlines = [LokalizacjaInline, ZdjecieAtrakcjiInline, GodzinyOtwarciaInline]
    list_display = ('nazwa', 'kategoria', 'display_adres')
    list_filter = ('kategoria',)
    search_fields = ('nazwa', 'opis', 'lokalizacja__miasto', 'lokalizacja__ulica')

    def display_adres(self, obj):
        """Displays formatted address from related Lokalizacja."""
        try:
            adres = obj.adres()
            logger.debug(f"Displaying address for '{obj.nazwa}': {adres}")
            return adres
        except Exception as e:
            logger.error(f"Error displaying address for '{obj}': {e}", exc_info=True)
            return "—"
    display_adres.short_description = 'Address'


class ZdjecieAtrakcjiAdmin(admin.ModelAdmin):
    """Admin interface for ZdjecieAtrakcji."""
    list_display = ('atrakcja', 'is_glowne', 'opis')
    search_fields = ('atrakcja__nazwa',)


class StatusAtrakcjiAdmin(admin.ModelAdmin):
    """Admin interface for StatusAtrakcji."""
    list_display = ('atrakcja', 'status', 'data_zmiany')
    list_filter = ('status',)


class GodzinyOtwarciaAdmin(admin.ModelAdmin):
    """Admin interface for GodzinyOtwarcia."""
    list_display = ('atrakcja', 'dzien_tygodnia', 'godzina_otwarcia', 'godzina_zamkniecia', 'czy_otwarte')
    list_filter = ('czy_otwarte',)


class RodzajBiletuAdmin(admin.ModelAdmin):
    """Admin interface for RodzajBiletu."""
    list_display = ('nazwa',)


class CennikAdmin(admin.ModelAdmin):
    """Admin interface for Cennik."""
    list_display = ('atrakcja', 'rodzaj_biletu', 'cena', 'waluta', 'ważny_od', 'ważny_do')
    list_filter = ('waluta',)


admin.site.register(Kategoria, KategoriaAdmin)
admin.site.register(Atrakcja, AtrakcjaAdmin)
admin.site.register(ZdjecieAtrakcji, ZdjecieAtrakcjiAdmin)
admin.site.register(StatusAtrakcji, StatusAtrakcjiAdmin)
admin.site.register(GodzinyOtwarcia, GodzinyOtwarciaAdmin)
admin.site.register(RodzajBiletu, RodzajBiletuAdmin)
admin.site.register(Cennik, CennikAdmin)

logger.info("Zarejestrowano modele admina: Kategoria, Atrakcja, Zdjęcia, Statusy, Godziny, Bilety, Cenniki")
