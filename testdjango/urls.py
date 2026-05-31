"""
URL configuration for testdjango project.

The `urlpatterns` list routes URLs to views.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path
from django.urls import re_path
from django.views.static import serve

import core.views as views

urlpatterns = [
    # Административная панель
    path('admin/', admin.site.urls),

    # Основные страницы
    path('', views.main, name='main'),
    path('create_question/', views.create_question, name='create_question'),
    path('my-questions/', views.my_questions, name='my-questions'),

    # Работа с вопросами
    path('question/<int:question_id>/', views.question, name='question'),
    path('question/<int:question_id>/vote/', views.vote_question, name='vote_question'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),

    # Работа с ответами
    path('answer/<int:answer_id>/vote/', views.vote_answer, name='vote_answer'),
    path('answer/<int:answer_id>/comment/', views.add_comment, name='add_comment'),

    # Работа с комментариями
    path('comment/<int:comment_id>/vote/', views.vote_comment, name='vote_comment'),

    # Аутентификация и профили
    path('accounts/login/', views.user_login, name='login'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/profile/<int:profile_id>/', views.profile, name='profile'),
    path('accounts/profile/edit/', views.edit_profile, name='edit_profile'),

    # Административные действия
    path('user/<int:user_id>/toggle-block/', views.toggle_block_user, name='toggle_block_user'),
]

# Добавление URL для медиафайлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Принудительная раздача медиа-файлов при выключенном DEBUG (для локальной проверки и Render)
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]