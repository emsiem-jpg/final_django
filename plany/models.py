import logging
from django.db import models

logger = logging.getLogger(__name__)


class PlanZwiedzania(models.Model):
    """
    Represents a sightseeing plan created by a user.
    """
    class StatusPlanu(models.TextChoices):
        SZKIC = 'S', 'Szkic'          # Draft
        AKTYWNY = 'A', 'Aktywny'      # Active
        ZAKONCZONY = 'Z', 'Zakończony' # Completed
        ZARCHIWIZOWANY = 'X', 'Zarchiwizowany'  # Archived

    nazwa = models.CharField(max_length=100)
    opis = models.TextField(blank=True)
    adres_startowy = models.CharField(max_length=255, blank=True, null=True)
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    data_modyfikacji = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=1, choices=StatusPlanu.choices, default=StatusPlanu.SZKIC)
    is_public = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Plan zwiedzania"
        verbose_name_plural = "Plany zwiedzania"
        ordering = ['-data_utworzenia']

    def __str__(self):
        result = self.nazwa
        logger.debug(f"__str__ PlanZwiedzania: {result}")
        return result


class PlanUzytkownika(models.Model):
    """
    Connects a user with a sightseeing plan and defines ownership.
    """
    uzytkownik = models.ForeignKey('konta.User', on_delete=models.CASCADE)
    plan = models.ForeignKey(PlanZwiedzania, on_delete=models.CASCADE)
    jest_wlascicielem = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Plan użytkownika"
        verbose_name_plural = "Plany użytkowników"
        unique_together = ('uzytkownik', 'plan')

    def __str__(self):
        result = f"{self.uzytkownik.username} - {self.plan.nazwa}"
        logger.debug(f"__str__ PlanUzytkownika: {result}")
        return result


class EtapPlanu(models.Model):
    """
    Represents a single stage within a sightseeing plan.
    """
    plan = models.ForeignKey(PlanZwiedzania, on_delete=models.CASCADE, related_name='etapy')
    nazwa = models.CharField(max_length=100)
    kolejnosc = models.PositiveIntegerField()
    opis = models.TextField(blank=True)
    adres_startowy = models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        verbose_name = "Etap planu"
        verbose_name_plural = "Etapy planu"
        ordering = ['kolejnosc']
        unique_together = ('plan', 'kolejnosc')

    def __str__(self):
        result = f"{self.plan.nazwa} - {self.nazwa}"
        logger.debug(f"__str__ EtapPlanu: {result}")
        return result


class ElementEtapu(models.Model):
    """
    Represents a single attraction scheduled in a stage of a sightseeing plan.
    """
    etap = models.ForeignKey(EtapPlanu, on_delete=models.CASCADE, related_name='elementy')
    atrakcja = models.ForeignKey('atrakcje.Atrakcja', on_delete=models.CASCADE)
    kolejnosc = models.PositiveIntegerField()
    planowana_data = models.DateTimeField()
    czas_wizyty = models.PositiveIntegerField(help_text="Czas w minutach")
    czas_dojazdu = models.PositiveIntegerField(help_text="Czas w minutach", null=True, blank=True)

    class Meta:
        verbose_name = "Element etapu"
        verbose_name_plural = "Elementy etapu"
        ordering = ['kolejnosc']
        unique_together = ('etap', 'kolejnosc')

    def __str__(self):
        result = f"{self.etap.nazwa} - {self.atrakcja.nazwa}"
        logger.debug(f"__str__ ElementEtapu: {result}")
        return result


class PlanPodglad(models.Model):
    """
    Read-only view representing a flattened preview of plans, stages, and attractions.
    """
    plan_id = models.IntegerField(primary_key=True)
    plan_nazwa = models.CharField(max_length=255)
    etap_nr = models.IntegerField()
    etap_nazwa = models.CharField(max_length=255)
    atr_nr = models.IntegerField()
    atrakcja_nazwa = models.CharField(max_length=255)
    planowana_data = models.DateTimeField()
    czas_wizyty = models.IntegerField()
    czas_dojazdu = models.IntegerField()

    class Meta:
        managed = False  
        db_table = 'v_plan_podglad'

    def __str__(self):
        result = f"{self.plan_nazwa} / {self.etap_nazwa} / {self.atrakcja_nazwa}"
        logger.debug(f"__str__ PlanPodglad: {result}")
        return result
