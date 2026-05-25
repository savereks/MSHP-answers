"""
Инициализация модуля views.
Экспортирует все основные функции для обратной совместимости.
"""

from core.views.auth import user_login, register
from core.views.context import general_context
from core.views.profile import profile, edit_profile
from core.views.questions import main, create_question, question_detail, my_questions
from core.views.answers import add_comment
from core.views.votes import vote_question, vote_answer, vote_comment
from core.views.admin_actions import delete_question, toggle_block_user
from core.views.utils import get_user_role, can_delete_content, can_create_content, get_user_rating

# Для обратной совместимости
question = question_detail

__all__ = [
    'user_login', 'register', 'general_context', 'profile', 'edit_profile',
    'main', 'create_question', 'question', 'question_detail', 'my_questions', 'add_comment',
    'vote_question', 'vote_answer', 'vote_comment', 'delete_question',
    'toggle_block_user', 'get_user_role', 'can_delete_content',
    'can_create_content', 'get_user_rating'
]