from django.utils import timezone

from celery import shared_task
from django.core.mail import send_mail
from drf_yasg.codecs import logger

from config import settings
from materials.models import Course, Subscription
from users.models import User


@shared_task
def send_course_update_notification(course_id=None):
    if course_id is None:
        # Логика для обработки всех курсов (или просто ничего не делаем)
        logger.info("Запущена задача send_course_update_notification без course_id")
        return

    course = Course.objects.get(id=course_id)
    subscribers = Subscription.objects.filter(course=course).select_related('user')
    recipient_list = [sub.user.email for sub in subscribers if sub.user.email]
    if recipient_list:
        send_mail(
            subject=f'Курс "{course.title}" обновлён',
            message=f'Здравствуйте! Курс "{course.title}" был обновлён. Зайдите на платформу, чтобы посмотреть новые материалы.',
            recipient_list=recipient_list,
            from_email=settings.DEFAULT_FROM_EMAIL,
            fail_silently=False,
        )



@shared_task
def deactivate_inactive_users():
    """
    Проверяет пользователей по дате последнего входа (last_login).
    Если пользователь не заходил более 30 дней, деактивирует его (is_active = False).
    """

    from datetime import timedelta
    month_ago = timezone.now() - timedelta(days=30)


    users_to_deactivate = User.objects.filter(
        last_login__lt=month_ago,
        is_active=True
    )

    count = users_to_deactivate.update(is_active=False)

    return f"Деактивировано пользователей: {count}"