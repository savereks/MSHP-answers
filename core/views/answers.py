"""
Работа с ответами и комментариями к вопросам.
"""

import logging
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from core.forms import CommentForm
from core.models import Answer, ProfileImage, Vote, Comment
from core.constants import get_tag_by_id

logger = logging.getLogger(__name__)


def load_question_details(question_obj):
    """Загружает детали вопроса: рейтинг, аватар, теги."""
    from core.models import Vote, ProfileImage
    from core.constants import get_tag_by_id

    question_votes = Vote.objects.filter(
        question=question_obj,
        answer__isnull=True,
        comment__isnull=True
    )
    question_obj.likes = question_votes.filter(vote_type=True).count()
    question_obj.dislikes = question_votes.filter(vote_type=False).count()
    question_obj.rating = question_obj.likes - question_obj.dislikes

    if question_obj.author:
        profile = ProfileImage.objects.filter(user=question_obj.author).first()
        avatar_url = (
            profile.avatar.url
            if profile and profile.avatar
            else '/media/profile_pics/default.jpg'
        )
        question_obj.author_avatar_url = avatar_url
    else:
        question_obj.author_avatar_url = '/media/profile_pics/default.jpg'

    tag_ids = [
        int(tag_id) for tag_id in question_obj.tags.split(',') if tag_id
    ]
    question_obj.tag_objects = [
        get_tag_by_id(tag_id) for tag_id in tag_ids if get_tag_by_id(tag_id)
    ]


def load_answer_details(answer):
    """Загружает детали ответа: рейтинг, аватар, комментарии."""
    from core.models import Vote, ProfileImage, Comment

    answer_votes = Vote.objects.filter(
        answer=answer,
        comment__isnull=True
    )
    answer.likes = answer_votes.filter(vote_type=True).count()
    answer.dislikes = answer_votes.filter(vote_type=False).count()
    answer.rating = answer.likes - answer.dislikes

    if answer.author:
        profile = ProfileImage.objects.filter(user=answer.author).first()
        avatar_url = (
            profile.avatar.url
            if profile and profile.avatar
            else '/media/profile_pics/default.jpg'
        )
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
            avatar_url = (
                profile.avatar.url
                if profile and profile.avatar
                else '/media/profile_pics/default.jpg'
            )
            comment.author_avatar_url = avatar_url
        else:
            comment.author_avatar_url = '/media/profile_pics/default.jpg'


def load_answers_with_details(answers):
    """Загружает детали для списка ответов."""
    for answer in answers:
        load_answer_details(answer)


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