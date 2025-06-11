import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.timezone import now
from plany.models import PlanUzytkownika
from .forms import LoginForm, CustomUserCreationForm

User = get_user_model()
logger = logging.getLogger(__name__)


def test_email_view(request):
    """
    Simple view to send a test email to verify email configuration.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: A message indicating the email was sent.
    """
    send_mail(
        subject="Test maila z Django",
        message="Gratulacje! Mail działa poprawnie.",
        from_email=None,  
        recipient_list=['emsiem-jpg@wp.pl'],  
        fail_silently=False,
    )
    return HttpResponse("Email został wysłany.")


class CustomLoginView(LoginView):
    """
    Extends Django's built-in LoginView to log successful logins.

    Attributes:
        template_name (str): The template used to render the login page.
    """
    template_name = 'konta/login.html'

    def form_valid(self, form):
        logger.info("Zalogowano użytkownika: %s", form.get_user().username)
        return super().form_valid(form)


def login_user(request):
    """
    Custom login view using LoginForm. Authenticates and logs in the user manually.

    Redirects to the next URL if present, or to the homepage.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: The login page or a redirect upon successful login.
    """
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if not user.is_active:
                    messages.error(request, "Konto nieaktywne. Sprawdź e-mail aktywacyjny.")
                    return redirect("konta:login")
                login(request, user)
                next_url = request.GET.get('next') or 'strona_glowna'
                return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'konta/login.html', {'form': form})


def register_view(request):
    """
    Custom user registration view that creates a new inactive user and sends
    an email with an activation link.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: The registration page or redirect after successful registration.
    """
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            logger.info("Zarejestrowano nowego użytkownika: %s", user.username)

            # Generuj link aktywacyjny
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = request.build_absolute_uri(
                reverse('konta:activate', kwargs={'uidb64': uid, 'token': token})
            )

            html_message = render_to_string('konta/email_activation.html', {
                'user': user,
                'activation_link': activation_link,
                'current_year': now().year,
            })

            send_mail(
                subject="Aktywuj swoje konto",
                message=f"Cześć {user.username}, kliknij link: {activation_link}",  
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
                html_message=html_message,  
            )

            messages.success(request, "Rejestracja zakończona. Sprawdź e-mail, aby aktywować konto.")
            return redirect("konta:login")
    else:
        form = CustomUserCreationForm()

    return render(request, 'konta/register.html', {'form': form})


def activate_account(request, uidb64, token):
    """
    Activates a newly registered user if the token and uid match.

    Args:
        request (HttpRequest): The incoming request.
        uidb64 (str): Base64 encoded user ID.
        token (str): Token to verify user identity.

    Returns:
        HttpResponse: A message confirming activation or failure.
    """
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Konto zostało aktywowane. Możesz się teraz zalogować.")
        return redirect('konta:login')
    else:
        return HttpResponse("Nieprawidłowy lub wygasły link aktywacyjny.")


@login_required
def profile(request):
    """
    Displays the user's profile with their sightseeing plans.

    Requires authentication.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: The profile page with the user's plans.
    """
    moje_plany = PlanUzytkownika.objects.select_related('plan').filter(
        uzytkownik=request.user
    ).order_by('-plan__data_utworzenia')

    return render(request, 'konta/profile.html', {
        'moje_plany': moje_plany
    })
