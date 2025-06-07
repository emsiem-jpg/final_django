from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.utils.timezone import now
from datetime import timedelta
from django.template.loader import render_to_string
from .models import PlanZwiedzania, PlanUzytkownika, EtapPlanu, ElementEtapu, PlanPodglad
from atrakcje.models import Atrakcja
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from collections import defaultdict
import logging
import googlemaps
from django.conf import settings
from weasyprint import HTML
logger = logging.getLogger(__name__)
User = get_user_model()

# ========== MAPA I TRASA ==========
def generuj_mape_i_trase(plan):
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    punkty = []
    elementy = []

    for etap in plan.etapy.all().order_by('kolejnosc'):
        for el in etap.elementy.all().order_by('kolejnosc'):
            lok = el.atrakcja.lokalizacja
            if lok and lok.szerokosc_geo and lok.dlugosc_geo:
                punkty.append((lok.szerokosc_geo, lok.dlugosc_geo))
                elementy.append(el)

    if len(punkty) < 2:
        return None, []

    # Directions API
    directions = gmaps.directions(
        origin=punkty[0],
        destination=punkty[-1],
        waypoints=punkty[1:-1] if len(punkty) > 2 else None,
        mode="driving"
    )

    # Aktualizuj czas_dojazdu na podstawie Directions API
    if directions and "legs" in directions[0]:
        legs = directions[0]["legs"]
        for i, leg in enumerate(legs):
            if i + 1 < len(elementy):
                czas_sec = leg.get("duration", {}).get("value", 0)
                elementy[i + 1].czas_dojazdu = round(czas_sec / 60)  # w minutach
                elementy[i + 1].save(update_fields=["czas_dojazdu"])

    # Mapa statyczna
    map_url = f"https://maps.googleapis.com/maps/api/staticmap?size=800x400&key={settings.GOOGLE_MAPS_API_KEY}"
    for lat, lng in punkty:
        map_url += f"&markers={lat},{lng}"

    return map_url, directions


# ========== WIDOKI ==========

@login_required
def dodaj_do_koszyka(request, atrakcja_id):
    koszyk = request.session.get('koszyk', [])
    if atrakcja_id not in koszyk:
        koszyk.append(atrakcja_id)
        request.session['koszyk'] = koszyk
        logger.info("Dodano atrakcję ID %s do koszyka użytkownika %s", atrakcja_id, request.user.username)
    return redirect('lista_atrakcji')


@login_required
def koszyk(request):
    koszyk_ids = request.session.get('koszyk', [])
    atrakcje = Atrakcja.objects.filter(id__in=koszyk_ids)

    liczba_dni = request.GET.get('dni', 3)
    try:
        liczba_dni = int(liczba_dni)
    except ValueError:
        liczba_dni = 3

    return render(request, 'plany/koszyk.html', {
        'atrakcje': atrakcje,
        'liczba_dni': liczba_dni,
        'dni_range': range(1, liczba_dni + 1)
    })


@login_required
def usun_z_koszyka(request, atrakcja_id):
    koszyk = request.session.get('koszyk', [])
    if atrakcja_id in koszyk:
        koszyk.remove(atrakcja_id)
        request.session['koszyk'] = koszyk
        logger.info("Usunięto atrakcję ID %s z koszyka użytkownika %s", atrakcja_id, request.user.username)
    return redirect('plany:koszyk')

def szczegoly_planu(request, id):
    plan = get_object_or_404(
        PlanZwiedzania.objects.prefetch_related('etapy__elementy__atrakcja__lokalizacja'),
        id=id
    )
    mapa_url, trasa = generuj_mape_i_trase(plan)
    return render(request, 'plany/szczegoly_planu.html', {
        'plan': plan,
        'static_map_url': mapa_url,
        'trasa': trasa,
         'google_maps_key': settings.GOOGLE_MAPS_API_KEY
    })




@login_required
def zapisz_plan(request):
    if request.method == 'POST':
        logger.info("Użytkownik %s rozpoczął zapisywanie planu.", request.user.username)
        nazwa = request.POST.get('nazwa', '').strip()
        liczba_dni = int(request.POST.get('liczba_dni', 1))
        wybrane_ids = request.session.get('koszyk', [])

        if not wybrane_ids:
            messages.error(request, "Twój koszyk jest pusty.")
            return redirect('plany:koszyk')

        if not nazwa:
            nazwa = f"Plan {request.user.username}"

        plan = PlanZwiedzania.objects.create(nazwa=nazwa, opis="Utworzono z koszyka")

        PlanUzytkownika.objects.create(
            uzytkownik=request.user,
            plan=plan,
            jest_wlascicielem=True
        )

        przypisane_atrakcje = defaultdict(list)
        for atrakcja_id in wybrane_ids:
            dzien_str = request.POST.get(f'dzien_{atrakcja_id}')
            try:
                dzien = int(dzien_str)
                przypisane_atrakcje[dzien].append(int(atrakcja_id))
            except (TypeError, ValueError):
                continue

        gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
        czas_start = now()

        for dzien, atrakcje_ids in sorted(przypisane_atrakcje.items()):
            etap = EtapPlanu.objects.create(
                plan=plan,
                nazwa=f"Dzień {dzien}",
                kolejnosc=dzien
            )

            poprzednia_lokalizacja = None

            for kolejnosc, atrakcja_id in enumerate(atrakcje_ids, start=1):
                atrakcja = get_object_or_404(Atrakcja.objects.select_related('lokalizacja'), id=atrakcja_id)
                czas_dojazdu = 0

                if poprzednia_lokalizacja:
                    try:
                        directions = gmaps.directions(
                            origin=(poprzednia_lokalizacja.szerokosc_geo, poprzednia_lokalizacja.dlugosc_geo),
                            destination=(atrakcja.lokalizacja.szerokosc_geo, atrakcja.lokalizacja.dlugosc_geo),
                            mode="driving"
                        )
                        if directions and directions[0]['legs']:
                            czas_dojazdu = directions[0]['legs'][0]['duration']['value'] // 60  # w minutach
                    except Exception as e:
                        logger.warning("Błąd przy pobieraniu trasy: %s", e)
                        czas_dojazdu = 15  # fallback

                ElementEtapu.objects.create(
                    etap=etap,
                    atrakcja=atrakcja,
                    kolejnosc=kolejnosc,
                    planowana_data=czas_start,
                    czas_wizyty=atrakcja.czas_zwiedzania or 30,
                    czas_dojazdu=czas_dojazdu
                )

                czas_start += timedelta(minutes=(atrakcja.czas_zwiedzania or 30) + czas_dojazdu)
                poprzednia_lokalizacja = atrakcja.lokalizacja

        request.session['koszyk'] = []
        logger.info("Utworzono plan %s (ID: %s)", plan.nazwa, plan.id)
        return redirect('plany:szczegoly_planu', plan.id)




import requests
import base64

@login_required
def export_plan_pdf(request, id):
    plan = get_object_or_404(
        PlanZwiedzania.objects.prefetch_related('etapy__elementy__atrakcja__lokalizacja'),
        id=id
    )

    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

    mapy_etapow = {}
    for etap in plan.etapy.all():
        punkty = []
        for el in etap.elementy.all():
            lok = el.atrakcja.lokalizacja
            if lok and lok.szerokosc_geo and lok.dlugosc_geo:
                punkty.append((lok.szerokosc_geo, lok.dlugosc_geo))

        if len(punkty) >= 2:
            # Pobierz trasę od Google Directions API
            try:
                directions = gmaps.directions(
                    origin=punkty[0],
                    destination=punkty[-1],
                    waypoints=punkty[1:-1] if len(punkty) > 2 else None,
                    mode="driving"
                )
                polyline = directions[0]['overview_polyline']['points']
            except Exception as e:
                logger.warning(f"[MAPA] Nie udało się pobrać trasy dla etapu {etap.id}: {e}")
                polyline = None
        else:
            polyline = None

        if len(punkty) >= 1:
            url = f"https://maps.googleapis.com/maps/api/staticmap?size=800x300&key={settings.GOOGLE_MAPS_API_KEY}"

            for lat, lng in punkty:
                url += f"&markers={lat},{lng}"

            if polyline:
                url += f"&path=enc:{polyline}"

            try:
                response = requests.get(url)
                if response.status_code == 200:
                    encoded = base64.b64encode(response.content).decode('utf-8')
                    data_url = f"data:image/png;base64,{encoded}"
                    mapy_etapow[etap.id] = data_url
                else:
                    logger.warning(f"Nie udało się pobrać mapy dla etapu {etap.id}: {response.status_code}")
            except Exception as e:
                logger.exception(f"Błąd pobierania mapy dla etapu {etap.id}: {e}")

    html_string = render_to_string('plany/plan_pdf.html', {
        'plan': plan,
        'mapy_etapow': mapy_etapow,
    })

    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="plan_{plan.id}.pdf"'
    return response



@login_required
def usun_plan(request, id):
    plan = get_object_or_404(PlanZwiedzania, id=id)
    relacja = get_object_or_404(PlanUzytkownika, plan=plan, uzytkownik=request.user)

    if not relacja.jest_wlascicielem:
        logger.warning("Nieautoryzowana próba usunięcia planu ID: %s przez %s", plan.id, request.user.username)
        return HttpResponseForbidden("Nie masz uprawnień do usunięcia tego planu.")

    if request.method == "POST":
        logger.info("Użytkownik %s usunął plan: %s (ID: %s)", request.user.username, plan.nazwa, plan.id)
        plan.delete()
        messages.success(request, "Plan został usunięty.")
        return HttpResponseRedirect(reverse('profile'))

    return render(request, 'plany/potwierdz_usuniecie.html', {'plan': plan})


def is_moderator_or_admin(user):
    return user.is_authenticated and user.role in ['moderator', 'admin']


@user_passes_test(is_moderator_or_admin)
@login_required
def podglad_planu(request):
    podglad = PlanPodglad.objects.all().order_by('plan_id', 'etap_nr', 'atr_nr')
    return render(request, 'plany/podglad.html', {'podglad': podglad})
