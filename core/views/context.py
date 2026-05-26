"""
Функции для создания общего контекста страниц.
"""

import logging
from django.db import models
from core.forms import SearchForm
from core.models import Question

logger = logging.getLogger(__name__)


def general_context(request):
    """Создаёт общий контекст для всех страниц."""
    search_form = SearchForm()
    context = {
        "menu": [["Задать вопрос", "/create_question"]],
        'sform': search_form
    }

    # Обработка POST запроса поиска (по подстроке)
    if request.method == "POST" and "title_search" in request.POST:
        title_search = request.POST.get('title_search')
        questions = Question.objects.filter(
            models.Q(title__icontains=title_search) |
            models.Q(text__icontains=title_search)
        )
        logger.info(
            f"Поиск по подстроке: '{title_search}', найдено: {questions.count()}"
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