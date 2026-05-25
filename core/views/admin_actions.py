"""
Административные действия: удаление вопросов, блокировка пользователей.
"""

import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from core.models import Question, User, ProfileImage
from core.views.utils import can_delete_content

logger = logging.getLogger(__name__)


@login_required(login_url='/accounts/login/')
@require_POST
def delete_question(request, question_id):
    """Удаление вопроса (администратор, доверенный участник или автор)."""
    question = get_object_or_404(Question, pk=question_id)

    if can_delete_content(request.user, question.author):
        question_title = question.title
        question.delete()
        logger.info(f"Пользователь {request.user.username} удалил вопрос: '{question_title}' (ID: {question_id})")
        return JsonResponse({'success': True, 'message': 'Вопрос успешно удалён'})

    logger.warning(f"Пользователь {request.user.username} попытался удалить вопрос {question_id} без прав")
    return JsonResponse({'success': False, 'message': 'У вас нет прав для удаления этого вопроса'}, status=403)


@login_required(login_url='/accounts/login/')
@require_POST
def toggle_block_user(request, user_id):
    """Блокировка/разблокировка пользователя (только для администратора)."""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Недостаточно прав'}, status=403)

    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = ProfileImage.objects.get_or_create(user=target_user)
    profile.is_blocked = not profile.is_blocked
    profile.save()

    status_text = "заблокирован" if profile.is_blocked else "разблокирован"
    logger.info(f"Администратор {request.user.username} {status_text} пользователя {target_user.username}")

    return JsonResponse({'success': True, 'is_blocked': profile.is_blocked, 'message': f'Пользователь {status_text}'})