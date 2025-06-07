from django.contrib import admin
from .models import (
    Kategoria, Lokalizacja, Atrakcja, StatusAtrakcji,
    ZdjecieAtrakcji, GodzinyOtwarcia, RodzajBiletu, Cennik
)
from django.utils.html import format_html
from django.conf import settings
import googlemaps
from django import forms


class LokalizacjaInline(admin.StackedInline):
    model = Lokalizacja
    extra = 0
    min_num = 1
    max_num = 1  # ponieważ OneToOne

    def save_model(self, request, obj, form, change):
        adres = f"{obj.ulica} {obj.numer_budynku}, {obj.kod_pocztowy} {obj.miasto}"
        gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
        try:
            geocode_result = gmaps.geocode(adres)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                obj.szerokosc_geo = location['lat']
                obj.dlugosc_geo = location['lng']
        except Exception as e:
            self.message_user(request, f"Błąd geokodowania: {str(e)}", level='error')
        super().save_model(request, obj, form, change)


class LokalizacjaForm(forms.ModelForm):
    class Meta:
        model = Lokalizacja
        fields = '__all__'
        widgets = {
            'miasto': forms.TextInput(attrs={'placeholder': 'np. Warszawa'}),
            'ulica': forms.TextInput(attrs={'placeholder': 'np. Rynek Główny'}),
            'numer_budynku': forms.TextInput(attrs={'placeholder': 'np. 1'}),
            'kod_pocztowy': forms.TextInput(attrs={'placeholder': 'np. 00-001'}),
        }


class KategoriaAdmin(admin.ModelAdmin):
    list_display = ('nazwa', 'display_icon')
    fields = ('nazwa', 'ikona', 'icon_preview')
    readonly_fields = ('icon_preview',)

    def display_icon(self, obj):
        return format_html('<i class="{}"></i>', obj.ikona) if obj.ikona else "-"
    display_icon.short_description = 'Ikona'

    def icon_preview(self, obj):
        return format_html('<i class="{} fa-2x"></i>', obj.ikona) if obj.ikona else "Brak ikony"
    icon_preview.short_description = 'Podgląd ikony'


class AtrakcjaAdmin(admin.ModelAdmin):
    inlines = [LokalizacjaInline]
    list_display = ('nazwa', 'kategoria', 'display_adres', 'map_preview')
    list_filter = ('kategoria',)
    search_fields = ('nazwa', 'opis', 'lokalizacja__miasto', 'lokalizacja__ulica')
    readonly_fields = ('map_preview',)

    def display_adres(self, obj):
        return obj.adres()
    display_adres.short_description = 'Adres'

    def map_preview(self, obj):
        if hasattr(obj, 'lokalizacja') and obj.lokalizacja.szerokosc_geo and obj.lokalizacja.dlugosc_geo:
            return format_html(
                '<iframe width="300" height="200" frameborder="0" style="border:0" '
                'src="https://www.google.com/maps/embed/v1/view?key={}&center={},{}&zoom=15"></iframe>',
                settings.GOOGLE_MAPS_API_KEY,
                obj.lokalizacja.szerokosc_geo,
                obj.lokalizacja.dlugosc_geo
            )
        return "Brak współrzędnych"
    map_preview.short_description = 'Podgląd mapy'


class ZdjecieAtrakcjiAdmin(admin.ModelAdmin):
    list_display = ('atrakcja', 'is_glowne', 'opis')
    search_fields = ('atrakcja__nazwa',)


class StatusAtrakcjiAdmin(admin.ModelAdmin):
    list_display = ('atrakcja', 'status', 'data_zmiany')
    list_filter = ('status',)


class GodzinyOtwarciaAdmin(admin.ModelAdmin):
    list_display = ('atrakcja', 'dzien_tygodnia', 'godzina_otwarcia', 'godzina_zamkniecia', 'czy_otwarte')
    list_filter = ('czy_otwarte',)


class RodzajBiletuAdmin(admin.ModelAdmin):
    list_display = ('nazwa',)


class CennikAdmin(admin.ModelAdmin):
    list_display = ('atrakcja', 'rodzaj_biletu', 'cena', 'waluta', 'ważny_od', 'ważny_do')
    list_filter = ('waluta',)


admin.site.register(Kategoria, KategoriaAdmin)
admin.site.register(Atrakcja, AtrakcjaAdmin)
admin.site.register(ZdjecieAtrakcji, ZdjecieAtrakcjiAdmin)
admin.site.register(StatusAtrakcji, StatusAtrakcjiAdmin)
admin.site.register(GodzinyOtwarcia, GodzinyOtwarciaAdmin)
admin.site.register(RodzajBiletu, RodzajBiletuAdmin)
admin.site.register(Cennik, CennikAdmin)
