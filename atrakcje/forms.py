import logging
from django import forms
from .models import Atrakcja, Lokalizacja

logger = logging.getLogger(__name__)


class AtrakcjaForm(forms.ModelForm):
    """
    Form for creating or editing an attraction.

    Fields:
        - nazwa: Name of the attraction
        - kategoria: Category of the attraction
        - opis: Description of the attraction
        - czas_zwiedzania: Estimated visit time (in minutes)
        - minimalny_wiek: Minimum age requirement (optional)
    """
    class Meta:
        model = Atrakcja
        fields = ['nazwa', 'kategoria', 'opis', 'czas_zwiedzania', 'minimalny_wiek']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug("Zainicjalizowano formularz AtrakcjaForm")

    def save(self, commit=True):
        instance = super().save(commit)
        logger.info(f"Zapisano atrakcję: {instance.nazwa} (ID: {instance.id})")
        return instance


class LokalizacjaForm(forms.ModelForm):
    """
    Form for entering the physical location of an attraction.

    Fields:
        - miasto: City
        - ulica: Street name
        - numer_budynku: Building number
        - kod_pocztowy: Postal code
    """
    class Meta:
        model = Lokalizacja
        fields = ['miasto', 'ulica', 'numer_budynku', 'kod_pocztowy']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug("Zainicjalizowano formularz LokalizacjaForm")

    def save(self, commit=True):
        instance = super().save(commit)
        logger.info(f"Zapisano lokalizację: {instance.pelny_adres()} (ID: {instance.id})")
        return instance
