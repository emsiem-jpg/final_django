import logging
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML

logger = logging.getLogger(__name__)

def render_plan_to_pdf(plan, mapy_etapow, base_url):
    """
    Renders a sightseeing plan into a downloadable PDF file using WeasyPrint.

    Args:
        plan (PlanZwiedzania): The sightseeing plan instance to render.
        mapy_etapow (dict): A dictionary of etap_id -> map image URLs (or paths).
        base_url (str): Absolute base URL used to resolve static/media files in the HTML.

    Returns:
        HttpResponse: A response containing the generated PDF file.
    """
    try:
        logger.debug(f"Rozpoczynam renderowanie PDF dla planu ID {plan.id}")

        html_string = render_to_string('plany/plan_pdf.html', {
            'plan': plan,
            'mapy_etapow': mapy_etapow,
            'etap_info': {},  
        })

        pdf_file = HTML(string=html_string, base_url=base_url).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="plan_{plan.id}.pdf"'

        logger.info(f"Wygenerowano PDF dla planu ID {plan.id}")
        return response

    except Exception as e:
        logger.error(f"Błąd podczas generowania PDF dla planu ID {plan.id}: {e}", exc_info=True)
        return HttpResponse("Błąd podczas generowania PDF.", status=500)
