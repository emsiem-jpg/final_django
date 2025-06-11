from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings
import logging
import googlemaps

from .models import PlanZwiedzania, PlanUzytkownika
from atrakcje.models import Atrakcja
from .services.maps import (
    build_etap_data, build_etap_map,
    generate_map_and_update_travel_times
)
from .services.pdf_generator import render_plan_to_pdf
from .services.plan_builder import PlanBuilder

logger = logging.getLogger(__name__)
User = get_user_model()


@login_required
def dodaj_do_koszyka(request, atrakcja_id):
    """
    Adds an attraction to the user's session cart.

    Args:
        request (HttpRequest): The HTTP request.
        atrakcja_id (int): ID of the attraction to be added.

    Returns:
        HttpResponseRedirect: Redirects to the attractions list.
    """
    koszyk = request.session.get('koszyk', [])
    if atrakcja_id not in koszyk:
        koszyk.append(atrakcja_id)
        request.session['koszyk'] = koszyk
        logger.info("Dodano atrakcję ID %s do koszyka użytkownika %s", atrakcja_id, request.user.username)
    return redirect('lista_atrakcji')

@login_required
def koszyk(request):
    """
    Displays the contents of the user's cart and a form for day assignment.

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        HttpResponse: Page with the attractions cart.
    """
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
    """
    Removes an attraction from the user's session cart.

    Args:
        request (HttpRequest): The HTTP request.
        atrakcja_id (int): ID of the attraction to be removed.

    Returns:
        HttpResponseRedirect: Redirects to the cart page.
    """
    koszyk = request.session.get('koszyk', [])
    if atrakcja_id in koszyk:
        koszyk.remove(atrakcja_id)
        request.session['koszyk'] = koszyk
        logger.info("Usunięto atrakcję ID %s z koszyka użytkownika %s", atrakcja_id, request.user.username)
    return redirect('plany:koszyk')

@login_required
def szczegoly_planu(request, id):
    """
    Displays the details of the sightseeing plan with stage maps.

    Args:
        request (HttpRequest): The HTTP request.
        id (int): ID of the plan.

    Returns:
        HttpResponse: Page with plan details.
    """
    plan = get_object_or_404(
        PlanZwiedzania.objects.prefetch_related('etapy__elementy__atrakcja__lokalizacja'),
        id=id
    )
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    etap_info = {}
    mapy_etapow = {}
    for etap in plan.etapy.all():
        punkty, dojazd_info = build_etap_data(plan, etap, gmaps)
        czas_zwiedzania = sum(el.czas_wizyty for el in etap.elementy.all())
        czas_dojazdu = sum(el.czas_dojazdu or 0 for el in etap.elementy.all())

        etap_info[etap.id] = {
            "dojazd_info": dojazd_info,
            "czas_zwiedzania": czas_zwiedzania,
            "czas_dojazdu": czas_dojazdu,
            "czas_laczny": czas_zwiedzania + czas_dojazdu
        }
        mapy_etapow[etap.id] = punkty
    return render(request, 'plany/szczegoly_planu.html', {
        'plan': plan,
        'mapy_etapow': mapy_etapow,
        'etap_info': etap_info,
        'google_maps_key': settings.GOOGLE_MAPS_API_KEY
    })


@login_required
def generuj_mape_i_trase(request, id):
    """
    Generates a route between attractions and updates travel times.

    Args:
        request (HttpRequest): The HTTP request.
        id (int): ID of the plan.

    Returns:
        HttpResponse: Page with map and generated route.
    """
    plan = get_object_or_404(PlanZwiedzania, id=id)
    map_url, directions = generate_map_and_update_travel_times(plan)
    return render(request, 'plany/mapa_i_trasa.html', {'plan': plan, 'map_url': map_url, 'directions': directions})

@login_required
def zapisz_plan(request):
    """
    Saves a new sightseeing plan based on the contents of the cart.

    Args:
        request (HttpRequest): HTTP request with form data.

    Returns:
        HttpResponseRedirect: Redirects to plan details or cart.
    """
    if request.method == 'POST':
        koszyk_ids = request.session.get('koszyk', [])
        if not koszyk_ids:
            messages.warning(request, "Twój koszyk jest pusty.")
            logger.warning("Użytkownik %s próbował zapisać plan bez atrakcji w koszyku", request.user.username)
            return redirect('plany:koszyk')

        przypisane_atrakcje = {}
        for key, value in request.POST.items():
            if key.startswith("dzien_"):
                try:
                    atrakcja_id = int(key.split("_")[1])
                    dzien = int(value)
                    przypisane_atrakcje.setdefault(dzien, []).append(atrakcja_id)
                except ValueError:
                    continue

        
        starty = {}
        for key, value in request.POST.items():
            if key.startswith("start_dzien_"):
                try:
                    dzien = int(key.split("_")[-1])
                    if value.strip():
                        starty[dzien] = value.strip()
                except ValueError:
                    continue

        logger.info("Użytkownik %s zapisuje nowy plan. Przypisane atrakcje: %s", request.user.username, przypisane_atrakcje)
        logger.debug("Adresy startowe: %s", starty)

        nazwa = request.POST.get('nazwa') or f"Plan {request.user.username}"
        adres_startowy = starty.get(1, request.POST.get('adres_startowy'))  # fallback

        try:
            gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
            builder = PlanBuilder(
                user=request.user,
                koszyk_ids=koszyk_ids,
                nazwa=nazwa,
                adres_startowy=adres_startowy,
                przypisane_atrakcje=przypisane_atrakcje,
                gmaps=gmaps,
                starty=starty 
            )
            plan = builder.build()
            request.session['koszyk'] = []  
            logger.info("Zapisano nowy plan ID: %s dla użytkownika %s", plan.id, request.user.username)
            return redirect('plany:szczegoly_planu', id=plan.id)

        except Exception as e:
            logger.error("Błąd podczas zapisywania planu dla użytkownika %s: %s", request.user.username, str(e))
            messages.error(request, "Wystąpił błąd podczas zapisywania planu.")
            return redirect('plany:koszyk')

    else:
        return redirect('plany:koszyk')

@login_required
def export_plan_pdf(request, id):
    """
    Exports the plan to a PDF file along with stage maps.

    Args:
        request (HttpRequest): The HTTP request.
        id (int): ID of the plan.

    Returns:
        HttpResponse: PDF as a downloadable response.
    """
    plan = get_object_or_404(
        PlanZwiedzania.objects.prefetch_related('etapy__elementy__atrakcja__lokalizacja'),
        id=id
    )
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    mapy_etapow = {}
    for etap in plan.etapy.all():
        map_data = build_etap_map(etap, gmaps, plan.adres_startowy)
        if map_data:
            mapy_etapow[etap.id] = map_data
    return render_plan_to_pdf(plan, mapy_etapow, request.build_absolute_uri())

@login_required
def usun_plan(request, id):
    """
    Deletes a user's sightseeing plan if they are the owner.

    Args:
        request (HttpRequest): The HTTP request.
        id (int): ID of the plan.

    Returns:
        HttpResponse: Deletion confirmation or redirect to profile.
    """
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
