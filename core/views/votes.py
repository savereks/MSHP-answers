"""
Голосование за вопросы, ответы и комментарии.
"""

import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from core.models import Question, Answer, Comment, Vote

logger = logging.getLogger(__name__)


def _process_vote(existing_vote, vote_type):
    """Обрабатывает логику голосования."""
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            existing_vote.delete()
            return 'cancelled'
        else:
            existing_vote.vote_type = vote_type
            existing_vote.save()
            return 'changed'
    return 'created'


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

    _process_vote(existing_vote, vote_type)
    logger.info(
        f"Пользователь {request.user.username} "
        f"{'лайкнул' if vote_type else 'дизлайкнул'} вопрос {question_id}"
    )

    question_votes = Vote.objects.filter(
        question=question,
        answer__isnull=True,
        comment__isnull=True
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

    _process_vote(existing_vote, vote_type)
    logger.info(
        f"Пользователь {request.user.username} "
        f"{'лайкнул' if vote_type else 'дизлайкнул'} ответ {answer_id}"
    )

    answer_votes = Vote.objects.filter(
        answer=answer,
        comment__isnull=True
    )
    likes = answer_votes.filter(vote_type=True).count()
    dislikes = answer_votes.filter(vote_type=False).count()

    return JsonResponse({
        'likes': likes,
        'dislikes': dislikes,
        'rating': likes - dislikes
    })


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

    _process_vote(existing_vote, vote_type)
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