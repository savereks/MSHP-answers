"""
URL configuration for testdjango project.

The `urlpatterns` list routes URLs to views.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path

import core.views as views
from core.views import create_question, edit_profile, main, vote_answer

urlpatterns = [
    # Административная панель
    path('admin/', admin.site.urls),

    # Основные страницы
    path('', main, name='main'),
    path('create_question/', create_question, name='create_question'),
    path('my-questions/', views.my_questions, name='my-questions'),

    # Работа с вопросами
    path('question/<int:question_id>/', views.question, name='question'),
    path('question/<int:question_id>/vote/', views.vote_question, name='vote_question'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),

    # Работа с ответами
    path('answer/<int:answer_id>/vote/', vote_answer, name='vote_answer'),
    path('answer/<int:answer_id>/comment/', views.add_comment, name='add_comment'),

    # Работа с комментариями
    path('comment/<int:comment_id>/vote/', views.vote_comment, name='vote_comment'),

    # Аутентификация и профили
    path('accounts/login/', views.user_login, name='login'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/profile/<int:profile_id>/', views.profile, name='profile'),
    path('accounts/profile/edit/', edit_profile, name='edit_profile'),
]

# Добавление URL для медиафайлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)