"""
Профиль пользователя и его редактирование.
"""

import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.models import User, ProfileImage, Question, Answer, Comment, Vote
from core.forms import ProfileForm
from core.views.context import general_context
from core.views.utils import get_user_role, can_delete_content, get_user_rating

logger = logging.getLogger(__name__)


def _calculate_user_rating_stats(user_obj):
    """Рассчитывает статистику рейтинга пользователя."""
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

    return questions_rating, answers_rating, comments_rating


def _get_user_role_info(user_obj, total_rating):
    """Определяет роль пользователя на основе рейтинга."""
    if user_obj.is_staff:
        return 'admin', 'Администратор'
    elif total_rating >= 10:
        return 'trusted', 'Доверенный участник'
    return 'user', 'Участник'


@login_required(login_url='/accounts/login/')
def profile(request, profile_id):
    """Страница профиля пользователя."""
    user_obj = User.objects.get(id=profile_id)
    profile, _ = ProfileImage.objects.get_or_create(user=user_obj)

    questions_rating, answers_rating, comments_rating = _calculate_user_rating_stats(user_obj)
    total_rating = questions_rating + answers_rating + comments_rating

    role, role_name = _get_user_role_info(user_obj, total_rating)

    questions_count = Question.objects.filter(author=user_obj).count()
    answers_count = Answer.objects.filter(author=user_obj).count()
    comments_count = Comment.objects.filter(author=user_obj).count()

    can_delete = can_delete_content(request.user, user_obj) if request.user.is_authenticated else False
    is_admin = request.user.is_staff
    is_trusted = get_user_role(request.user) == 'trusted' if request.user.is_authenticated else False
    is_blocked = profile.is_blocked
    user_role = get_user_role(user_obj) if not user_obj.is_staff else 'admin'

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
        'can_user_create': not is_blocked,
    }
    context.update(general_context(request))
    return render(request, 'profile.html', context)


@login_required
def edit_profile(request):
    """Редактирование профиля пользователя."""
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            logger.info(f"Пользователь {request.user.username} обновил профиль")
            return redirect('profile', profile_id=request.user.id)
    else:
        form = ProfileForm(instance=request.user.profile)

    context = {'form': form}
    context.update(general_context(request))
    return render(request, 'edit_profile.html', context)