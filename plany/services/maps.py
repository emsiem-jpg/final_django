import logging
import base64
import requests
from django.conf import settings
import googlemaps

logger = logging.getLogger(__name__)


def geocode_address(address, gmaps):
    """
    Converts a textual address into geographical coordinates (latitude and longitude)
    using the Google Maps Geocoding API.

    Args:
        address (str): The address to geocode.
        gmaps (googlemaps.Client): Authenticated Google Maps client.

    Returns:
        tuple: (latitude, longitude) if successful, otherwise (None, None).
    """
    try:
        result = gmaps.geocode(address)
        if result:
            loc = result[0]['geometry']['location']
            logger.info(f"Zgeokodowano adres '{address}' → ({loc['lat']}, {loc['lng']})")
            return loc['lat'], loc['lng']
        else:
            logger.warning(f"Brak wyników geokodowania dla adresu: {address}")
    except Exception as e:
        logger.warning(f"Geocoding error: {e}", exc_info=True)
    return None, None


def build_etap_points(etap, gmaps):
    """
    Builds a list of geographical points for a given etap, including the starting address
    and all attractions.

    Args:
        etap (Etap): The etap object containing the route and elements.
        gmaps (googlemaps.Client): Authenticated Google Maps client.

    Returns:
        list: List of dictionaries with keys 'label', 'lat', and 'lng'.
    """
    punkty = []

    if etap.adres_startowy:
        lat, lng = geocode_address(etap.adres_startowy, gmaps)
        if lat and lng:
            punkty.append({"label": "S", "lat": lat, "lng": lng})

    for el in etap.elementy.all():
        lok = el.atrakcja.lokalizacja
        if lok and lok.szerokosc_geo and lok.dlugosc_geo:
            punkty.append({
                "label": str(el.kolejnosc),
                "lat": lok.szerokosc_geo,
                "lng": lok.dlugosc_geo
            })

    return punkty


def generate_static_map_url(punkty, gmaps, etap_kolejnosc=1, adres_startowy=None):
    """
    Generates a static Google Maps image URL for a route with markers and a polyline.

    Args:
        punkty (list): List of point dictionaries with 'label', 'lat', and 'lng'.
        gmaps (googlemaps.Client): Authenticated Google Maps client.
        etap_kolejnosc (int): Optional order/index of the etap.
        adres_startowy (str): Optional start address for context/logging.

    Returns:
        str or None: Base64-encoded image string (data:image/png;base64,...) or None if failed.
    """
    if len(punkty) < 2:
        logger.warning("Zbyt mało punktów do wygenerowania statycznej mapy")
        return None

    polyline = None
    try:
        latlngs = [f"{p['lat']},{p['lng']}" for p in punkty]
        directions = gmaps.directions(
            origin=latlngs[0],
            destination=latlngs[-1],
            waypoints=latlngs[1:-1] if len(latlngs) > 2 else None,
            mode="driving"
        )
        polyline = directions[0]['overview_polyline']['points']
        logger.debug(f"Pobrano polyline dla etapu {etap_kolejnosc}")
    except Exception as e:
        logger.warning("Failed to get directions: %s", e, exc_info=True)

    url = f"https://maps.googleapis.com/maps/api/staticmap?size=800x300&key={settings.GOOGLE_MAPS_API_KEY}"
    for p in punkty:
        url += f"&markers=color:blue%7Clabel:{p['label']}%7C{p['lat']},{p['lng']}"
    if polyline:
        url += f"&path=enc:{polyline}"

    logger.debug(f"Generowanie mapy statycznej z {len(punkty)} punktami (etap {etap_kolejnosc})")

    try:
        response = requests.get(url)
        if response.status_code == 200:
            encoded = base64.b64encode(response.content).decode('utf-8')
            return f"data:image/png;base64,{encoded}"
        else:
            logger.warning(f"Błąd pobierania mapy statycznej: kod HTTP {response.status_code}")
    except Exception as e:
        logger.warning(f"Failed to download static map: {e}", exc_info=True)
    return None


def build_etap_map(etap, gmaps, _):
    """
    Builds a static map image (base64) for a given etap using its start address and attractions.

    Args:
        etap (Etap): Etap object with address and attractions.
        gmaps (googlemaps.Client): Authenticated Google Maps client.
        _ (unused): Placeholder for compatibility.

    Returns:
        str or None: Base64-encoded map image or None if not enough data.
    """
    punkty = build_etap_points(etap, gmaps)
    return generate_static_map_url(punkty, gmaps, etap.kolejnosc, etap.adres_startowy)


def build_etap_data(plan, etap, gmaps):
    """
    Builds routing information and estimated total driving time for an etap.

    Args:
        plan (Plan): The plan to which the etap belongs.
        etap (Etap): The etap to process.
        gmaps (googlemaps.Client): Authenticated Google Maps client.

    Returns:
        tuple: (list of points, descriptive summary string)
    """
    punkty = build_etap_points(etap, gmaps)

    if len(punkty) < 2:
        logger.warning(f"Etap {etap.id} zawiera za mało punktów do wyznaczenia trasy")
        return punkty, "Brak wystarczającej liczby punktów."

    try:
        latlngs = [f"{p['lat']},{p['lng']}" for p in punkty]
        directions = gmaps.directions(
            origin=latlngs[0],
            destination=latlngs[-1],
            waypoints=latlngs[1:-1] if len(latlngs) > 2 else None,
            optimize_waypoints=True,
            mode="driving"
        )
        total_minutes = sum(leg['duration']['value'] for leg in directions[0]['legs']) // 60
        logger.info(f"Zbudowano dane etapu {etap.id}: {len(punkty)} punktów, szacowany czas: {total_minutes} min")
        return punkty, f"Szacowany łączny czas przejazdu: {total_minutes} minut"
    except Exception as e:
        logger.warning(f"Nie udało się pobrać trasy dla etapu {etap.id}: {e}", exc_info=True)
        return punkty, "Brak danych o trasie."


def calculate_route_order(gmaps, punkty):
    """
    Optimizes the order of visiting points and calculates total travel duration.

    Args:
        gmaps (googlemaps.Client): Authenticated Google Maps client.
        punkty (list): List of points with 'lat' and 'lng' values.

    Returns:
        tuple: (reordered list of points, total duration in seconds)
    """
    latlngs = [f"{p['lat']},{p['lng']}" for p in punkty]
    origin = latlngs[0]
    destination = latlngs[-1] if len(latlngs) > 1 else latlngs[0]
    waypoints = latlngs[1:-1] if len(latlngs) > 2 else None

    try:
        if waypoints:
            directions = gmaps.directions(
                origin=origin,
                destination=destination,
                waypoints=waypoints,
                optimize_waypoints=True,
                mode="driving"
            )
            order = directions[0].get('waypoint_order', list(range(len(waypoints))))
            uporzadkowane = [punkty[0]] + [punkty[i + 1] for i in order] + [punkty[-1]]
        else:
            directions = gmaps.directions(
                origin=origin,
                destination=destination,
                mode="driving"
            )
            uporzadkowane = punkty

        duration = sum(leg['duration']['value'] for leg in directions[0]['legs'])
        logger.info(f"Obliczono zoptymalizowaną trasę: {len(uporzadkowane)} punktów, {duration // 60} minut")
        return uporzadkowane, duration
    except Exception as e:
        logger.error(f"Błąd optymalizacji trasy: {e}", exc_info=True)
        return punkty, 0


def generate_map_and_update_travel_times(plan):
    """
    Generates a static route map for all attractions in a plan and updates travel times
    between attractions.

    Args:
        plan (Plan): The sightseeing plan to update.

    Returns:
        tuple: (map_url: str, directions: list) or (None, []) on failure.
    """
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    punkty = []
    elementy = []

    for etap in plan.etapy.all().order_by('kolejnosc'):
        for el in etap.elementy.all().order_by('kolejnosc'):
            lok = el.atrakcja.lokalizacja
            if lok and lok.szerokosc_geo and lok.dlugosc_geo:
                punkty.append((lok.szerokosc_geo, lok.dlugosc_geo))
                elementy.append(el)

    logger.debug(f"Zebrano {len(punkty)} punktów z planu ID {plan.id}")

    if len(punkty) < 2:
        logger.warning(f"Za mało punktów do wygenerowania trasy dla planu ID {plan.id}")
        return None, []

    try:
        directions = gmaps.directions(
            origin=punkty[0],
            destination=punkty[-1],
            waypoints=punkty[1:-1] if len(punkty) > 2 else None,
            mode="driving"
        )

        if directions and "legs" in directions[0]:
            legs = directions[0]["legs"]
            for i, leg in enumerate(legs):
                if i + 1 < len(elementy):
                    czas_sec = leg.get("duration", {}).get("value", 0)
                    elementy[i + 1].czas_dojazdu = round(czas_sec / 60)
                    elementy[i + 1].save(update_fields=["czas_dojazdu"])
            logger.info(f"Aktualizacja czasu dojazdu: {len(elementy)} elementów przetworzonych w planie {plan.id}")
    except Exception as e:
        logger.error(f"Błąd przy pobieraniu trasy w planie {plan.id}: {e}", exc_info=True)
        return None, []

    map_url = f"https://maps.googleapis.com/maps/api/staticmap?size=800x400&key={settings.GOOGLE_MAPS_API_KEY}"
    for lat, lng in punkty:
        map_url += f"&markers={lat},{lng}"

    return map_url, directions
