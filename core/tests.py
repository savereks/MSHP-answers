from http.client import responses
import datetime

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse


class MainPage(TestCase):
    def setUp(self):
        self.client = Client()
        self.response = self.client.get('')

    def test_index_response(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, "menu")

    def test_index_context(self):
        self.assertEqual(self.response.context["menu"][0], ["Задать вопрос", "/create_question"])
        self.assertEqual(self.response.context["menu"][1], ['Войти', '/accounts/login/'])
        self.assertEqual(self.response.context["menu"][2], ['Регистрация', '/accounts/register/'])


class MainPageUser(TestCase):
    fixtures = [
        "db.json"
    ]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(username='Sania123')
        self.client.force_login(self.user)

        self.response = self.client.get('')

    def test_main_response_with_user(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, "<title>МШП Ответы</title>")
        self.assertEqual(self.response.context["menu"][1], ['Профиль', f'/accounts/profile/{self.user.id}'])
        self.assertIn('sform', self.response.context)

    def test_search_bar_success(self):
        self.response = self.client.post("", {"title_search":"Привет!"})
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.context["questions"][0].text, "Кто тут")

    def test_search_bar_tags(self):
        self.response = self.client.post("", {"title_search": "hurghiuegrhieurgh"})
        self.assertEqual(self.response.status_code, 200)
        # Проверяем, что у первого вопроса ровно 1 тег
        self.assertEqual(self.response.context["questions"][0].tags.count(), 2)

# Create your tests here.
