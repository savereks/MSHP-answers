"""
Аутентификация и регистрация пользователей.
"""

import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from core.forms import LoginForm, UserRegistrationForm
from core.models import ProfileImage
from core.views.context import general_context

logger = logging.getLogger(__name__)


def user_login(request):
    """Страница входа пользователя."""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)

            if user is not None and user.is_active:
                try:
                    profile = ProfileImage.objects.get(user=user)
                    if profile.is_blocked:
                        form.add_error(None, 'Ваш аккаунт заблокирован. Обратитесь к администратору.')
                        context = {'form': form}
                        context.update(general_context(request))
                        return render(request, 'registration/login.html', context)
                except ProfileImage.DoesNotExist:
                    pass

                login(request, user)
                logger.info(f"Пользователь вошёл: {user.username}")

                next_url = request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(f'/accounts/profile/{user.id}')

            logger.warning(f"Неудачная попытка входа для пользователя: {username}")
            form.add_error(None, 'Неверное имя пользователя или пароль')
    else:
        form = LoginForm()

    context = {'form': form}
    context.update(general_context(request))
    return render(request, 'registration/login.html', context)


def register(request):
    """Страница регистрации нового пользователя."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(f"Новый пользователь зарегистрирован: {user.username}")
            login(request, user)
            return redirect(f'/accounts/profile/{user.id}/')
    else:
        form = UserRegistrationForm()

    context = {'form': form}
    context.update(general_context(request))
    return render(request, 'registration/register.html', context)