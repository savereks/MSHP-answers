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
    Хранит аватар и биографию.
    """
    objects = None
    avatar = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg', blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)


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
    title = models.CharField(max_length=200)
    text = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.CharField(max_length=500, blank=True, default='')

    def get_tags_list(self):
        """Возвращает список тегов вопроса"""
        if self.tags:
            return self.tags.split(',')
        return []

    def set_tags_list(self, tags_list):
        """Устанавливает теги из списка"""
        self.tags = ','.join(tags_list) if tags_list else ''

    def __str__(self):
        return self.title


class Vote(models.Model):
    """
    Модель голосования.
    Универсальная модель для вопросов, ответов и комментариев.
    """
    objects = None
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True)
    answer = models.ForeignKey('Answer', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    vote_type = models.BooleanField(default=True)

    class Meta:
        unique_together = [['user', 'question'], ['user', 'answer'], ['user', 'comment']]


class Answer(models.Model):
    """
    Модель ответа на вопрос.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.text


class Comment(models.Model):
    """
    Модель комментария к ответу.
    """
    text = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True)
    answer = models.ForeignKey('Answer', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)  # Для вложенных комментариев

    def __str__(self):
        return self.text[:50]

    def get_rating(self):
        """Получить рейтинг комментария"""
        votes = Vote.objects.filter(comment=self)
        likes = votes.filter(vote_type=True).count()
        dislikes = votes.filter(vote_type=False).count()
        return likes - dislikes

