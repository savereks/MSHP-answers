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


def _process_vote(existing_vote, vote_type, user, **target):
    """
    Обрабатывает логику голосования.

    Args:
        existing_vote: Существующий голос или None
        vote_type: Тип голоса (True=лайк, False=дизлайк)
        user: Пользователь, который голосует
        **target: Цель голосования (question=..., answer=..., comment=...)

    Returns:
        str: Статус операции ('created', 'cancelled', 'changed')
    """
    if existing_vote is None:
        Vote.objects.create(user=user, vote_type=vote_type, **target)
        return 'created'
    if existing_vote.vote_type == vote_type:
        existing_vote.delete()
        return 'cancelled'
    existing_vote.vote_type = vote_type
    existing_vote.save()
    return 'changed'


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
        question=question
    ).first()

    _process_vote(
        existing_vote,
        vote_type,
        request.user,
        question=question
    )

    logger.info(
        f"Пользователь {request.user.username} "
        f"{'лайкнул' if vote_type else 'дизлайкнул'} вопрос {question_id}"
    )

    question_votes = Vote.objects.filter(question=question)
    likes = question_votes.filter(vote_type=True).count()
    dislikes = question_votes.filter(vote_type=False).count()
    rating = likes - dislikes

    logger.info(f"Вопрос {question_id}: лайков={likes}, дизлайков={dislikes}, рейтинг={rating}")

    return JsonResponse({
        'likes': likes,
        'dislikes': dislikes,
        'rating': rating
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
        answer=answer
    ).first()

    _process_vote(
        existing_vote,
        vote_type,
        request.user,
        answer=answer
    )

    logger.info(
        f"Пользователь {request.user.username} "
        f"{'лайкнул' if vote_type else 'дизлайкнул'} ответ {answer_id}"
    )

    answer_votes = Vote.objects.filter(answer=answer)
    likes = answer_votes.filter(vote_type=True).count()
    dislikes = answer_votes.filter(vote_type=False).count()
    rating = likes - dislikes

    logger.info(f"Ответ {answer_id}: лайков={likes}, дизлайков={dislikes}, рейтинг={rating}")

    return JsonResponse({
        'likes': likes,
        'dislikes': dislikes,
        'rating': rating
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

    _process_vote(
        existing_vote,
        vote_type,
        request.user,
        comment=comment
    )

    logger.info(
        f"Пользователь {request.user.username} "
        f"{'лайкнул' if vote_type else 'дизлайкнул'} комментарий {comment_id}"
    )

    comment_votes = Vote.objects.filter(comment=comment)
    likes = comment_votes.filter(vote_type=True).count()
    dislikes = comment_votes.filter(vote_type=False).count()
    rating = likes - dislikes

    logger.info(f"Комментарий {comment_id}: лайков={likes}, дизлайков={dislikes}, рейтинг={rating}")

    return JsonResponse({
        'likes': likes,
        'dislikes': dislikes,
        'rating': rating
    })