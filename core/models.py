"""
Модели данных для основного приложения.
Содержит все модели для работы с базой данных.
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class ProfileImage(models.Model):
    """
    Модель профиля пользователя.
    Хранит аватар, биографию и статус блокировки.
    """
    avatar = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg', blank=True, verbose_name="Аватар")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь")
    bio = models.TextField(max_length=500, blank=True, verbose_name="О себе")
    is_blocked = models.BooleanField(default=False, verbose_name="Заблокирован")

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"Профиль {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Автоматическое создание профиля при регистрации пользователя.
    """
    if created:
        ProfileImage.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Автоматическое сохранение профиля при сохранении пользователя.
    """
    instance.profile.save()


class Question(models.Model):
    """
    Модель вопроса.
    Содержит заголовок, текст, автора, дату создания и теги.
    """
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    text = models.TextField(verbose_name="Текст вопроса")
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    tags = models.CharField(max_length=500, blank=True, default='', verbose_name="Теги")

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ['-created_at']

    def get_tags_list(self):
        """Возвращает список тегов вопроса."""
        if self.tags:
            return self.tags.split(',')
        return []

    def set_tags_list(self, tags_list):
        """Устанавливает теги из списка."""
        self.tags = ','.join(tags_list) if tags_list else ''

    def __str__(self):
        return self.title


class Vote(models.Model):
    """
    Модель голосования.
    Универсальная модель для вопросов, ответов и комментариев.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name="Пользователь")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Вопрос")
    answer = models.ForeignKey('Answer', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Ответ")
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата голосования")
    vote_type = models.BooleanField(default=True, verbose_name="Тип голоса (True=лайк, False=дизлайк)")

    class Meta:
        verbose_name = "Голос"
        verbose_name_plural = "Голоса"
        unique_together = [['user', 'question'], ['user', 'answer'], ['user', 'comment']]

    def __str__(self):
        vote_text = "лайк" if self.vote_type else "дизлайк"
        if self.question:
            return f"{self.user.username} {vote_text} вопроса {self.question.id}"
        if self.answer:
            return f"{self.user.username} {vote_text} ответа {self.answer.id}"
        if self.comment:
            return f"{self.user.username} {vote_text} комментария {self.comment.id}"
        return f"{self.user.username} {vote_text}"


class Answer(models.Model):
    """
    Модель ответа на вопрос.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Вопрос")
    text = models.TextField(verbose_name="Текст ответа")
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Родительский ответ")

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"
        ordering = ['-created_at']

    def __str__(self):
        text_preview = self.text[:50] if len(self.text) > 50 else self.text
        return text_preview


class Comment(models.Model):
    """
    Модель комментария к ответу.
    """
    text = models.TextField(verbose_name="Текст комментария")
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name="Автор")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Вопрос")
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Ответ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Родительский комментарий")

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['created_at']

    def get_rating(self):
        """Получает рейтинг комментария."""
        votes = Vote.objects.filter(comment=self)
        likes = votes.filter(vote_type=True).count()
        dislikes = votes.filter(vote_type=False).count()
        return likes - dislikes

    def __str__(self):
        text_preview = self.text[:50] if len(self.text) > 50 else self.text
        author_name = self.author.username if self.author else "Неизвестный"
        return f"Комментарий от {author_name}: {text_preview}"