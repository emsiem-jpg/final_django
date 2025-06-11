from django.db import models
from django.utils.timezone import now
from django.utils.html import format_html
import googlemaps
from django.conf import settings
from datetime import date
import logging

logger = logging.getLogger(__name__)

class Kategoria(models.Model):
    """Represents a category of attractions (e.g., museums, parks)."""
    nazwa = models.CharField(max_length=100, unique=True)
    ikona = models.CharField(max_length=30, blank=True)
    opis = models.TextField(blank=True)

    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"

    def __str__(self):
        return self.nazwa

    def ikona_html(self):
        return format_html(f'<i class="fas {self.ikona}"></i>')


class Atrakcja(models.Model):
    """Represents a tourist attraction with its category, description and optional visit time."""
    nazwa = models.CharField(max_length=200, unique=True)
    kategoria = models.ForeignKey(Kategoria, on_delete=models.PROTECT)
    opis = models.TextField()
    minimalny_wiek = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    czas_zwiedzania = models.PositiveIntegerField(
    null=True,
    blank=True,
    help_text="Szacowany czas zwiedzania (w minutach)"
)
    @property
    def statystyki_cen(self):
        """Returns related pricing statistics if available."""
        try:
            return CennikStatystykiMV.objects.get(pk=self.pk)
        except CennikStatystykiMV.DoesNotExist:
             logger.info(f"Brak statystyk cenowych dla atrakcji: {self.pk} - {self.nazwa}")
             return None
        except Exception as e:
            logger.error(f"Błąd przy pobieraniu statystyk cenowych dla atrakcji {self.pk} - {self.nazwa}: {e}", exc_info=True)
            return None
            


    def adres(self):
        """Returns the full address of the attraction if location exists."""
        return self.lokalizacja.pelny_adres() if hasattr(self, 'lokalizacja') else "Brak lokalizacji"
    adres.short_description = "Adres"

    def aktualna_cena(self):
        """Returns the latest price entry for the attraction."""
        today = date.today()
        aktualne = self.ceny.filter(ważny_od__lte=today).order_by('-ważny_od')
        if aktualne.exists():
            cena = aktualne.first()
            return f"{cena.cena} {cena.waluta}"
        return None
    class Meta:
        verbose_name = "Atrakcja"
        verbose_name_plural = "Atrakcje"

    def __str__(self):
        return self.nazwa


class Lokalizacja(models.Model):
    """Represents the physical address of an attraction and stores geolocation coordinates."""
    atrakcja = models.OneToOneField(Atrakcja, on_delete=models.CASCADE, related_name='lokalizacja', null=True, blank=True)
    miasto = models.CharField(max_length=50)
    ulica = models.CharField(max_length=100)
    numer_budynku = models.CharField(max_length=10)
    kod_pocztowy = models.CharField(max_length=10)
    szerokosc_geo = models.FloatField(null=True, blank=True)
    dlugosc_geo = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Lokalizacja"
        verbose_name_plural = "Lokalizacje"
        unique_together = ('miasto', 'ulica', 'numer_budynku')
        db_table = "Lokalizacja"

    def __str__(self):
        return f"{self.ulica} {self.numer_budynku}, {self.miasto}"

    def pelny_adres(self):
        """Returns the formatted full address."""
        return f"{self.ulica} {self.numer_budynku}, {self.kod_pocztowy} {self.miasto}"

    def save(self, *args, **kwargs):
        """Automatically geocodes address if coordinates are missing."""
        if (not self.szerokosc_geo or not self.dlugosc_geo) and self.miasto and self.ulica and self.numer_budynku and self.kod_pocztowy:
            gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
            adres = f"{self.ulica} {self.numer_budynku}, {self.kod_pocztowy} {self.miasto}"
            try:
                rezultat = gmaps.geocode(adres)
                if rezultat:
                    location = rezultat[0]['geometry']['location']
                    self.szerokosc_geo = location['lat']
                    self.dlugosc_geo = location['lng']
                    logger.info(f"Zgeokodowano lokalizację '{adres}' → ({self.szerokosc_geo}, {self.dlugosc_geo})")
                else:
                    logger.warning(f"Brak wyników geokodowania dla adresu: {adres}")
            except Exception as e:
                logger.error(f"Błąd geokodowania adresu: {adres} - {e}", exc_info=True)
        super().save(*args, **kwargs)

class StatusAtrakcji(models.Model):
    """Tracks status changes of an attraction (e.g., available, under renovation)."""
    class Status(models.TextChoices):
        DOSTEPNA = 'D', 'Dostępna'
        NIEDOSTEPNA = 'N', 'Niedostępna'
        REMONT = 'R', 'W remoncie'
        ZAMKNIETA = 'Z', 'Zamknięta'

    atrakcja = models.ForeignKey(Atrakcja, on_delete=models.CASCADE, related_name='statusy')
    status = models.CharField(max_length=1, choices=Status.choices)
    data_zmiany = models.DateTimeField(auto_now_add=True)
    komentarz = models.TextField(blank=True)

    class Meta:
        verbose_name = "Status atrakcji"
        verbose_name_plural = "Statusy atrakcji"
        ordering = ['-data_zmiany']

    def __str__(self):
        return f"{self.atrakcja.nazwa} - {self.get_status_display()}"


class ZdjecieAtrakcji(models.Model):
    """Stores photos related to an attraction, with optional main image flag."""
    atrakcja = models.ForeignKey(Atrakcja, on_delete=models.CASCADE, related_name='zdjecia')
    zdjecie = models.ImageField(upload_to='atrakcje/')
    is_glowne = models.BooleanField(default=False)
    opis = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Zdjęcie atrakcji"
        verbose_name_plural = "Zdjęcia atrakcji"

    def __str__(self):
        return f"Zdjęcie {self.atrakcja.nazwa}"


class GodzinyOtwarcia(models.Model):
    """Defines weekly opening hours for each attraction."""
    class DzienTygodnia(models.TextChoices):
        PONIEDZIALEK = '1', 'Poniedziałek'
        WTOREK = '2', 'Wtorek'
        SRODA = '3', 'Środa'
        CZWARTEK = '4', 'Czwartek'
        PIATEK = '5', 'Piątek'
        SOBOTA = '6', 'Sobota'
        NIEDZIELA = '7', 'Niedziela'
    atrakcja = models.ForeignKey(Atrakcja, on_delete=models.CASCADE, related_name='godziny_otwarcia')
    dzien_tygodnia = models.CharField(max_length=1, choices=DzienTygodnia.choices)
    godzina_otwarcia = models.TimeField()
    godzina_zamkniecia = models.TimeField()
    czy_otwarte = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Godziny otwarcia"
        verbose_name_plural = "Godziny otwarcia"
        unique_together = ('atrakcja', 'dzien_tygodnia')

    def __str__(self):
        return f"{self.atrakcja.nazwa} - {self.get_dzien_tygodnia_display()}"


class RodzajBiletu(models.Model):
    """Describes different types of tickets available for attractions."""
    nazwa = models.CharField(max_length=50)
    opis = models.TextField(blank=True)

    class Meta:
        verbose_name = "Rodzaj biletu"
        verbose_name_plural = "Rodzaje biletów"

    def __str__(self):
        return self.nazwa


class Cennik(models.Model):
    """Stores ticket prices for an attraction, including validity periods."""
    atrakcja = models.ForeignKey(Atrakcja, on_delete=models.CASCADE, related_name='ceny')
    rodzaj_biletu = models.ForeignKey(RodzajBiletu, on_delete=models.PROTECT)
    cena = models.DecimalField(max_digits=8, decimal_places=2)
    waluta = models.CharField(max_length=3, default='PLN')
    ważny_od = models.DateField()
    ważny_do = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Cennik"
        verbose_name_plural = "Cenniki"
        ordering = ['-ważny_od']

    def __str__(self):
        return f"{self.atrakcja.nazwa} - {self.rodzaj_biletu} ({self.cena} {self.waluta})"

class CennikStatystykiMV(models.Model):
    """Represents aggregated pricing statistics from a materialized view."""
    atrakcja = models.OneToOneField('Atrakcja', on_delete=models.DO_NOTHING, db_column='atrakcja_id', primary_key=True)
    min_cena = models.DecimalField(max_digits=8, decimal_places=2)
    max_cena = models.DecimalField(max_digits=8, decimal_places=2)
    avg_cena = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        managed = False  # to jest widok, nie tabela
        db_table = 'mv_cennik_statystyki'

