from django import forms
from .models import Atrakcja, Lokalizacja

class AtrakcjaForm(forms.ModelForm):
    class Meta:
        model = Atrakcja
        fields = ['nazwa', 'kategoria', 'opis', 'czas_zwiedzania', 'minimalny_wiek']

class LokalizacjaForm(forms.ModelForm):
    class Meta:
        model = Lokalizacja
        fields = ['miasto', 'ulica', 'numer_budynku', 'kod_pocztowy']
