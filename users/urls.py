from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, StudentProfileViewSet, InstructorProfileViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"student-profiles", StudentProfileViewSet, basename="student-profile")
router.register(r"instructor-profiles", InstructorProfileViewSet, basename="instructor-profile")

urlpatterns = [
    path("", include(router.urls)),
]
