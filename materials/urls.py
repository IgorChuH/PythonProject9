from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet,
    LessonListCreateView,
    LessonRetrieveView,
    LessonUpdateView,
    LessonDestroyView,
    SubscriptionView
)

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")

urlpatterns = [
    path("", include(router.urls)),
    path("lessons/", LessonListCreateView.as_view(), name="lesson-list"),
    path("lessons/<int:pk>/", LessonRetrieveView.as_view(), name="lesson-detail"),
    path("lessons/<int:pk>/update/", LessonUpdateView.as_view(), name="lesson-update"),
    path("lessons/<int:pk>/delete/", LessonDestroyView.as_view(), name="lesson-delete"),
    path('subscription/', SubscriptionView.as_view(), name='subscription'),
]
