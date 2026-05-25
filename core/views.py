"""
Представления (views) для основного приложения.
Содержит все функции-обработчики HTTP запросов.
"""
import logging

from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from core.constants import ALL_TAGS, get_tag_by_id
from core.forms import (
    QuestionForm, SearchForm, AnswerForm, UserRegistrationForm,
    ProfileForm, CommentForm, LoginForm
)
from core.models import Question, Answer, ProfileImage, Vote, User, Comment

logger = logging.getLogger(__name__)


def general_context(request):
    """Создаёт общий контекст для всех страниц."""
    search_form = SearchForm()
    context = {
        "menu": [["Задать вопрос", "/create_question"]],
        'sform': search_form
    }

    if request.method == "POST" and "title_search" in request.POST:
        title_search = request.POST.get('title_search')
        questions = Question.objects.filter(title__contains=title_search)
        logger.info(
            f"Поиск по запросу: '{title_search}', найдено: {questions.count()}"
        )
        context.update({"questions": questions})

    if request.user.is_authenticated:
        context['menu'].append(
            ['Профиль', f'/accounts/profile/{request.user.id}']
        )
    else:
        context['menu'].append(['Войти', '/accounts/login/'])
        context['menu'].append(['Регистрация', '/accounts/register/'])

    return context


def get_user_role(user):
    """
    Определяет роль пользователя на основе рейтинга.
    Возвращает: 'admin', 'trusted', 'user'
    """
    if user.is_staff:
        return 'admin'

    # Рассчёт рейтинга пользователя
    total_rating = 0
    for question in Question.objects.filter(author=user):
        question_votes = Vote.objects.filter(
            question=question, answer__isnull=True, comment__isnull=True
        )
        likes = question_votes.filter(vote_type=True).count()
        dislikes = question_votes.filter(vote_type=False).count()
        total_rating += (likes - dislikes)

    for answer in Answer.objects.filter(author=user):
        answer_votes = Vote.objects.filter(answer=answer, comment__isnull=True)
        likes = answer_votes.filter(vote_type=True).count()
        dislikes = answer_votes.filter(vote_type=False).count()
        total_rating += (likes - dislikes)

    for comment in Comment.objects.filter(author=user):
        comment_votes = Vote.objects.filter(comment=comment)
        likes = comment_votes.filter(vote_type=True).count()
        dislikes = comment_votes.filter(vote_type=False).count()
        total_rating += (likes - dislikes)

    if total_rating >= 10:
        return 'trusted'
    return 'user'


def can_delete_content(user, content_author):
    """
    Проверяет, может ли пользователь удалить контент.
    - Администратор может удалять любые вопросы
    - Доверенный участник (рейтинг ≥ 10) может удалять любые вопросы
    - Обычный пользователь может удалять только свои вопросы
    """
    if user.is_staff:
        return True

    if get_user_role(user) == 'trusted':
        return True

    return user == content_author


def can_create_content(user):
    """
    Проверяет, может ли пользователь создавать контент (не заблокирован).
    """
    try:
        profile = ProfileImage.objects.get(user=user)
        return not profile.is_blocked
    except ProfileImage.DoesNotExist:
        return True


@login_required(login_url='/accounts/login/')
@require_POST
def toggle_block_user(request, user_id):
    """
    Блокировка/разблокировка пользователя (только для администратора).
    """
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Недостаточно прав'
        }, status=403)

    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = ProfileImage.objects.get_or_create(user=target_user)
    profile.is_blocked = not profile.is_blocked
    profile.save()

    status_text = "заблокирован" if profile.is_blocked else "разблокирован"
    logger.info(
        f"Администратор {request.user.username} "
        f"{status_text} пользователя {target_user.username}"
    )

    return JsonResponse({
        'success': True,
        'is_blocked': profile.is_blocked,
        'message': f'Пользователь {status_text}'
    })


def main(request):
    """Главная страница со списком вопросов."""
    logger.info(f"Главная страница открыта пользователем: {request.user}")
    context = {}
    context.update(general_context(request))

    all_tags = ALL_TAGS
    selected_tags = [int(tag) for tag in request.GET.getlist('tags') if tag]
    search_query = request.GET.get('q', '').strip()

    if 'questions' in context:
        queryset = context['questions'].select_related('author')
    else:
        queryset = Question.objects.select_related('author').order_by('-created_at')

    if search_query:
        queryset = queryset.filter(
            models.Q(title__icontains=search_query) |
            models.Q(text__icontains=search_query)
        )
        logger.info(f"Поиск через GET: '{search_query}'")

    if selected_tags:
        for tag_id in selected_tags:
            tag = get_tag_by_id(tag_id)
            if tag:
                queryset = queryset.filter(tags__contains=str(tag_id))
        logger.debug(f"Фильтрация по тегам: {selected_tags}")

    questions = list(queryset)
    logger.debug(f"Загружено вопросов: {len(questions)}")

    author_ids = {q.author_id for q in questions if q.author_id}
    avatar_by_user = {}

    if author_ids:
        for img in ProfileImage.objects.filter(
            user_id__in=author_ids
        ).select_related('user'):
            if img.avatar:
                avatar_by_user[img.user_id] = img.avatar.url

    for question in questions:
        question_votes = Vote.objects.filter(
            question=question, answer__isnull=True, comment__isnull=True
        )
        question.likes = question_votes.filter(vote_type=True).count()
        question.dislikes = question_votes.filter(vote_type=False).count()
        question.rating = question.likes - question.dislikes

        author_id = question.author_id
        question.author_avatar_url = avatar_by_user.get(
            author_id, '/media/profile_pics/default.jpg'
        )

        tag_ids = [int(tag_id) for tag_id in question.tags.split(',') if tag_id]
        question.tag_objects = [
            get_tag_by_id(tag_id) for tag_id in tag_ids if get_tag_by_id(tag_id)
        ]

    context['questions'] = questions
    context['all_tags'] = all_tags
    context['selected_tags'] = selected_tags
    context['search_query'] = search_query

    if request.user.is_authenticated:
        context['user_role'] = get_user_role(request.user)
    else:
        context['user_role'] = None

    return render(request, 'index.html', context)


@login_required(login_url='/accounts/login/')
@require_POST
def vote_question(request, question_id):
    """Обработка голосования за вопрос."""
    question = get_object_or_404(Question, pk=question_id)
    raw_vote = request.POST.get('vote', '')

    if raw_vote == 'like':
        vote_type = True
    elif raw_vote == 'dislike':
        vote_type = False
    else:
        logger.warning(
            f"Неправильный голос: '{raw_vote}' от пользователя {request.user}"
        )
        return JsonResponse({'error': 'invalid vote'}, status=400)

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

    logger.info(
        f"Пользователь {request.user.username} "
        f"{'лайкнул' if vote_type else 'дизлайкнул'} вопрос {question_id}"
    )

    question_votes = Vote.objects.filter(
        question=question, answer__isnull=True, comment__isnull=True
    )
    likes = question_votes.filter(vote_type=True).count()
    dislikes = question_votes.filter(vote_type=False).count()

    return JsonResponse({
        'likes': likes,
        'dislikes': dislikes,
        'rating': likes - dislikes
    })


@login_required(login_url='/accounts/login/')
@require_POST
def vote_answer(request, answer_id):
    """Обработка голосования за ответ."""
    answer = get_object_or_404(Answer, pk=answer_id)
    raw_vote = request.POST.get('vote', '')

    if raw_vote == 'like':
        vote_type = True
    elif raw_vote == 'dislike':
        vote_type = False
    else:
        logger.warning(
            f"Неправильный голос за ответ: '{raw_vote}' "
            f"от пользователя {request.user}"
        )
        return JsonResponse({'error': 'invalid vote'}, status=400)

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

    logger.info(
        f"Пользователь {request.user.username} "
        f"{'лайкнул' if vote_type else 'дизлайкнул'} ответ {answer_id}"
    )

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
    """Добавление комментария к ответу."""
    answer = get_object_or_404(Answer, pk=answer_id)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = Comment(
            text=form.cleaned_data['text'],
            author=request.user,
            answer=answer
        )
        comment.save()
        logger.info(
            f"Пользователь {request.user.username} "
            f"добавил комментарий к ответу {answer_id}"
        )

    return redirect(f'/question/{answer.question.id}/')


@login_required(login_url='/accounts/login/')
@require_POST
def vote_comment(request, comment_id):
    """Обработка голосования за комментарий."""
    comment = get_object_or_404(Comment, pk=comment_id)
    raw_vote = request.POST.get('vote', '')

    if raw_vote == 'like':
        vote_type = True
    elif raw_vote == 'dislike':
        vote_type = False
    else:
        logger.warning(
            f"Неправильный голос за комментарий: '{raw_vote}' "
            f"от пользователя {request.user}"
        )
        return JsonResponse({'error': 'invalid vote'}, status=400)

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

    logger.info(
        f"Пользователь {request.user.username} "
        f"{'лайкнул' if vote_type else 'дизлайкнул'} комментарий {comment_id}"
    )

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
    """Создание нового вопроса."""
    # Проверка на блокировку
    profile = ProfileImage.objects.get(user=request.user)
    if profile.is_blocked:
        context = {'error': 'Ваш аккаунт заблокирован. Вы не можете создавать вопросы.'}
        context.update(general_context(request))
        return render(request, "create_question.html", context)

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

        logger.info(
            f"Пользователь {author.username} создал вопрос: '{title}' "
            f"(ID: {new_question.id}) с тегами: {tags}"
        )
        return redirect('/')

    form = QuestionForm()
    context = {'form': form}
    context.update(general_context(request))

    return render(request, "create_question.html", context)


def question(request, question_id):
    """Страница просмотра вопроса."""
    if request.method == 'POST':
        answer_form = AnswerForm(request.POST)
        if answer_form.is_valid() and request.user.is_authenticated:
            # Проверка на блокировку
            try:
                profile = ProfileImage.objects.get(user=request.user)
                if profile.is_blocked:
                    return redirect(f'/question/{question_id}/')
            except ProfileImage.DoesNotExist:
                pass

            question_obj = Question.objects.get(id=question_id)
            answer = Answer(
                question=question_obj,
                text=answer_form.cleaned_data['text'],
                author=request.user
            )
            answer.save()
            logger.info(
                f"Пользователь {request.user.username} "
                f"добавил ответ на вопрос {question_id}"
            )
        return redirect(f'/question/{question_id}/')

    # GET запрос - отображение страницы
    question_obj = Question.objects.get(id=question_id)

    question_votes = Vote.objects.filter(
        question=question_obj, answer__isnull=True, comment__isnull=True
    )
    question_obj.likes = question_votes.filter(vote_type=True).count()
    question_obj.dislikes = question_votes.filter(vote_type=False).count()
    question_obj.rating = question_obj.likes - question_obj.dislikes

    if question_obj.author:
        profile = ProfileImage.objects.filter(user=question_obj.author).first()
        avatar_url = profile.avatar.url if profile and profile.avatar \
            else '/media/profile_pics/default.jpg'
        question_obj.author_avatar_url = avatar_url
    else:
        question_obj.author_avatar_url = '/media/profile_pics/default.jpg'

    tag_ids = [
        int(tag_id) for tag_id in question_obj.tags.split(',') if tag_id
    ]
    question_obj.tag_objects = [
        get_tag_by_id(tag_id) for tag_id in tag_ids if get_tag_by_id(tag_id)
    ]

    answers = Answer.objects.filter(
        question=question_obj
    ).select_related('author__profile')

    for answer in answers:
        answer_votes = Vote.objects.filter(answer=answer, comment__isnull=True)
        answer.likes = answer_votes.filter(vote_type=True).count()
        answer.dislikes = answer_votes.filter(vote_type=False).count()
        answer.rating = answer.likes - answer.dislikes

        if answer.author:
            profile = ProfileImage.objects.filter(user=answer.author).first()
            avatar_url = profile.avatar.url if profile and profile.avatar \
                else '/media/profile_pics/default.jpg'
            answer.author_avatar_url = avatar_url
        else:
            answer.author_avatar_url = '/media/profile_pics/default.jpg'

        answer.comments = Comment.objects.filter(
            answer=answer
        ).select_related('author__profile').order_by('created_at')

        for comment in answer.comments:
            comment_votes = Vote.objects.filter(comment=comment)
            comment.likes = comment_votes.filter(vote_type=True).count()
            comment.dislikes = comment_votes.filter(vote_type=False).count()
            comment.rating = comment.likes - comment.dislikes

            if comment.author:
                profile = ProfileImage.objects.filter(user=comment.author).first()
                avatar_url = profile.avatar.url if profile and profile.avatar \
                    else '/media/profile_pics/default.jpg'
                comment.author_avatar_url = avatar_url
            else:
                comment.author_avatar_url = '/media/profile_pics/default.jpg'

    answer_form = AnswerForm()
    comment_form = CommentForm()
    logger.debug(f"Открыт вопрос {question_id}, ответов: {answers.count()}")

    context = {
        'question': question_obj,
        'answers': answers,
        'answer_form': answer_form,
        'comment_form': comment_form,
    }
    context.update(general_context(request))

    return render(request, 'question.html', context)


def get_user_rating(user):
    """Подсчёт общего рейтинга пользователя."""
    questions_rating = 0
    for question in Question.objects.filter(author=user):
        question_votes = Vote.objects.filter(
            question=question, answer__isnull=True, comment__isnull=True
        )
        likes = question_votes.filter(vote_type=True).count()
        dislikes = question_votes.filter(vote_type=False).count()
        questions_rating += (likes - dislikes)

    answers_rating = 0
    for answer in Answer.objects.filter(author=user):
        answer_votes = Vote.objects.filter(answer=answer, comment__isnull=True)
        likes = answer_votes.filter(vote_type=True).count()
        dislikes = answer_votes.filter(vote_type=False).count()
        answers_rating += (likes - dislikes)

    comments_rating = 0
    for comment in Comment.objects.filter(author=user):
        comment_votes = Vote.objects.filter(comment=comment)
        likes = comment_votes.filter(vote_type=True).count()
        dislikes = comment_votes.filter(vote_type=False).count()
        comments_rating += (likes - dislikes)

    return questions_rating + answers_rating + comments_rating


@login_required(login_url='/accounts/login/')
@require_POST
def delete_question(request, question_id):
    """
    Удаление вопроса.
    - Администратор может удалять любые вопросы
    - Доверенный участник (рейтинг ≥ 10) может удалять любые вопросы
    - Обычный пользователь может удалять только свои вопросы
    """
    question = get_object_or_404(Question, pk=question_id)

    if can_delete_content(request.user, question.author):
        question_title = question.title
        question.delete()
        logger.info(
            f"Пользователь {request.user.username} "
            f"удалил вопрос: '{question_title}' (ID: {question_id})"
        )
        return JsonResponse({
            'success': True,
            'message': 'Вопрос успешно удалён'
        })

    logger.warning(
        f"Пользователь {request.user.username} "
        f"попытался удалить вопрос {question_id} без прав"
    )
    return JsonResponse({
        'success': False,
        'message': 'У вас нет прав для удаления этого вопроса'
    }, status=403)


@login_required(login_url='/accounts/login/')
def profile(request, profile_id):
    """Страница профиля пользователя."""
    user_obj = User.objects.get(id=profile_id)
    profile, _ = ProfileImage.objects.get_or_create(user=user_obj)

    # Расчёт рейтинга пользователя
    questions_rating = 0
    for question in Question.objects.filter(author=user_obj):
        question_votes = Vote.objects.filter(
            question=question, answer__isnull=True, comment__isnull=True
        )
        likes = question_votes.filter(vote_type=True).count()
        dislikes = question_votes.filter(vote_type=False).count()
        questions_rating += (likes - dislikes)

    answers_rating = 0
    for answer in Answer.objects.filter(author=user_obj):
        answer_votes = Vote.objects.filter(answer=answer, comment__isnull=True)
        likes = answer_votes.filter(vote_type=True).count()
        dislikes = answer_votes.filter(vote_type=False).count()
        answers_rating += (likes - dislikes)

    comments_rating = 0
    for comment in Comment.objects.filter(author=user_obj):
        comment_votes = Vote.objects.filter(comment=comment)
        likes = comment_votes.filter(vote_type=True).count()
        dislikes = comment_votes.filter(vote_type=False).count()
        comments_rating += (likes - dislikes)

    total_rating = questions_rating + answers_rating + comments_rating

    # Определение роли
    if user_obj.is_staff:
        role = 'admin'
        role_name = 'Администратор'
    elif total_rating >= 10:
        role = 'trusted'
        role_name = 'Доверенный участник'
    else:
        role = 'user'
        role_name = 'Участник'

    questions_count = Question.objects.filter(author=user_obj).count()
    answers_count = Answer.objects.filter(author=user_obj).count()
    comments_count = Comment.objects.filter(author=user_obj).count()

    # Права на удаление
    can_delete = can_delete_content(request.user, user_obj) if request.user.is_authenticated else False
    is_admin = request.user.is_staff
    is_trusted = get_user_role(request.user) == 'trusted' if request.user.is_authenticated else False
    is_blocked = profile.is_blocked
    can_user_create = not is_blocked
    user_role = get_user_role(user_obj) if not user_obj.is_staff else 'admin'

    logger.debug(
        f"Открыт профиль пользователя: {user_obj.username}, "
        f"рейтинг: {total_rating}, роль: {role_name}"
    )

    context = {
        'user': user_obj,
        'profile': profile,
        'total_rating': total_rating,
        'questions_rating': questions_rating,
        'answers_rating': answers_rating,
        'comments_rating': comments_rating,
        'questions_count': questions_count,
        'answers_count': answers_count,
        'comments_count': comments_count,
        'is_admin': is_admin,
        'is_trusted': is_trusted,
        'role_name': role_name,
        'role': role,
        'user_role': user_role,
        'can_delete': can_delete,
        'is_blocked': is_blocked,
        'can_user_create': can_user_create,
    }
    context.update(general_context(request))

    return render(request, 'profile.html', context)


@login_required
def edit_profile(request):
    """Редактирование профиля пользователя."""
    if request.method == 'POST':
        form = ProfileForm(
            request.POST, request.FILES, instance=request.user.profile
        )
        if form.is_valid():
            form.save()
            logger.info(
                f"Пользователь {request.user.username} обновил профиль"
            )
            return redirect('profile', profile_id=request.user.id)
    else:
        form = ProfileForm(instance=request.user.profile)

    context = {'form': form}
    context.update(general_context(request))

    return render(request, 'edit_profile.html', context)


def user_login(request):
    """Страница входа пользователя."""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)

            if user is not None and user.is_active:
                # Проверка на блокировку
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

            logger.warning(
                f"Неудачная попытка входа для пользователя: {username}"
            )
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


@login_required(login_url='/accounts/login/')
def my_questions(request):
    """Страница "Моя активность"."""
    user = request.user

    user_questions = Question.objects.filter(author=user).order_by('-created_at')

    for question in user_questions:
        question.answers_count = Answer.objects.filter(question=question).count()
        tag_ids = [int(tag_id) for tag_id in question.tags.split(',') if tag_id]
        question.tag_objects = [
            get_tag_by_id(tag_id) for tag_id in tag_ids if get_tag_by_id(tag_id)
        ]

    user_answers = Answer.objects.filter(
        author=user
    ).select_related('question', 'question__author').order_by('-created_at')

    for answer in user_answers:
        answer_votes = Vote.objects.filter(answer=answer, comment__isnull=True)
        answer.likes = answer_votes.filter(vote_type=True).count()
        answer.dislikes = answer_votes.filter(vote_type=False).count()
        answer.rating = answer.likes - answer.dislikes

    logger.debug(
        f"Пользователь {user.username} открыл свои вопросы и ответы: "
        f"найдено вопросов - {user_questions.count()}, "
        f"ответов - {user_answers.count()}"
    )

    context = {
        'user': user,
        'questions': user_questions,
        'answers': user_answers,
        'user_role': get_user_role(user),
        'can_delete': can_delete_content(user, user),
    }
    context.update(general_context(request))

    return render(request, 'my-questions.html', context)