"""
URL configuration for testdjango project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from core.views import main, create_question, edit_profile, vote_answer
from django.contrib.auth.views import LogoutView
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
import core.views as cv


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main, name='main'),
    path('accounts/profile/<int:profile_id>/', cv.profile, name='profile'),
    path('accounts/profile/edit/', cv.edit_profile, name='edit_profile'),
    path('accounts/login/', cv.user_login, name='login'),
    path('accounts/register/', cv.register, name='register'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('my-questions/', cv.my_questions, name='my-questions'),
    path('create_question/', create_question),
    path('question/<int:question_id>/', cv.question, name='question'),
    path('question/<int:question_id>/vote/',cv.vote_question,name='vote_question',),
    path('answer/<int:answer_id>/vote/', cv.vote_answer, name='vote_answer'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
