from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.timezone import now
from django.utils.html import format_html
import googlemaps
from django.conf import settings
from datetime import date

class Kategoria(models.Model):
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
    
        try:
            return CennikStatystyki.objects.get(pk=self.pk)
        except CennikStatystyki.DoesNotExist:
            return None


    def adres(self):
        return self.lokalizacja.pelny_adres() if hasattr(self, 'lokalizacja') else "Brak lokalizacji"
    adres.short_description = "Adres"

    def aktualna_cena(self):
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
        return f"{self.ulica} {self.numer_budynku}, {self.kod_pocztowy} {self.miasto}"

    def save(self, *args, **kwargs):
        # Jeśli współrzędne są puste, próbujemy je pobrać z Google Maps
        if (not self.szerokosc_geo or not self.dlugosc_geo) and self.miasto and self.ulica and self.numer_budynku and self.kod_pocztowy:
            gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
            adres = f"{self.ulica} {self.numer_budynku}, {self.kod_pocztowy} {self.miasto}"
            try:
                rezultat = gmaps.geocode(adres)
                if rezultat:
                    location = rezultat[0]['geometry']['location']
                    self.szerokosc_geo = location['lat']
                    self.dlugosc_geo = location['lng']
            except Exception as e:
                # W razie błędu geokodowania nic nie robimy (możesz zalogować wyjątek)
                pass
        super().save(*args, **kwargs)

class StatusAtrakcji(models.Model):
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
    class DzienTygodnia(models.TextChoices):
        PONIEDZIALEK = '1', 'Poniedziałek'
        WTOREK = '2', 'Wtorek'
        # ... pozostałe dni

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
    nazwa = models.CharField(max_length=50)
    opis = models.TextField(blank=True)

    class Meta:
        verbose_name = "Rodzaj biletu"
        verbose_name_plural = "Rodzaje biletów"

    def __str__(self):
        return self.nazwa


class Cennik(models.Model):
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

class CennikStatystyki(models.Model):
    atrakcja = models.OneToOneField('Atrakcja', on_delete=models.DO_NOTHING, db_column='atrakcja_id', primary_key=True)
    min_cena = models.DecimalField(max_digits=8, decimal_places=2)
    max_cena = models.DecimalField(max_digits=8, decimal_places=2)
    avg_cena = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        managed = False  # to jest widok, nie tabela
        db_table = 'v_cennik_statystyki'