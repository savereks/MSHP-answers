from django.shortcuts import render


def general_context(request):
    """ Создает общий контекст """
    context = {
        "menu": [
            ["Задать вопрос", "/create_question"],
        ]
    }
    if request.user.is_authenticated:
        context['menu'].append(['Профиль', '/accounts/profile'])
        context['menu'].append(['Logout', '/accounts/logout'])
    else:
        context['menu'].append(['Логин', '/accounts/login'])
    return context

# Create your views here.


def main(request):
    #questions = Question.objects.filter(id=id).first()
    context = {
    #    'questions': questions
    }
    context.update(general_context(request))
    return render(request, 'index.html', context)


def calculator(request):
    return render(request, 'calc.html', general_context(request))
