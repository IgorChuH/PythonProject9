from rest_framework import viewsets, generics, permissions, status
from rest_framework.reverse import reverse
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from materials.models import Lesson, Course
from .models import Payment
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import PaymentSerializer, MyTokenObtainPairSerializer, UserSerializer, PaymentResponseSerializer, \
    PaymentCreateSerializer
from .models import User
from .service import create_stripe_checkout_session, create_stripe_price, create_stripe_product


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['paid_course', 'paid_lesson', 'payment_method']
    ordering_fields = ['payment_date']
    ordering = ['-payment_date']


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer



class UserCreateView(generics.CreateAPIView):
    """Регистрация нового пользователя"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  # доступно всем

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Просмотр и редактирование профиля текущего пользователя"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


from django.http import HttpResponse

def payment_success(request):
    return HttpResponse("Оплата прошла успешно!")

def payment_cancel(request):
    return HttpResponse("Оплата отменена.")


class PaymentCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Определяем, что оплачивается: курс или урок
        course = None
        lesson = None
        if data.get('course_id'):
            course = Course.objects.get(id=data['course_id'])
            product_name = course.title
            product_description = course.description
        elif data.get('lesson_id'):
            lesson = Lesson.objects.get(id=data['lesson_id'])
            product_name = lesson.title
            product_description = lesson.description
        else:
            return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Создаём продукт в Stripe
        product_id = create_stripe_product(name=product_name, description=product_description)

        # 2. Создаём цену
        price_id = create_stripe_price(product_id=product_id, amount=data['amount'])

        # 3. Формируем URLs для успеха и отмены (можно заменить на свои)
        success_url = request.build_absolute_uri(reverse('payment-success'))  # нужно создать заглушки
        cancel_url = request.build_absolute_uri(reverse('payment-cancel'))

        # 4. Создаём сессию
        session_id, payment_url = create_stripe_checkout_session(price_id, success_url, cancel_url)

        # 5. Сохраняем платёж в БД
        payment = Payment.objects.create(
            user=request.user,
            paid_course=course,
            paid_lesson=lesson,
            amount=data['amount'],
            payment_method=data['payment_method'],
            stripe_product_id=product_id,
            stripe_price_id=price_id,
            stripe_session_id=session_id,
            payment_link=payment_url,
            status='pending'
        )

        # Возвращаем ответ с данными платежа (или просто ссылку)
        response_serializer = PaymentResponseSerializer(payment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)