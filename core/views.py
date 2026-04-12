from django.shortcuts import render
from core.models import Question, Answer

def general_context(request):
    """ Создает общий контекст """
    context = {
        "menu": [
            ["Задать вопрос", "/create_question"],
        ]
    }
    if request.user.is_authenticated:
        context['menu'].append(['Профиль', '/accounts/profile'])
        context['menu'].append(['Выйти', '/'])
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

def question(request, question_id):
    question = Question.objects.get(id=question_id)
    answers = Answer.objects.filter(question=question)
    context = {
        'question': question,
        'answers': answers
    }
    context.update(general_context(request))
    return render(request, 'question.html', context)

def profile(request):
    """ показывает страницу профиля с именем пользователя"""
    user = request.user
    context = {
        'user': user,
    }
    context.update(general_context(request))
    return render(request, "profile.html", context)
