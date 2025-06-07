from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
from plany.models import PlanUzytkownika
from .forms import CustomUserCreationForm  
from django.contrib.auth.views import LoginView
import logging
logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    template_name = 'konta/login.html'
    def form_valid(self, form):
        logger.info("Zalogowano użytkownika: %s", form.get_user().username)
        return super().form_valid(form)
    
def login_user(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next') or 'strona_glowna'
                return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'konta/login.html', {'form': form})





def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info("Zarejestrowano nowego użytkownika: %s", user.username)
            return redirect("login")
    else:
        form = CustomUserCreationForm()
    return render(request, 'konta/register.html', {'form': form})



@login_required
def profile(request):
    moje_plany = PlanUzytkownika.objects.select_related('plan').filter(
        uzytkownik=request.user
    ).order_by('-plan__data_utworzenia')

    return render(request, 'konta/profile.html', {
        'moje_plany': moje_plany
    })