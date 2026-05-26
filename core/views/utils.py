"""
Вспомогательные функции для определения прав и ролей пользователей.
"""

from core.models import Question, Answer, Vote, Comment, ProfileImage


def get_user_role(user):
    """
    Определяет роль пользователя на основе рейтинга.
    Возвращает: 'admin', 'trusted', 'user'
    """
    if user.is_staff:
        return 'admin'

    total_rating = 0
    for question in Question.objects.filter(author=user):
        # Убраны лишние фильтры
        question_votes = Vote.objects.filter(question=question)
        likes = question_votes.filter(vote_type=True).count()
        dislikes = question_votes.filter(vote_type=False).count()
        total_rating += (likes - dislikes)

    for answer in Answer.objects.filter(author=user):
        # Убраны лишние фильтры
        answer_votes = Vote.objects.filter(answer=answer)
        likes = answer_votes.filter(vote_type=True).count()
        dislikes = answer_votes.filter(vote_type=False).count()
        total_rating += (likes - dislikes)

    for comment in Comment.objects.filter(author=user):
        comment_votes = Vote.objects.filter(comment=comment)
        likes = comment_votes.filter(vote_type=True).count()
        dislikes = comment_votes.filter(vote_type=False).count()
        total_rating += (likes - dislikes)

    return 'trusted' if total_rating >= 10 else 'user'


def can_delete_content(user, content_author):
    """
    Проверяет, может ли пользователь удалить контент.
    - Администратор и доверенный участник (рейтинг ≥ 10) могут удалять любые вопросы
    - Обычный пользователь может удалять только свои вопросы
    """
    if user.is_staff:
        return True
    if get_user_role(user) == 'trusted':
        return True
    return user == content_author


def can_create_content(user):
    """Проверяет, может ли пользователь создавать контент (не заблокирован)."""
    try:
        profile = ProfileImage.objects.get(user=user)
        return not profile.is_blocked
    except ProfileImage.DoesNotExist:
        return True


def get_user_rating(user):
    """Подсчёт общего рейтинга пользователя."""
    questions_rating = 0
    for question in Question.objects.filter(author=user):
        # Убраны лишние фильтры
        question_votes = Vote.objects.filter(question=question)
        likes = question_votes.filter(vote_type=True).count()
        dislikes = question_votes.filter(vote_type=False).count()
        questions_rating += (likes - dislikes)

    answers_rating = 0
    for answer in Answer.objects.filter(author=user):
        # Убраны лишние фильтры
        answer_votes = Vote.objects.filter(answer=answer)
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