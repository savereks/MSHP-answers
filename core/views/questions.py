"""
Работа с вопросами: главная страница, создание, просмотр.
"""

import logging
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.constants import ALL_TAGS, get_tag_by_id
from core.forms import QuestionForm, AnswerForm, CommentForm
from core.models import Question, Answer, ProfileImage, Vote, Comment
from core.views.context import general_context
from core.views.utils import get_user_role, can_delete_content
from core.views.answers import load_question_details, load_answers_with_details

logger = logging.getLogger(__name__)


def _load_avatars_for_questions(questions):
    """Загружает аватары для списка вопросов."""
    author_ids = {q.author_id for q in questions if q.author_id}
    avatar_by_user = {}

    if author_ids:
        for img in ProfileImage.objects.filter(user_id__in=author_ids).select_related('user'):
            if img.avatar:
                avatar_by_user[img.user_id] = img.avatar.url

    for question in questions:
        question_votes = Vote.objects.filter(
            question=question, answer__isnull=True, comment__isnull=True
        )
        question.likes = question_votes.filter(vote_type=True).count()
        question.dislikes = question_votes.filter(vote_type=False).count()
        question.rating = question.likes - question.dislikes
        question.author_avatar_url = avatar_by_user.get(question.author_id, '/media/profile_pics/default.jpg')

        tag_ids = [int(tag_id) for tag_id in question.tags.split(',') if tag_id]
        question.tag_objects = [get_tag_by_id(tag_id) for tag_id in tag_ids if get_tag_by_id(tag_id)]


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

    # Поиск по подстроке в заголовке или тексте вопроса
    if search_query:
        queryset = queryset.filter(
            models.Q(title__icontains=search_query) |
            models.Q(text__icontains=search_query)
        )
        logger.info(f"Поиск по подстроке через GET: '{search_query}'")

    if selected_tags:
        for tag_id in selected_tags:
            tag = get_tag_by_id(tag_id)
            if tag:
                queryset = queryset.filter(tags__contains=str(tag_id))

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
    context['user_role'] = get_user_role(request.user) if request.user.is_authenticated else None

    return render(request, 'index.html', context)


@login_required(login_url='/accounts/login/')
def create_question(request):
    """Создание нового вопроса."""
    profile = ProfileImage.objects.get(user=request.user)
    if profile.is_blocked:
        context = {'error': 'Ваш аккаунт заблокирован. Вы не можете создавать вопросы.'}
        context.update(general_context(request))
        return render(request, "create_question.html", context)

    if request.method == "POST":
        title = request.POST.get('title')
        text = request.POST.get('text')
        tags = request.POST.getlist('tags')
        tags_str = ','.join(tags) if tags else ''

        new_question = Question(title=title, text=text, author=request.user, tags=tags_str)
        new_question.save()
        logger.info(f"Пользователь {request.user.username} создал вопрос: '{title}'")
        return redirect('/')

    form = QuestionForm()
    context = {'form': form}
    context.update(general_context(request))
    return render(request, "create_question.html", context)


def question_detail(request, question_id):
    """Страница просмотра вопроса с ответами и комментариями."""
    if request.method == 'POST':
        answer_form = AnswerForm(request.POST)
        if answer_form.is_valid() and request.user.is_authenticated:
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
            logger.info(f"Пользователь {request.user.username} добавил ответ на вопрос {question_id}")
        return redirect(f'/question/{question_id}/')

    # GET запрос - отображение страницы
    question_obj = Question.objects.get(id=question_id)
    load_question_details(question_obj)

    answers = Answer.objects.filter(question=question_obj).select_related('author__profile')
    load_answers_with_details(answers)

    context = {
        'question': question_obj,
        'answers': answers,
        'answer_form': AnswerForm(),
        'comment_form': CommentForm(),
    }
    context.update(general_context(request))
    return render(request, 'question.html', context)


@login_required(login_url='/accounts/login/')
def my_questions(request):
    """Страница 'Моя активность'."""
    user = request.user

    user_questions = Question.objects.filter(author=user).order_by('-created_at')
    for question in user_questions:
        question.answers_count = Answer.objects.filter(question=question).count()
        tag_ids = [int(tag_id) for tag_id in question.tags.split(',') if tag_id]
        question.tag_objects = [get_tag_by_id(tag_id) for tag_id in tag_ids if get_tag_by_id(tag_id)]

    user_answers = Answer.objects.filter(author=user).select_related('question').order_by('-created_at')
    for answer in user_answers:
        answer_votes = Vote.objects.filter(answer=answer, comment__isnull=True)
        answer.likes = answer_votes.filter(vote_type=True).count()
        answer.dislikes = answer_votes.filter(vote_type=False).count()
        answer.rating = answer.likes - answer.dislikes

    context = {
        'user': user,
        'questions': user_questions,
        'answers': user_answers,
        'user_role': get_user_role(user),
        'can_delete': can_delete_content(user, user),
    }
    context.update(general_context(request))
    return render(request, 'my-questions.html', context)