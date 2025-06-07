# Skrypt generujacy dane zgodnie z przeslanymi modelami
from django.core.management.base import BaseCommand
from faker import Faker
from django.contrib.auth.hashers import make_password
import random
from datetime import datetime, timedelta, date

from atrakcje.models import (
    Kategoria, Atrakcja, Lokalizacja, StatusAtrakcji,
    ZdjecieAtrakcji, GodzinyOtwarcia, RodzajBiletu, Cennik
)
from konta.models import User
from plany.models import (
    PlanZwiedzania, PlanUzytkownika,
    EtapPlanu, ElementEtapu
)

fake = Faker('pl_PL')

class Command(BaseCommand):
    help = 'Generuje dane testowe dla przewodnika miejskiego'

    def handle(self, *args, **options):
        self.stdout.write("Rozpoczynam czyszczenie i generowanie danych...")
        self._clear_data()

        users = self._create_users(300)
        categories = self._create_categories()
        attractions = self._create_attractions(categories, 500)
        self._create_attraction_details(attractions)
        self._create_ticket_and_opening_data(attractions)
        self._create_tour_plans(users, attractions, 200)

        self.stdout.write(self.style.SUCCESS("Dane zostały pomyślnie wygenerowane!"))

    def _clear_data(self):
        ElementEtapu.objects.all().delete()
        EtapPlanu.objects.all().delete()
        PlanUzytkownika.objects.all().delete()
        PlanZwiedzania.objects.all().delete()
        Cennik.objects.all().delete()
        RodzajBiletu.objects.all().delete()
        GodzinyOtwarcia.objects.all().delete()
        ZdjecieAtrakcji.objects.all().delete()
        StatusAtrakcji.objects.all().delete()
        Lokalizacja.objects.all().delete()
        Atrakcja.objects.all().delete()
        Kategoria.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

    def _create_users(self, count):
        roles = ['tourist', 'guide', 'moderator', 'admin']
        users = []
        while len(users) < count:
            username = fake.unique.user_name()
            if not User.objects.filter(username=username).exists():
                user = User.objects.create(
                    username=username,
                    email=fake.unique.email(),
                    role=random.choice(roles),
                    password=make_password('test123'),
                    first_name=fake.first_name(),
                    last_name=fake.last_name()
                )
                users.append(user)
        return users

    def _create_categories(self):
        data = [
            {'nazwa': 'Muzeum', 'ikona': 'fa-museum'},
            {'nazwa': 'Park', 'ikona': 'fa-tree'},
            {'nazwa': 'Zabytek', 'ikona': 'fa-landmark'},
            {'nazwa': 'Restauracja', 'ikona': 'fa-utensils'},
        ]
        return [Kategoria.objects.create(**item) for item in data]

    def _create_attractions(self, categories, count):
        ulice = ['Floriańska', 'Grodzka', 'Szewska', 'Długa']
        miasta = ['Kraków', 'Warszawa', 'Wrocław']
        atrakcje = []
        for _ in range(count):
            atrakcja = Atrakcja.objects.create(
                nazwa=fake.unique.company(),
                kategoria=random.choice(categories),
                opis=fake.text(max_nb_chars=500),
                minimalny_wiek=random.choice([None, 3, 6, 12, 18]),
                czas_zwiedzania=random.randint(30, 120)
            )
            
            while True:
                miasto = random.choice(miasta)
                ulica = random.choice(ulice)
                numer = str(random.randint(1, 100))

                if not Lokalizacja.objects.filter(miasto=miasto, ulica=ulica, numer_budynku=numer).exists():
                    break

            Lokalizacja.objects.create(
                atrakcja=atrakcja,
                miasto=miasto,
                ulica=ulica,
                numer_budynku=numer,
                kod_pocztowy=fake.postcode(),
                szerokosc_geo=float(fake.latitude()),
                dlugosc_geo=float(fake.longitude())
            )

            
            atrakcje.append(atrakcja)
        return atrakcje

    def _create_attraction_details(self, attractions):
        for a in attractions:
            StatusAtrakcji.objects.create(
                atrakcja=a,
                status=random.choice(['D', 'N', 'R', 'Z']),
                komentarz=fake.sentence()
            )
            ZdjecieAtrakcji.objects.create(
                atrakcja=a,
                zdjecie='atrakcje/test.jpg',
                is_glowne=True,
                opis=fake.sentence()
            )

    def _create_ticket_and_opening_data(self, attractions):
        dni = ['1', '2', '3', '4', '5', '6', '7']
        rodzaje = ['Normalny', 'Ulgowy', 'Rodzinny']
        for a in attractions:
            for d in dni:
                GodzinyOtwarcia.objects.create(
                    atrakcja=a,
                    dzien_tygodnia=d,
                    godzina_otwarcia=datetime.strptime('08:00', "%H:%M").time(),
                    godzina_zamkniecia=datetime.strptime('18:00', "%H:%M").time(),
                    czy_otwarte=True
                )
            for r in rodzaje:
                rb = RodzajBiletu.objects.create(nazwa=r, opis=fake.sentence())
                Cennik.objects.create(
                    atrakcja=a,
                    rodzaj_biletu=rb,
                    cena=round(random.uniform(10, 50), 2),
                    waluta='PLN',
                    ważny_od=date.today()
                )

    def _create_tour_plans(self, users, attractions, count):
        for _ in range(count):
            plan = PlanZwiedzania.objects.create(
                nazwa=fake.word().capitalize(),
                opis=fake.text(max_nb_chars=200),
                status=random.choice(['S', 'A', 'Z', 'X']),
                is_public=True
            )
            user = random.choice([u for u in users if u.role in ['tourist', 'guide']])
            PlanUzytkownika.objects.create(plan=plan, uzytkownik=user, jest_wlascicielem=True)
            for i in range(random.randint(2, 4)):
                etap = EtapPlanu.objects.create(
                    plan=plan,
                    nazwa=f"Etap {i+1}",
                    kolejnosc=i+1,
                    opis=fake.sentence()
                )
                for j in range(random.randint(2, 5)):
                    ElementEtapu.objects.create(
                        etap=etap,
                        atrakcja=random.choice(attractions),
                        kolejnosc=j+1,
                        planowana_data=fake.date_time_this_year(),
                        czas_wizyty=random.randint(30, 180),
                        czas_dojazdu=random.randint(5, 45),
                        uwagi=fake.sentence()
                    )
