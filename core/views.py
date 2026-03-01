from django.shortcuts import render


def general_context(request):
    """ Создает общий контекст """
    context = {
        'user': request.user,
        "menu": [
            ["Задать вопрос", "/create_question"],
        ]
    }
    if not request.user.is_authenticated:
        context['menu'].append(['Профиль', '/accounts/profile'])
        context['menu'].append(['Logout', '/accounts/logout'])
    else:
        context['menu'].append(['Логин', '/accounts/login'])
    return context


def main(request):
    return render(request, 'index.html', general_context(request))


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

