from http.client import responses
import datetime

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from unittest import expectedFailure

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

class CreateQuestion(TestCase):
    fixtures = [
        "db.json"
    ]

    def setUp(self):
        self.client = Client()
        self.response = self.client.get('/create_question/')

    def test_unsigned_user(self):
        self.assertEqual(self.response.status_code, 302)

    def test_question_creation(self):
        self.user = User.objects.get(username='Sania123')
        self.client.force_login(self.user)
        self.response = self.client.post("/create_question/", {"title": "test_Question 123@$S", "text": "test text 123@$S", "tags":[1]})
        self.assertEqual(self.response.status_code, 302)
        self.response = self.client.get('/my-questions/')
        self.assertEqual(self.response.context["menu"][1], ['Профиль', f'/accounts/profile/{self.user.id}'])
        self.assertContains(self.response, "test_Question 123@$S")
        self.assertContains(self.response, "Коты")

class TestQuestion(TestCase):
    fixtures = [
        "db.json"
    ]

    def setUp(self):
        self.client = Client()
        self.response = self.client.get('/question/1/')

    def test_unsigned_user(self):
        self.assertEqual(self.response.status_code, 200)

    def test_question_answering(self):
        self.user = User.objects.get(username='Sania123')
        self.client.force_login(self.user)
        self.response = self.client.post("/question/1/", {"text": "test answer 123@$S"})
        self.assertEqual(self.response.status_code, 302)
        self.response = self.client.get('/question/1/')
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, "test answer 123@$S")
        self.assertContains(self.response, "Sania123")

    @expectedFailure
    def test_question_answering_unsigned(self):
        """
        Баг пока что ещё не исправлен
        """
        self.response = self.client.post("/question/1/", {"text": "test answer 123@$S"})
        self.assertEqual(self.response.status_code, 302)
        self.response = self.client.get('/question/1/')
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, "test answer 123@$S")
        self.assertContains(self.response, "Sania123")

class TestProfile(TestCase):
    fixtures = [
        "db.json"
    ]

    def setUp(self):
        self.client = Client()
        self.response = self.client.get('/accounts/profile/4/')

    def test_unsigned_user(self):
        self.assertEqual(self.response.status_code, 302)

    def test_profile_view(self):
        self.user = User.objects.get(username='Sania123')
        self.client.force_login(self.user)
        self.response = self.client.get('/accounts/profile/4/')
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, "Пользователь ещё не заполнил информацию о себе")
        self.assertContains(self.response, "Участник")
        self.assertContains(self.response, "Sania123")
        self.assertContains(self.response, "Sanioc@gmail.com")

    def test_profile_edit(self):
        self.user = User.objects.get(username='Sania123')
        self.client.force_login(self.user)
        self.response = self.client.get('/accounts/profile/edit/')
        self.assertEqual(self.response.status_code, 200)
        self.response = self.client.post("/accounts/profile/edit/", {"bio": "test bio 123@$S"})
        self.assertEqual(self.response.status_code, 302)
        self.response = self.client.get('/accounts/profile/4/')
        self.assertContains(self.response, "test bio 123@$S")

class TestRegister(TestCase):
    fixtures = [
        "db.json"
    ]

    def setUp(self):
        self.client = Client()
        self.response = self.client.get('/accounts/register/')

    def test_register_invalid(self):
        self.assertEqual(self.response.status_code, 200)
        self.response = self.client.post("/accounts/register/", {"username": "test_name_123@$S", "email": "test@test.com", "password1": "test password 123@$S", "password2": "test name 123@$S"}, follow=True)
        self.assertEqual(self.response.status_code, 200)
        self.assertNotContains(self.response, "Участник")

    def test_register_valid(self):
        self.assertEqual(self.response.status_code, 200)
        self.response = self.client.post("/accounts/register/", {"username": "Test_name_123@", "email": "test@test.com", "password1": "testpassword123@$S", "password2": "testpassword123@$S"}, follow=True)
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, "Участник")
        self.assertContains(self.response, "Test_name_123@")

class TestLogin(TestCase):
    fixtures = [
        "db.json"
    ]

    def setUp(self):
        self.client = Client()
        self.response = self.client.get('/accounts/register/')

    def test_login_with_new_account(self):
        self.user = User.objects.create_user(username="Test_name_123@", password="testpassword123@$S")
        self.response = self.client.post("/accounts/login/",
                                         {"username": "Test_name_123@", "password": "testpassword123@$S"},
                                         follow=True)
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, "Test_name_123@")
        self.assertContains(self.response, "Участник")