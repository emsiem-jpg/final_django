from datetime import timedelta
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from atrakcje.models import Atrakcja
from plany.models import PlanZwiedzania, PlanUzytkownika, EtapPlanu, ElementEtapu
import logging

logger = logging.getLogger(__name__)


class PlanBuilder:
    """
    Service class responsible for building a sightseeing plan from a user's cart
    and assigned attractions.

    Attributes:
        user (User): The user creating the plan.
        koszyk_ids (list): IDs of attractions in the user's cart.
        nazwa (str): Name of the plan.
        adres_startowy (str): Optional fallback starting address.
        przypisane_atrakcje (dict): Mapping of day -> list of attraction IDs.
        gmaps (googlemaps.Client): Google Maps client for travel time calculation.
        starty (dict): Mapping of day -> custom start address for that day.
        plan (PlanZwiedzania): The created sightseeing plan.
    """

    def __init__(self, user, koszyk_ids, nazwa, adres_startowy, przypisane_atrakcje, gmaps, starty=None):
        self.user = user
        self.koszyk_ids = koszyk_ids
        self.nazwa = nazwa or f"Plan {user.username}"
        self.adres_startowy = adres_startowy or None
        self.przypisane_atrakcje = przypisane_atrakcje
        self.gmaps = gmaps
        self.starty = starty or {}
        self.plan = None

    def build(self):
        logger.info(f"Rozpoczynam budowę planu dla użytkownika {self.user.username}")
        self._create_plan()
        self._assign_user()
        self._create_etapy_and_elements()
        logger.info(f"Zakończono budowę planu (ID: {self.plan.id})")
        return self.plan

    def _create_plan(self):
        # Create the main PlanZwiedzania object
        self.plan = PlanZwiedzania.objects.create(
            nazwa=self.nazwa,
            opis="Utworzono z koszyka",
            adres_startowy=self.adres_startowy
        )
        logger.debug(f"Utworzono plan: '{self.nazwa}' (ID: {self.plan.id})")

    def _assign_user(self):
        # Link the user as the plan's owner
        PlanUzytkownika.objects.create(
            uzytkownik=self.user,
            plan=self.plan,
            jest_wlascicielem=True
        )
        logger.debug(f"Przypisano użytkownika {self.user.username} jako właściciela planu ID {self.plan.id}")

    def _create_etapy_and_elements(self):
        # Start time for first day's schedule
        czas_start = now()

        # Process each day's attractions
        for dzien, atrakcje_ids in sorted(self.przypisane_atrakcje.items()):
            # Determine start address for this day
            adres_etapu = self.starty.get(dzien) or (self.adres_startowy if dzien == 1 else None)

            # Create the EtapPlanu instance
            etap = EtapPlanu.objects.create(
                plan=self.plan,
                nazwa=f"Dzień {dzien}",
                kolejnosc=dzien,
                adres_startowy=adres_etapu
            )
            logger.debug(f"Utworzono etap {etap.nazwa} (ID: {etap.id}) z {len(atrakcje_ids)} atrakcji")

            # Geocode start location
            poprzednia_lokalizacja = self._geocode_address(adres_etapu) if adres_etapu else None

            for kolejnosc, atrakcja_id in enumerate(atrakcje_ids, start=1):
                # Get attraction with location
                atrakcja = get_object_or_404(Atrakcja.objects.select_related('lokalizacja'), id=atrakcja_id)

                # Calculate travel time from previous location
                czas_dojazdu = self._calculate_travel_time(poprzednia_lokalizacja, atrakcja)

                # Add attraction to etap
                ElementEtapu.objects.create(
                    etap=etap,
                    atrakcja=atrakcja,
                    kolejnosc=kolejnosc,
                    planowana_data=czas_start,
                    czas_wizyty=atrakcja.czas_zwiedzania or 30,
                    czas_dojazdu=czas_dojazdu
                )

                logger.debug(
                    f"Dodano atrakcję '{atrakcja.nazwa}' do etapu {etap.kolejnosc} (czas dojazdu: {czas_dojazdu} min)"
                )

                # Update time for next item
                czas_start += timedelta(minutes=(atrakcja.czas_zwiedzania or 30) + czas_dojazdu)
                poprzednia_lokalizacja = atrakcja.lokalizacja

    def _geocode_address(self, address):
        """
        Geocodes a given address and returns an object with lat/lng.

        Returns:
            object | None: Location object with szerokosc_geo and dlugosc_geo
        """
        try:
            geocode_result = self.gmaps.geocode(address)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                logger.debug(f"Zgeokodowano adres: {address}")
                return type('Loc', (), {
                    'szerokosc_geo': location['lat'],
                    'dlugosc_geo': location['lng']
                })()
            else:
                logger.warning(f"Brak wyników geokodowania dla adresu: {address}")
        except Exception as e:
            logger.warning("Nie udało się zgeokodować adresu: %s", e, exc_info=True)
        return None

    def _calculate_travel_time(self, previous, current):
        """
        Calculates driving time between two locations using Google Maps Directions API.

        Returns:
            int: travel time in minutes, or 15 as fallback.
        """
        if not previous:
            return 0
        try:
            directions = self.gmaps.directions(
                origin=(previous.szerokosc_geo, previous.dlugosc_geo),
                destination=(current.lokalizacja.szerokosc_geo, current.lokalizacja.dlugosc_geo),
                mode="driving"
            )
            if directions and directions[0]['legs']:
                time = directions[0]['legs'][0]['duration']['value'] // 60
                logger.debug(f"Czas przejazdu: {time} min do '{current.nazwa}'")
                return time
        except Exception as e:
            logger.warning("Błąd przy pobieraniu trasy: %s", e, exc_info=True)
        return 15
