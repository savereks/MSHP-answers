from django.shortcuts import render
from core.models import Question
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from .forms import LoginForm, UserRegistrationForm


def general_context(request):
    """ Создает общий контекст """
    context = {
        "menu": [
            ["Задать вопрос", "/create_question"],
        ]
    }
    if request.user.is_authenticated:
        context['menu'].append(['Профиль', '/accounts/profile/'])
        context['menu'].append(['Выйти', '/accounts/logout'])
    else:
        context['menu'].append(['Войти', '/accounts/login'])
    return context

# Create your views here.
def main(request):
    questions = Question.objects.all()[:10]
    context = {
        'questions': questions
    }
    context.update(general_context(request))
    return render(request, 'index.html', context)


def calculator(request):
    return render(request, 'calc.html', general_context(request))


def profile(request):
    """ показывает страницу профиля с именем пользователя"""
    user = request.user
    context = {
        'user': user,
    }
    context.update(general_context(request))
    return render(request, "profile.html", context)


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(username=cd['username'], password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponse('Authenticated successfully')
                else:
                    return HttpResponse('Disabled account')
            else:
                return HttpResponse('Invalid login')
    else:
        form = LoginForm()
    context = {
        'form': form
    }
    return render(request, 'account/login.html', context)


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            # Create a new user object but avoid saving it yet
            new_user = user_form.save(commit=False)
            # Set the chosen password
            new_user.set_password(user_form.cleaned_data['password'])
            # Save the User object
            new_user.save()
            return render(request, 'account/register_done.html', {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
    context = {'user_form': user_form}
    return render(request, 'account/register.html', context)