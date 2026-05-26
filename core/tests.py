"""
Модуль тестирования для основного приложения.
Содержит тесты для проверки функциональности.
"""

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from core.models import Question, Answer, Comment, Vote, ProfileImage
from core.constants import ALL_TAGS, get_tag_by_id, get_tag_by_name, get_all_tags


class MainPage(TestCase):
    """Тесты главной страницы."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='Sania123', password='testpass')
        self.response = self.client.get('')

    def test_index_response(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, "menu")

    def test_index_context(self):
        menu_items = self.response.context["menu"]
        self.assertEqual(menu_items[0], ["Задать вопрос", "/create_question"])
        self.assertEqual(menu_items[1], ['Войти', '/accounts/login/'])

    def test_main_response_with_user(self):
        self.client.force_login(self.user)
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["menu"][1], ['Профиль', f'/accounts/profile/{self.user.id}'])

    def test_search_bar_success(self):
        Question.objects.create(title="Привет!", text="Кто тут", author=self.user, tags="")
        response = self.client.post("", {"title_search": "Привет!"})
        self.assertEqual(response.status_code, 200)

    def test_main_page_with_tags_filter(self):
        Question.objects.create(title="Test", text="Content", author=self.user, tags="1")
        response = self.client.get('/', {'tags': ['1']})
        self.assertEqual(response.status_code, 200)


class TestConstants(TestCase):
    """Тесты для constants.py."""

    def test_all_tags_contains_expected_tags(self):
        expected_names = ['Python', 'Django', 'JavaScript', 'React', 'Vue.js', 'HTML/CSS', 'SQL', 'PostgreSQL', 'Git', 'Docker', 'Linux', 'API', 'Machine Learning', 'Flask', 'FastAPI']
        tag_names = [tag['name'] for tag in ALL_TAGS]
        for name in expected_names:
            self.assertIn(name, tag_names)

    def test_get_tag_by_id(self):
        self.assertEqual(get_tag_by_id(1)['name'], 'Python')
        self.assertIsNone(get_tag_by_id(999))

    def test_get_tag_by_name(self):
        self.assertEqual(get_tag_by_name('django')['id'], 2)
        self.assertIsNone(get_tag_by_name('NonExistent'))


class TestAuth(TestCase):
    """Тесты аутентификации и регистрации."""

    def setUp(self):
        self.client = Client()
        self.user_data = {'username': 'testuser', 'email': 'test@example.com', 'password1': 'SecurePass123!', 'password2': 'SecurePass123!'}

    def test_register_valid(self):
        response = self.client.post("/accounts/register/", self.user_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "testuser")

    def test_register_invalid(self):
        response = self.client.post("/accounts/register/", {"username": "a", "password1": "1", "password2": "2"})
        self.assertEqual(response.status_code, 200)

    def test_login_valid(self):
        User.objects.create_user(username='loginuser', password='pass123')
        response = self.client.post("/accounts/login/", {"username": "loginuser", "password": "pass123"}, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_login_blocked_user(self):
        user = User.objects.create_user(username='blocked', password='pass123')
        profile, _ = ProfileImage.objects.get_or_create(user=user)
        profile.is_blocked = True
        profile.save()
        response = self.client.post("/accounts/login/", {"username": "blocked", "password": "pass123"}, follow=True)
        self.assertContains(response, "заблокирован")

    def test_register_creates_profile(self):
        self.client.post("/accounts/register/", self.user_data)
        user = User.objects.get(username='testuser')
        self.assertTrue(ProfileImage.objects.filter(user=user).exists())


class TestAnswers(TestCase):
    """Тесты для answers.py."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='commenter', password='pass')
        self.author = User.objects.create_user(username='author', password='pass')
        self.question = Question.objects.create(title="Test Q", text="Content", author=self.author, tags="1")
        self.answer = Answer.objects.create(question=self.question, text="Answer", author=self.author)
        self.client.force_login(self.user)

    def test_add_comment_valid(self):
        response = self.client.post(reverse('add_comment', args=[self.answer.id]), {"text": "Nice!"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(text="Nice!").exists())

    def test_add_comment_invalid(self):
        response = self.client.post(reverse('add_comment', args=[self.answer.id]), {"text": ""})
        self.assertFalse(Comment.objects.filter(text="").exists())

    def test_load_question_details(self):
        from core.views.answers import load_question_details
        load_question_details(self.question)
        self.assertTrue(hasattr(self.question, 'rating'))

    def test_load_answer_details(self):
        from core.views.answers import load_answer_details
        load_answer_details(self.answer)
        self.assertTrue(hasattr(self.answer, 'likes'))


class TestCreateQuestion(TestCase):
    """Тесты создания вопросов."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='creator', password='pass')
        self.client.force_login(self.user)

    def test_create_question_get(self):
        response = self.client.get('/create_question/')
        self.assertEqual(response.status_code, 200)

    def test_create_question_post(self):
        response = self.client.post('/create_question/', {"title": "New Q", "text": "Text", "tags": ["1"]})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Question.objects.filter(title="New Q").exists())

    def test_blocked_user_cannot_create(self):
        profile, _ = ProfileImage.objects.get_or_create(user=self.user)
        profile.is_blocked = True
        profile.save()
        response = self.client.post('/create_question/', {"title": "Blocked", "text": "Text", "tags": []})
        self.assertFalse(Question.objects.filter(title="Blocked").exists())


class TestQuestionDetail(TestCase):
    """Тесты страницы вопроса."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='pass')
        self.author = User.objects.create_user(username='author', password='pass')
        self.question = Question.objects.create(title="Test", text="Content", author=self.author, tags="")

    def test_question_detail_get(self):
        response = self.client.get(f'/question/{self.question.id}/')
        self.assertEqual(response.status_code, 200)

    def test_question_detail_post_answer(self):
        self.client.force_login(self.user)
        response = self.client.post(f'/question/{self.question.id}/', {"text": "New answer"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Answer.objects.filter(text="New answer").exists())


class TestProfile(TestCase):
    """Тесты профиля."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='profileuser', password='pass', email='test@test.com')

    def test_profile_view_requires_login(self):
        response = self.client.get(f'/accounts/profile/{self.user.id}/')
        self.assertEqual(response.status_code, 302)

    def test_profile_view_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(f'/accounts/profile/{self.user.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "profileuser")

    def test_profile_edit(self):
        self.client.force_login(self.user)
        response = self.client.post("/accounts/profile/edit/", {"bio": "New bio"})
        self.assertEqual(response.status_code, 302)


class TestVoting(TestCase):
    """Тесты голосования."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='voter', password='pass')
        self.author = User.objects.create_user(username='author', password='pass')
        self.question = Question.objects.create(title="Test", text="Content", author=self.author, tags="")
        self.answer = Answer.objects.create(question=self.question, text="Answer", author=self.author)
        self.client.force_login(self.user)

    def test_vote_question_like(self):
        response = self.client.post(reverse('vote_question', args=[self.question.id]), {"vote": "like"})
        self.assertEqual(response.json()["likes"], 1)

    def test_vote_question_dislike(self):
        response = self.client.post(reverse('vote_question', args=[self.question.id]), {"vote": "dislike"})
        self.assertEqual(response.json()["dislikes"], 1)

    def test_vote_answer(self):
        response = self.client.post(reverse('vote_answer', args=[self.answer.id]), {"vote": "like"})
        self.assertEqual(response.json()["likes"], 1)

    def test_cancel_vote(self):
        self.client.post(reverse('vote_question', args=[self.question.id]), {"vote": "like"})
        response = self.client.post(reverse('vote_question', args=[self.question.id]), {"vote": "like"})
        self.assertEqual(response.json()["likes"], 0)


class TestAdminActions(TestCase):
    """Тесты административных действий."""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin', password='pass')
        self.user = User.objects.create_user(username='regular', password='pass')
        self.question = Question.objects.create(title="To delete", text="Content", author=self.user, tags="")

    def test_admin_can_delete_question(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('delete_question', args=[self.question.id]))
        self.assertTrue(response.json()["success"])
        self.assertFalse(Question.objects.filter(id=self.question.id).exists())

    def test_toggle_block_user(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('toggle_block_user', args=[self.user.id]))
        self.assertTrue(response.json()["is_blocked"])


class TestMyQuestions(TestCase):
    """Тесты страницы 'Моя активность'."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='active', password='pass')
        self.question = Question.objects.create(title="My Q", text="Content", author=self.user, tags="1,2")
        self.client.force_login(self.user)

    def test_my_questions_page(self):
        response = self.client.get('/my-questions/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Q")

    def test_my_questions_requires_login(self):
        self.client.logout()
        response = self.client.get('/my-questions/')
        self.assertEqual(response.status_code, 302)


class TestPermissions(TestCase):
    """Тесты прав доступа."""

    def test_regular_user_cannot_delete_others_content(self):
        client = Client()
        user = User.objects.create_user(username='regular', password='pass')
        other = User.objects.create_user(username='other', password='pass')
        question = Question.objects.create(title="Other Q", text="Content", author=other, tags="")
        client.force_login(user)
        response = client.post(reverse('delete_question', args=[question.id]))
        self.assertEqual(response.status_code, 403)


class TestSearch(TestCase):
    """Тесты поиска."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='searcher', password='pass')
        Question.objects.create(title="Python tutorial", text="Learn Django", author=self.user, tags="")
        Question.objects.create(title="JavaScript basics", text="JS for beginners", author=self.user, tags="")

    def test_search_by_title(self):
        response = self.client.get("/", {"q": "Python"})
        self.assertEqual(len(response.context["questions"]), 1)

    def test_search_no_results(self):
        response = self.client.get("/", {"q": "nonexistent"})
        self.assertEqual(len(response.context["questions"]), 0)


class TestUtils(TestCase):
    """Тесты вспомогательных функций."""

    def setUp(self):
        self.user = User.objects.create_user(username='helper', password='pass')

    def test_get_user_role(self):
        from core.views.utils import get_user_role
        self.assertIn(get_user_role(self.user), ["user", "trusted", "admin"])

    def test_can_delete_content(self):
        from core.views.utils import can_delete_content
        self.assertTrue(can_delete_content(self.user, self.user))

    def test_can_create_content(self):
        from core.views.utils import can_create_content
        self.assertTrue(can_create_content(self.user))


# CI/CD интеграция
if __name__ == "__main__":
    import sys, django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'core'],
        MIDDLEWARE=[],
        SECRET_KEY='test-key',
    )
    django.setup()
    from django.test.runner import DiscoverRunner
    sys.exit(DiscoverRunner(verbosity=2, interactive=False).run_tests(['core']))