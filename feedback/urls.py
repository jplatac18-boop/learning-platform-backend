from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommentViewSet, CourseRatingViewSet

router = DefaultRouter()
router.register(r"comments", CommentViewSet, basename="comment")
router.register(r"ratings", CourseRatingViewSet, basename="rating")

urlpatterns = [
    path("", include(router.urls)),
]
