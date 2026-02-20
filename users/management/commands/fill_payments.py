from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from materials.models import Course, Lesson
from users.models import Payment
import random
from datetime import datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Заполняет таблицу платежей тестовыми данными'

    def handle(self, *args, **options):
        # Очищаем существующие платежи (опционально)
        Payment.objects.all().delete()

        # Получаем или создаём пользователей (если их нет)
        users = list(User.objects.all())
        if not users:
            # Создадим тестового пользователя
            user = User.objects.create_user(
                email='test@example.com',
                password='password',
                phone='1234567890',
                city='Moscow'
            )
            users = [user]

        courses = list(Course.objects.all())
        lessons = list(Lesson.objects.all())

        # Если нет курсов и уроков, создадим хотя бы один курс
        if not courses:
            course = Course.objects.create(
                title='Тестовый курс',
                description='Описание тестового курса'
            )
            courses = [course]
            if not lessons:
                lesson = Lesson.objects.create(
                    title='Тестовый урок',
                    description='Описание тестового урока',
                    video_link='http://example.com',
                    course=course
                )
                lessons = [lesson]

        # Генерируем 20 случайных платежей
        for i in range(20):
            user = random.choice(users)
            amount = round(random.uniform(100, 10000), 2)
            payment_method = random.choice([Payment.PaymentMethod.CASH, Payment.PaymentMethod.TRANSFER])
            # Случайно выбираем: оплата курса или урока
            if random.choice([True, False]) and courses:
                paid_course = random.choice(courses)
                paid_lesson = None
            else:
                paid_course = None
                paid_lesson = random.choice(lessons) if lessons else None

            # Случайная дата за последние 30 дней
            payment_date = datetime.now() - timedelta(days=random.randint(0, 30))

            Payment.objects.create(
                user=user,
                payment_date=payment_date,
                paid_course=paid_course,
                paid_lesson=paid_lesson,
                amount=amount,
                payment_method=payment_method
            )

        self.stdout.write(self.style.SUCCESS('Успешно создано 20 тестовых платежей'))