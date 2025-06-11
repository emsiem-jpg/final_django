import logging
from django.shortcuts import render, get_object_or_404
from .models import Atrakcja, CennikStatystykiMV
from django.conf import settings
from django.db import connection
from django.core.paginator import Paginator

logger = logging.getLogger(__name__)




def lista_atrakcji(request):
    """
    Renders a paginated list of attractions.
    Supports optional filtering by city (via 'miasto' GET parameter).
    Also attaches pricing statistics from materialized view.

    Template: atrakcje/lista_atrakcji.html
    """
    miasto = request.GET.get('miasto', '').strip()
    atrakcje_qs = Atrakcja.objects.all().select_related('lokalizacja', 'kategoria')

    if miasto:
        atrakcje_qs = atrakcje_qs.filter(lokalizacja__miasto__icontains=miasto)
        logger.info(f"Filtruję atrakcje po mieście: {miasto}")

    statystyki_dict = {
        stat.atrakcja_id: stat
        for stat in CennikStatystykiMV.objects.all()
    }

    paginator = Paginator(atrakcje_qs, 10)  # 10 attractions per page
    page_number = request.GET.get("page")
    atrakcje_page = paginator.get_page(page_number)

    logger.debug(f"Wyświetlam stronę {page_number} z listą atrakcji (miasto='{miasto}')")

    return render(request, 'atrakcje/lista_atrakcji.html', {
        'atrakcje': atrakcje_page,
        'miasto': miasto,
        'statystyki_dict': statystyki_dict,
    })


def get_aktualne_ceny(atrakcja_id):
    """
    Executes a custom database function to retrieve current ticket prices for an attraction.

    Args:
        atrakcja_id (int): ID of the attraction.

    Returns:
        list of tuples: [(ticket_type, price, currency), ...]
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT f_aktualne_ceny(%s) FROM dual", [atrakcja_id])
            refcursor = cursor.fetchone()[0]
            ceny = list(refcursor)
            logger.info(f"Pobrano {len(ceny)} cen(y) dla atrakcji ID {atrakcja_id}")
            return ceny
    except Exception as e:
        logger.error(f"Błąd przy pobieraniu cen dla atrakcji ID {atrakcja_id}: {e}", exc_info=True)
        return []


def szczegoly_atrakcji(request, id):
    """
    Renders details for a specific attraction, including pricing and Google Maps integration.

    Args:
        id (int): ID of the attraction.

    Template: atrakcje/szczegoly.html
    """
    atrakcja = get_object_or_404(Atrakcja.objects.select_related('kategoria'), id=id)
    logger.debug(f"Pobrano szczegóły atrakcji: {atrakcja.nazwa} (ID: {id})")

    glowne_zdjecie = atrakcja.zdjecia.filter(is_glowne=True).first()
    pozostale_zdjecia = atrakcja.zdjecia.exclude(id=glowne_zdjecie.id) if glowne_zdjecie else atrakcja.zdjecia.all()
    ceny = get_aktualne_ceny(atrakcja.id)
    godziny = atrakcja.godziny_otwarcia.all().order_by('dzien_tygodnia')

    return render(request, 'atrakcje/szczegoly.html', {
        'atrakcja': atrakcja,
        'ceny': ceny,
        'godziny': godziny,
        'google_maps_key': settings.GOOGLE_MAPS_API_KEY
    })


def strona_glowna(request):
    """
    Renders the homepage of the application.

    Template: atrakcje/strona_glowna.html
    """
    logger.debug("Wejście na stronę główną")
    return render(request, 'atrakcje/strona_glowna.html')
