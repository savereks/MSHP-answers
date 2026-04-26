from django.shortcuts import render, redirect
from core.models import Question, Answer, ProfileImage
from core.forms import Question_Form, Search_Form, AnswerForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, UserRegistrationForm


def general_context(request):
    """ Создает общий контекст """
    search_form = Search_Form()
    context = {
        "menu": [
            ["Задать вопрос", "/create_question"],
        ],
        'sform': search_form
    }
    if request.method == "POST":
        if "title_search" in request.POST:
            title_search = request.POST.get('title_search')
            questions = Question.objects.filter(title__contains=title_search)
            context.update({"questions" : questions})
    if request.user.is_authenticated:
        context['menu'].append(['Профиль', '/accounts/profile/'])
    else:
        context['menu'].append(['Войти', '/accounts/login/'])
    return context

# Create your views here.
def main(request):
    questions = Question.objects.all()[:10]
    context = {
        'questions': questions
    }

    context.update(general_context(request))
    return render(request, 'index.html', context)


def create_question(request):
    if request.method == "POST":
        title = request.POST.get('title')
        text = request.POST.get('text')

        new_question = Question(
            title=title,
            text=text
        )

        new_question.save()

        return redirect('/')

    elif request.method == "GET":
        form = Question_Form()
        context = {
            'form': form
        }
        context.update(general_context(request))
        return render(
            request,
            "create_question.html",
            context
        )

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


@login_required
def profile(request):
    """ показывает страницу профиля с именем пользователя"""
    user = request.user
    profile_image_obj = ProfileImage.objects.filter(user_id=user.id).first()
    profile_pic_url = profile_image_obj.file if profile_image_obj else None
    context = {
        'user': user,
        'profile_pic': profile_pic_url,
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
                    return redirect('/accounts/profile/')
                else:
                    return HttpResponse('Disabled account')
            else:
                return HttpResponse('Invalid login')
    else:
        form = LoginForm()
    context = {
        'form': form
    }
    return render(request, 'registration/login.html', context)


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


def my_questions(request):
    user = request.user
    user_questions = []
    context = {
        'user': user,
        'questions': user_questions
    }
    context.update(general_context(request))
    return render(request, 'my-questions.html', context)
