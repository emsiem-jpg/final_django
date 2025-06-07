from django.db import models

class PlanZwiedzania(models.Model):
    class StatusPlanu(models.TextChoices):
        SZKIC = 'S', 'Szkic'
        AKTYWNY = 'A', 'Aktywny'
        ZAKONCZONY = 'Z', 'Zakończony'
        ZARCHIWIZOWANY = 'X', 'Zarchiwizowany'

    nazwa = models.CharField(max_length=100)
    opis = models.TextField(blank=True)
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    data_modyfikacji = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=1, choices=StatusPlanu.choices, default=StatusPlanu.SZKIC)
    is_public = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Plan zwiedzania"
        verbose_name_plural = "Plany zwiedzania"
        ordering = ['-data_utworzenia']

    def __str__(self):
        return self.nazwa

class PlanUzytkownika(models.Model):
    uzytkownik = models.ForeignKey('konta.User', on_delete=models.CASCADE)
    plan = models.ForeignKey(PlanZwiedzania, on_delete=models.CASCADE)
    jest_wlascicielem = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Plan użytkownika"
        verbose_name_plural = "Plany użytkowników"
        unique_together = ('uzytkownik', 'plan')

    def __str__(self):
        return f"{self.uzytkownik.username} - {self.plan.nazwa}"

class EtapPlanu(models.Model):
    plan = models.ForeignKey(PlanZwiedzania, on_delete=models.CASCADE, related_name='etapy')
    nazwa = models.CharField(max_length=100)
    kolejnosc = models.PositiveIntegerField()
    opis = models.TextField(blank=True)

    class Meta:
        verbose_name = "Etap planu"
        verbose_name_plural = "Etapy planu"
        ordering = ['kolejnosc']
        unique_together = ('plan', 'kolejnosc')

    def __str__(self):
        return f"{self.plan.nazwa} - {self.nazwa}"

class ElementEtapu(models.Model):
    etap = models.ForeignKey(EtapPlanu, on_delete=models.CASCADE, related_name='elementy')
    atrakcja = models.ForeignKey('atrakcje.Atrakcja', on_delete=models.CASCADE)
    kolejnosc = models.PositiveIntegerField()
    planowana_data = models.DateTimeField()
    czas_wizyty = models.PositiveIntegerField(help_text="Czas w minutach")
    czas_dojazdu = models.PositiveIntegerField(help_text="Czas w minutach", null=True, blank=True)
    uwagi = models.TextField(blank=True)

    class Meta:
        verbose_name = "Element etapu"
        verbose_name_plural = "Elementy etapu"
        ordering = ['kolejnosc']
        unique_together = ('etap', 'kolejnosc')

    def __str__(self):
        return f"{self.etap.nazwa} - {self.atrakcja.nazwa}"
    
class PlanPodglad(models.Model):
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
        managed = False  # Django nie będzie próbował modyfikować tego widoku
        db_table = 'v_plan_podglad'