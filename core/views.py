import logging
from core.models import Question, Answer, ProfileImage, Vote, User, Comment
from core.forms import Question_Form, Search_Form, AnswerForm, UserRegistrationForm, ProfileForm, CommentForm
from core.constants import ALL_TAGS, get_all_tags, get_tag_by_id
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, UserRegistrationForm
from django.db import models

logger = logging.getLogger(__name__)


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
            logger.info(f"Поиск по запросу: '{title_search}', найдено: {questions.count()}")
            context.update({"questions": questions})
    if request.user.is_authenticated:
        context['menu'].append(['Профиль', f'/accounts/profile/{request.user.id}'])
    else:
        context['menu'].append(['Войти', '/accounts/login/'])
        context['menu'].append(['Регистрация', '/accounts/register/'])
    return context


def main(request):
    logger.info(f"Главная страница открыта пользователем: {request.user}")
    context = {}
    context.update(general_context(request))

    # Получаем все теги из констант
    all_tags = ALL_TAGS

    # Получаем выбранные теги
    selected_tags = [int(tag) for tag in request.GET.getlist('tags') if tag]

    # Получаем поисковый запрос
    search_query = request.GET.get('q', '').strip()

    if 'questions' in context:
        qs = context['questions'].select_related('author')
    else:
        qs = (
            Question.objects.select_related('author')
            .order_by('-created_at')
        )

    # Поиск по тексту вопроса
    if search_query:
        qs = qs.filter(
            models.Q(title__icontains=search_query) |
            models.Q(text__icontains=search_query)
        )
        logger.info(f"Поиск через GET: '{search_query}'")

    # Фильтрация по тегам
    if selected_tags:
        for tag_id in selected_tags:
            tag = get_tag_by_id(tag_id)
            if tag:
                qs = qs.filter(tags__contains=str(tag_id))
        logger.debug(f"Фильтрация по тегам: {selected_tags}")

    questions = list(qs)
    logger.debug(f"Загружено вопросов: {len(questions)}")
    author_ids = {q.author_id for q in questions if q.author_id}
    avatar_by_user = {}

    if author_ids:
        for img in ProfileImage.objects.filter(user_id__in=author_ids).select_related('user'):
            if img.avatar:
                avatar_by_user[img.user_id] = img.avatar.url

    for question in questions:
        qvotes = Vote.objects.filter(question=question, answer__isnull=True)
        question.likes = qvotes.filter(vote_type=True).count()
        question.dislikes = qvotes.filter(vote_type=False).count()
        question.rating = question.likes - question.dislikes
        aid = question.author_id
        question.author_avatar_url = avatar_by_user.get(aid, '/media/profile_pics/default.jpg')

        # Преобразуем строку тегов в список объектов для шаблона
        question_tags_ids = [int(t) for t in question.tags.split(',') if t]
        question.tag_objects = [get_tag_by_id(tag_id) for tag_id in question_tags_ids if get_tag_by_id(tag_id)]

    context['questions'] = questions
    context['all_tags'] = all_tags
    context['selected_tags'] = selected_tags
    context['search_query'] = search_query
    return render(request, 'index.html', context)


@login_required(login_url='/accounts/login/')
@require_POST
def vote_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    raw = request.POST.get('vote', '')
    if raw == 'like':
        vote_type = True
    elif raw == 'dislike':
        vote_type = False
    else:
        logger.warning(f"Неправильный голос: '{raw}' от пользователя {request.user}")
        return JsonResponse({'error': 'invalid vote'}, status=400)

    # Проверяем существующий голос
    existing_vote = Vote.objects.filter(
        user=request.user,
        question=question,
        answer__isnull=True,
        comment__isnull=True
    ).first()

    if existing_vote:
        if existing_vote.vote_type == vote_type:
            existing_vote.delete()
        else:
            existing_vote.vote_type = vote_type
            existing_vote.save()
    else:
        Vote.objects.create(
            user=request.user,
            question=question,
            vote_type=vote_type
        )

    logger.info(f"Пользователь {request.user.username} {'лайкнул' if vote_type else 'дизлайкнул'} вопрос {question_id}")

    # Подсчитываем голоса только за вопрос
    qvotes = Vote.objects.filter(question=question, answer__isnull=True, comment__isnull=True)
    likes = qvotes.filter(vote_type=True).count()
    dislikes = qvotes.filter(vote_type=False).count()
    return JsonResponse(
        {'likes': likes, 'dislikes': dislikes, 'rating': likes - dislikes}
    )


@login_required(login_url='/accounts/login/')
@require_POST
def vote_answer(request, answer_id):
    """Голосование за ответ """
    answer = get_object_or_404(Answer, pk=answer_id)
    raw = request.POST.get('vote', '')

    if raw == 'like':
        vote_type = True
    elif raw == 'dislike':
        vote_type = False
    else:
        logger.warning(f"Неправильный голос за ответ: '{raw}' от пользователя {request.user}")
        return JsonResponse({'error': 'invalid vote'}, status=400)

    # Проверяем существующий голос
    existing_vote = Vote.objects.filter(
        user=request.user,
        answer=answer,
        comment__isnull=True
    ).first()

    if existing_vote:
        if existing_vote.vote_type == vote_type:
            existing_vote.delete()
        else:
            existing_vote.vote_type = vote_type
            existing_vote.save()
    else:
        Vote.objects.create(
            user=request.user,
            answer=answer,
            vote_type=vote_type
        )

    logger.info(f"Пользователь {request.user.username} {'лайкнул' if vote_type else 'дизлайкнул'} ответ {answer_id}")

    # Подсчитываем голоса только за ответ
    answer_votes = Vote.objects.filter(answer=answer, comment__isnull=True)
    likes = answer_votes.filter(vote_type=True).count()
    dislikes = answer_votes.filter(vote_type=False).count()

    return JsonResponse({
        'likes': likes,
        'dislikes': dislikes,
        'rating': likes - dislikes
    })


@login_required(login_url='/accounts/login/')
@require_POST
def add_comment(request, answer_id):
    """Добавление комментария к ответу"""
    answer = get_object_or_404(Answer, pk=answer_id)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = Comment(
            text=form.cleaned_data['text'],
            author=request.user,
            answer=answer
        )
        comment.save()
        logger.info(f"Пользователь {request.user.username} добавил комментарий к ответу {answer_id}")

    return redirect(f'/question/{answer.question.id}/')


@login_required(login_url='/accounts/login/')
@require_POST
def vote_comment(request, comment_id):
    """Голосование за комментарий"""
    comment = get_object_or_404(Comment, pk=comment_id)
    raw = request.POST.get('vote', '')

    if raw == 'like':
        vote_type = True
    elif raw == 'dislike':
        vote_type = False
    else:
        logger.warning(f"Неправильный голос за комментарий: '{raw}' от пользователя {request.user}")
        return JsonResponse({'error': 'invalid vote'}, status=400)

    # Проверяем существующий голос
    existing_vote = Vote.objects.filter(
        user=request.user,
        comment=comment
    ).first()

    if existing_vote:
        if existing_vote.vote_type == vote_type:
            existing_vote.delete()
        else:
            existing_vote.vote_type = vote_type
            existing_vote.save()
    else:
        Vote.objects.create(
            user=request.user,
            comment=comment,
            vote_type=vote_type
        )

    logger.info(f"Пользователь {request.user.username} {'лайкнул' if vote_type else 'дизлайкнул'} комментарий {comment_id}")

    # Подсчитываем голоса
    comment_votes = Vote.objects.filter(comment=comment)
    likes = comment_votes.filter(vote_type=True).count()
    dislikes = comment_votes.filter(vote_type=False).count()

    return JsonResponse({
        'likes': likes,
        'dislikes': dislikes,
        'rating': likes - dislikes
    })


@login_required(login_url='/accounts/login/')
def create_question(request):
    if request.method == "POST":
        title = request.POST.get('title')
        text = request.POST.get('text')
        tags = request.POST.getlist('tags')
        author = request.user

        tags_str = ','.join(tags) if tags else ''

        new_question = Question(
            title=title,
            text=text,
            author=author,
            tags=tags_str
        )

        new_question.save()
        logger.info(f"Пользователь {author.username} создал вопрос: '{title}' (ID: {new_question.id}) с тегами: {tags}")

        return redirect('/')

    elif request.method == "GET":
        form = Question_Form()
        context = {
            'form': form
        }
        context.update(general_context(request))
        return render(request, "create_question.html", context)


def question(request, question_id):
    if request.method == 'POST':
        answer_form = AnswerForm(request.POST)
        if answer_form.is_valid() and request.user.is_authenticated:
            question = Question.objects.get(id=question_id)
            answer = Answer(
                question=question,
                text=answer_form.cleaned_data['text'],
                author=request.user
            )
            answer.save()
            logger.info(f"Пользователь {request.user.username} добавил ответ на вопрос {question_id}")
        return redirect(f'/question/{question_id}/')

    elif request.method == 'GET':
        question = Question.objects.get(id=question_id)

        # Рассчитываем рейтинг вопроса
        qvotes = Vote.objects.filter(question=question, answer__isnull=True, comment__isnull=True)
        question.likes = qvotes.filter(vote_type=True).count()
        question.dislikes = qvotes.filter(vote_type=False).count()
        question.rating = question.likes - question.dislikes

        # Получаем аватар автора
        if question.author:
            profile = ProfileImage.objects.filter(user=question.author).first()
            question.author_avatar_url = profile.avatar.url if profile and profile.avatar else '/media/profile_pics/default.jpg'
        else:
            question.author_avatar_url = '/media/profile_pics/default.jpg'

        # Преобразуем теги вопроса
        question_tags_ids = [int(t) for t in question.tags.split(',') if t] if hasattr(question, 'tags') else []
        question.tag_objects = [get_tag_by_id(tag_id) for tag_id in question_tags_ids if get_tag_by_id(tag_id)]

        answers = Answer.objects.filter(question=question).select_related('author__profile')

        # Рассчитываем рейтинг для каждого ответа и загружаем комментарии
        for answer in answers:
            # Рейтинг ответа (только голоса за ответ, без комментариев)
            avotes = Vote.objects.filter(answer=answer, comment__isnull=True)
            answer.likes = avotes.filter(vote_type=True).count()
            answer.dislikes = avotes.filter(vote_type=False).count()
            answer.rating = answer.likes - answer.dislikes

            # Получаем аватар автора ответа
            if answer.author:
                profile = ProfileImage.objects.filter(user=answer.author).first()
                answer.author_avatar_url = profile.avatar.url if profile and profile.avatar else '/media/profile_pics/default.jpg'
            else:
                answer.author_avatar_url = '/media/profile_pics/default.jpg'

            # Загружаем комментарии к ответу
            answer.comments = Comment.objects.filter(answer=answer).select_related('author__profile').order_by('created_at')

            # Рассчитываем рейтинг для каждого комментария
            for comment in answer.comments:
                comment_votes = Vote.objects.filter(comment=comment)
                comment.likes = comment_votes.filter(vote_type=True).count()
                comment.dislikes = comment_votes.filter(vote_type=False).count()
                comment.rating = comment.likes - comment.dislikes

                # Получаем аватар автора комментария
                if comment.author:
                    profile = ProfileImage.objects.filter(user=comment.author).first()
                    comment.author_avatar_url = profile.avatar.url if profile and profile.avatar else '/media/profile_pics/default.jpg'
                else:
                    comment.author_avatar_url = '/media/profile_pics/default.jpg'

        answer_form = AnswerForm()
        comment_form = CommentForm()
        logger.debug(f"Открыт вопрос {question_id}, ответов: {answers.count()}")

        context = {
            'question': question,
            'answers': answers,
            'answer_form': answer_form,
            'comment_form': comment_form,
        }
        context.update(general_context(request))
        return render(request, 'question.html', context)


@login_required(login_url='/accounts/login/')
def profile(request, profile_id):
    """ Показывает страницу профиля с именем пользователя"""

    user = User.objects.get(id=profile_id)
    profile, created = ProfileImage.objects.get_or_create(user=user)
    logger.debug(f"Открыт профиль пользователя: {user.username}")

    context = {
        'user': user,
        'profile': profile,
    }
    context.update(general_context(request))
    return render(request, 'profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            logger.info(f"Пользователь {request.user.username} обновил профиль")
            return redirect('profile', profile_id=request.user.id)
    else:
        form = ProfileForm(instance=request.user.profile)

    context = {
        'form': form,
    }
    context.update(general_context(request))
    return render(request, 'edit_profile.html', context)


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(username=cd['username'], password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    logger.info(f"Пользователь вошёл: {user.username}")

                    next_url = request.POST.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect(f'/accounts/profile/{user.id}')
                else:
                    logger.warning(f"Попытка входа в заблокированный аккаунт: {cd['username']}")
                    form.add_error(None, 'Учётная запись заблокирована')
            else:
                logger.warning(f"Неудачная попытка входа для пользователя: {cd['username']}")
                form.add_error(None, 'Неверное имя пользователя или пароль')
    else:
        form = LoginForm()

    context = {
        'form': form
    }
    context.update(general_context(request))
    return render(request, 'registration/login.html', context)


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(f"Новый пользователь зарегистрирован: {user.username}")

            login(request, user)

            return redirect(f'/accounts/profile/{user.id}/')
    else:
        form = UserRegistrationForm()

    context = {
        'form': form
    }
    context.update(general_context(request))
    return render(request, 'registration/register.html', context)


@login_required(login_url='/accounts/login/')
def my_questions(request):
    """Показывает вопросы пользователя и его ответы на чужие вопросы"""
    user = request.user

    # Вопросы пользователя с количеством ответов
    user_questions = (
        Question.objects.filter(author=user)
        .order_by('-created_at')
    )

    # Добавляем количество ответов к каждому вопросу
    for question in user_questions:
        question.answers_count = Answer.objects.filter(question=question).count()
        # Преобразуем теги
        question_tags_ids = [int(t) for t in question.tags.split(',') if t]
        question.tag_objects = [get_tag_by_id(tag_id) for tag_id in question_tags_ids if get_tag_by_id(tag_id)]

    # Ответы пользователя на чужие вопросы
    user_answers = (
        Answer.objects.filter(author=user)
        .select_related('question', 'question__author')
        .order_by('-created_at')
    )

    # Добавляем рейтинг для каждого ответа
    for answer in user_answers:
        answer_votes = Vote.objects.filter(answer=answer)
        answer.likes = answer_votes.filter(vote_type=True).count()
        answer.dislikes = answer_votes.filter(vote_type=False).count()
        answer.rating = answer.likes - answer.dislikes

    logger.debug(
        f"Пользователь {user.username} открыл свои вопросы и ответы: найдено вопросов - {user_questions.count()}, ответов - {user_answers.count()}")

    context = {
        'user': user,
        'questions': user_questions,
        'answers': user_answers,
    }
    context.update(general_context(request))
    return render(request, 'my-questions.html', context)