from django.shortcuts import render, redirect
from core.models import Question, Answer
from core.forms import AnswerForm

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
    if request.method == 'POST':
        answer_form = AnswerForm(request.POST)
        if answer_form.is_valid():
            question = Question.objects.get(id=question_id)
            answer = Answer(
                question=question,
                text=answer_form.cleaned_data['text'],
                author=request.user
            )
            answer.save()
            return redirect(f'/question/{question_id}/')
    elif request.method == 'GET':
        question = Question.objects.get(id=question_id)
        answers = Answer.objects.filter(question=question)
        answer_form = AnswerForm()
        context = {
            'question': question,
            'answers': answers,
            'answer_form': answer_form
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
