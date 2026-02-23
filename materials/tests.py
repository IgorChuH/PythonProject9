from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from rest_framework import status
from .models import Course, Lesson, Subscription
from users.models import User


class LessonTestCase(TestCase):
    def setUp(self):
        # Создаём группу модераторов (если ещё не создана в БД)
        self.moderator_group, _ = Group.objects.get_or_create(name='Moderators')

        # Обычный пользователь
        self.user = User.objects.create_user(
            email='user@test.com',
            password='password',
            phone='1234567890',
            city='Moscow'
        )
        # Модератор
        self.moderator = User.objects.create_user(
            email='moderator@test.com',
            password='password'
        )
        self.moderator.groups.add(self.moderator_group)

        # Ещё один пользователь (владелец другого курса)
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='password'
        )

        # Создаём курс (владелец – self.user)
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            owner=self.user
        )

        # Урок этого курса
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            description='Lesson Description',
            video_link='https://youtube.com/watch?v=123',
            course=self.course,
            owner=self.user
        )

        # Клиенты для аутентификации
        self.client = APIClient()
        self.user_client = APIClient()
        self.user_client.force_authenticate(user=self.user)
        self.moderator_client = APIClient()
        self.moderator_client.force_authenticate(user=self.moderator)
        self.other_client = APIClient()
        self.other_client.force_authenticate(user=self.other_user)

    def test_create_lesson_valid_link(self):
        """Создание урока с допустимой youtube-ссылкой должно проходить"""
        data = {
            'title': 'New Lesson',
            'description': 'New Description',
            'video_link': 'https://youtu.be/abc123',
            'course': self.course.id
        }
        response = self.user_client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)
        self.assertEqual(Lesson.objects.last().owner, self.user)

    def test_create_lesson_invalid_link(self):
        """Создание урока с ссылкой не на YouTube должно возвращать ошибку"""
        data = {
            'title': 'New Lesson',
            'description': 'New Description',
            'video_link': 'https://vimeo.com/123',
            'course': self.course.id
        }
        response = self.user_client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('video_link', response.data)

    def test_create_lesson_by_moderator_forbidden(self):
        """Модератор не может создавать уроки"""
        data = {
            'title': 'Moderator Lesson',
            'description': 'Should be forbidden',
            'video_link': 'https://youtube.com/watch?v=456',
            'course': self.course.id
        }
        response = self.moderator_client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_list_pagination(self):
        """Проверка, что пагинация работает и возвращается правильная структура"""
        # Создадим дополнительные уроки
        for i in range(7):
            Lesson.objects.create(
                title=f'Lesson {i}',
                description='',
                video_link='https://youtube.com',
                course=self.course,
                owner=self.user
            )
        response = self.user_client.get('/api/lessons/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(len(response.data['results']), 5)

    def test_update_lesson_by_owner(self):
        """Владелец может обновить свой урок"""
        data = {'title': 'Updated Title'}
        response = self.user_client.patch(f'/api/lessons/{self.lesson.id}/update/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, 'Updated Title')

    def test_update_lesson_by_moderator(self):
        """Модератор может обновить любой урок"""
        data = {'title': 'Moderator Updated'}
        response = self.moderator_client.patch(f'/api/lessons/{self.lesson.id}/update/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, 'Moderator Updated')

    def test_update_lesson_by_other_user_forbidden(self):
        """Другой пользователь (не владелец, не модератор) не может обновить урок"""
        data = {'title': 'Other Update'}
        response = self.other_client.patch(f'/api/lessons/{self.lesson.id}/update/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_lesson_by_owner(self):
        """Владелец может удалить свой урок"""
        response = self.user_client.delete(f'/api/lessons/{self.lesson.id}/delete/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_delete_lesson_by_moderator_forbidden(self):
        """Модератор не может удалить урок"""
        response = self.moderator_client.delete(f'/api/lessons/{self.lesson.id}/delete/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubscriptionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@test.com', password='password')
        self.course = Course.objects.create(title='Test Course', description='...', owner=self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_subscribe_and_unsubscribe(self):
        """Проверка добавления и удаления подписки через эндпоинт subscription/"""
        # Подписываемся
        response = self.client.post('/api/subscription/', {'course_id': self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'подписка добавлена')
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course).exists())

        # Отписываемся (повторный запрос)
        response = self.client.post('/api/subscription/', {'course_id': self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'подписка удалена')
        self.assertFalse(Subscription.objects.filter(user=self.user, course=self.course).exists())

    def test_is_subscribed_field_in_course(self):
        """Поле is_subscribed в сериализаторе курса должно правильно отображаться"""
        # Сначала без подписки
        response = self.client.get(f'/api/courses/{self.course.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_subscribed'])

        # Подписываемся
        Subscription.objects.create(user=self.user, course=self.course)
        response = self.client.get(f'/api/courses/{self.course.id}/')
        self.assertTrue(response.data['is_subscribed'])


