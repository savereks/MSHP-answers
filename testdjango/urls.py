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
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import main, calculator
import core.views as cv

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main),
    path('calculator/', calculator),
    path('accounts/profile/', cv.profile, name='profile'),
    path('accounts/login/', cv.user_login, name='login'),
    path('accounts/register/', cv.register, name='register'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('my-questions/', cv.my_questions, name='my-questions')
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
