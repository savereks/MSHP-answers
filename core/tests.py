"""
Модуль тестирования для основного приложения.

Содержит тесты для проверки функциональности:
- Главная страница
- Создание вопросов и ответов
- Профили пользователей
- Регистрация и аутентификация
"""

from django.contrib.auth.models import User
from django.test import TestCase, Client


class MainPage(TestCase):
    """Тесты главной страницы для неавторизованного пользователя."""

    def setUp(self):
        """Настройка тестового клиента и выполнение GET запроса."""
        self.client = Client()
        self.response = self.client.get('')

    def test_index_response(self):
        """Проверка статуса ответа и наличия меню."""
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, "menu")

    def test_index_context(self):
        """Проверка контекста меню для неавторизованного пользователя."""
        menu_items = self.response.context["menu"]
        self.assertEqual(menu_items[0], ["Задать вопрос", "/create_question"])
        self.assertEqual(menu_items[1], ['Войти', '/accounts/login/'])
        self.assertEqual(menu_items[2], ['Регистрация', '/accounts/register/'])


class MainPageUser(TestCase):
    """Тесты главной страницы для авторизованного пользователя."""

    fixtures = ["db.json"]

    def setUp(self):
        """Настройка авторизованного пользователя и выполнение GET запроса."""
        self.client = Client()
        self.user = User.objects.get(username='Sania123')
        self.client.force_login(self.user)
        self.response = self.client.get('')

    def test_main_response_with_user(self):
        """Проверка ответа для авторизованного пользователя."""
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, "<title>МШП Ответы</title>")
        self.assertEqual(
            self.response.context["menu"][1],
            ['Профиль', f'/accounts/profile/{self.user.id}']
        )
        self.assertIn('sform', self.response.context)

    def test_search_bar_success(self):
        """Проверка успешного поиска по заголовку."""
        self.response = self.client.post("", {"title_search": "Привет!"})
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.context["questions"][0].text, "Кто тут")

    def test_search_bar_tags(self):
        """Проверка поиска с несуществующим запросом."""
        self.response = self.client.post("", {"title_search": "hurghiuegrhieurgh"})
        self.assertEqual(self.response.status_code, 200)
        # Проверяем, что у первого вопроса ровно 2 тега
        self.assertEqual(self.response.context["questions"][0].tags.count(), 2)


class CreateQuestion(TestCase):
    """Тесты создания нового вопроса."""

    fixtures = ["db.json"]

    def setUp(self):
        """Настройка клиента и выполнение GET запроса."""
        self.client = Client()
        self.response = self.client.get('/create_question/')

    def test_unsigned_user(self):
        """Проверка редиректа для неавторизованного пользователя."""
        self.assertEqual(self.response.status_code, 302)

    def test_question_creation(self):
        """Проверка успешного создания вопроса."""
        self.user = User.objects.get(username='Sania123')
        self.client.force_login(self.user)

        post_response = self.client.post(
            "/create_question/",
            {
                "title": "test_Question 123@$S",
                "text": "test text 123@$S",
                "tags": [1]
            }
        )
        self.assertEqual(post_response.status_code, 302)

        my_questions_response = self.client.get('/my-questions/')
        self.assertEqual(
            my_questions_response.context["menu"][1],
            ['Профиль', f'/accounts/profile/{self.user.id}']
        )
        self.assertContains(my_questions_response, "test_Question 123@$S")
        self.assertContains(my_questions_response, "Коты")


class TestQuestion(TestCase):
    """Тесты страницы вопроса."""

    fixtures = ["db.json"]

    def setUp(self):
        """Настройка клиента и выполнение GET запроса."""
        self.client = Client()
        self.response = self.client.get('/question/1/')

    def test_unsigned_user(self):
        """Проверка доступа неавторизованного пользователя."""
        self.assertEqual(self.response.status_code, 200)

    def test_question_answering(self):
        """Проверка добавления ответа авторизованным пользователем."""
        self.user = User.objects.get(username='Sania123')
        self.client.force_login(self.user)

        post_response = self.client.post("/question/1/", {"text": "test answer 123@$S"})
        self.assertEqual(post_response.status_code, 302)

        get_response = self.client.get('/question/1/')
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, "test answer 123@$S")
        self.assertContains(get_response, "Sania123")

    def test_question_answering_unsigned(self):
        """Проверка добавления ответа неавторизованным пользователем."""
        post_response = self.client.post("/question/1/", {"text": "test answer 123@$S"})
        self.assertEqual(post_response.status_code, 302)

        get_response = self.client.get('/question/1/')
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, "test answer 123@$S")
        self.assertContains(get_response, "Sania123")


class TestProfile(TestCase):
    """Тесты страницы профиля пользователя."""

    fixtures = ["db.json"]

    def setUp(self):
        """Настройка клиента и выполнение GET запроса."""
        self.client = Client()
        self.response = self.client.get('/accounts/profile/4/')

    def test_unsigned_user(self):
        """Проверка редиректа для неавторизованного пользователя."""
        self.assertEqual(self.response.status_code, 302)

    def test_profile_view(self):
        """Проверка отображения страницы профиля."""
        self.user = User.objects.get(username='Sania123')
        self.client.force_login(self.user)

        response = self.client.get('/accounts/profile/4/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Пользователь ещё не заполнил информацию о себе")
        self.assertContains(response, "Участник")
        self.assertContains(response, "Sania123")
        self.assertContains(response, "Sanioc@gmail.com")

    def test_profile_edit(self):
        """Проверка редактирования профиля."""
        self.user = User.objects.get(username='Sania123')
        self.client.force_login(self.user)

        get_response = self.client.get('/accounts/profile/edit/')
        self.assertEqual(get_response.status_code, 200)

        post_response = self.client.post(
            "/accounts/profile/edit/",
            {"bio": "test bio 123@$S"}
        )
        self.assertEqual(post_response.status_code, 302)

        profile_response = self.client.get('/accounts/profile/4/')
        self.assertContains(profile_response, "test bio 123@$S")


class TestRegister(TestCase):
    """Тесты регистрации новых пользователей."""

    fixtures = ["db.json"]

    def setUp(self):
        """Настройка клиента и выполнение GET запроса."""
        self.client = Client()
        self.response = self.client.get('/accounts/register/')

    def test_register_invalid(self):
        """Проверка регистрации с несовпадающими паролями."""
        self.assertEqual(self.response.status_code, 200)

        post_response = self.client.post(
            "/accounts/register/",
            {
                "username": "test_name_123@$S",
                "email": "test@test.com",
                "password1": "test password 123@$S",
                "password2": "test name 123@$S"
            },
            follow=True
        )
        self.assertEqual(post_response.status_code, 200)
        self.assertNotContains(post_response, "Участник")

    def test_register_valid(self):
        """Проверка успешной регистрации."""
        self.assertEqual(self.response.status_code, 200)

        post_response = self.client.post(
            "/accounts/register/",
            {
                "username": "Test_name_123@",
                "email": "test@test.com",
                "password1": "testpassword123@$S",
                "password2": "testpassword123@$S"
            },
            follow=True
        )
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, "Участник")
        self.assertContains(post_response, "Test_name_123@")


class TestLogin(TestCase):
    """Тесты входа в систему."""

    fixtures = ["db.json"]

    def setUp(self):
        """Настройка клиента и выполнение GET запроса."""
        self.client = Client()
        self.response = self.client.get('/accounts/register/')

    def test_login_with_new_account(self):
        """Проверка входа с новым аккаунтом."""
        self.user = User.objects.create_user(
            username="Test_name_123@",
            password="testpassword123@$S"
        )

        post_response = self.client.post(
            "/accounts/login/",
            {
                "username": "Test_name_123@",
                "password": "testpassword123@$S"
            },
            follow=True
        )
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, "Test_name_123@")
        self.assertContains(post_response, "Участник")