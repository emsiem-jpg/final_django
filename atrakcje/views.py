from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from .models import Atrakcja, CennikStatystyki
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from .forms import AtrakcjaForm, LokalizacjaForm
from django.db import connection
from rest_framework import viewsets
from .models import Atrakcja
from .serializers import AtrakcjaSerializer
from django.core.paginator import Paginator
import logging
logger = logging.getLogger(__name__)

class AtrakcjaViewSet(viewsets.ModelViewSet):
    queryset = Atrakcja.objects.all()
    serializer_class = AtrakcjaSerializer


def lista_atrakcji(request):
    miasto = request.GET.get('miasto', '').strip()
    atrakcje_qs = Atrakcja.objects.all().select_related('lokalizacja', 'kategoria')

    if miasto:
        atrakcje_qs = atrakcje_qs.filter(lokalizacja__miasto__icontains=miasto)

    statystyki_dict = {
        stat.atrakcja_id: stat
        for stat in CennikStatystyki.objects.all()
    }

    paginator = Paginator(atrakcje_qs, 10)  # 10 atrakcji na stronę
    page_number = request.GET.get("page")
    atrakcje_page = paginator.get_page(page_number)

    return render(request, 'atrakcje/lista_atrakcji.html', {
        'atrakcje': atrakcje_page,
        'miasto': miasto,
        'statystyki_dict': statystyki_dict,
    })


def get_aktualne_ceny(atrakcja_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT f_aktualne_ceny(%s) FROM dual", [atrakcja_id])
        refcursor = cursor.fetchone()[0]
        return list(refcursor)  # [(rodzaj, cena, waluta), ...]


def szczegoly_atrakcji(request, id):
    atrakcja = get_object_or_404(Atrakcja.objects.select_related('kategoria'), id=id)
    ceny = get_aktualne_ceny(atrakcja.id)
    return render(request, 'atrakcje/szczegoly.html', {
        'atrakcja': atrakcja,
        'ceny': ceny,
        'google_maps_key': settings.GOOGLE_MAPS_API_KEY
    })

def strona_glowna(request):
    return render(request, 'atrakcje/strona_glowna.html')

def dodaj_atrakcje(request):
    if not request.user.is_authenticated or request.user.role not in ['guide', 'moderator', 'admin']:
        
        return HttpResponseForbidden("Nie masz uprawnień do dodawania atrakcji.")

    if request.method == 'POST':
        atrakcja_form = AtrakcjaForm(request.POST)
        lokalizacja_form = LokalizacjaForm(request.POST)
        logger.warning("Dostęp zabroniony do dodawania atrakcji dla użytkownika: %s", request.user.username)
        if atrakcja_form.is_valid() and lokalizacja_form.is_valid():
            atrakcja = atrakcja_form.save()
            lokalizacja = lokalizacja_form.save(commit=False)
            lokalizacja.atrakcja = atrakcja
            lokalizacja.save()  # tu odpali się geokodowanie
            logger.info("Dodano nową atrakcję: %s (ID: %s) przez użytkownika %s", atrakcja.nazwa, atrakcja.id, request.user.username)
            return HttpResponseRedirect(reverse('szczegoly', args=[atrakcja.id]))
    else:
        atrakcja_form = AtrakcjaForm()
        lokalizacja_form = LokalizacjaForm()

    return render(request, 'atrakcje/dodaj.html', {
        'atrakcja_form': atrakcja_form,
        'lokalizacja_form': lokalizacja_form
    })

