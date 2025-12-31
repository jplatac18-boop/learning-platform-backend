# courses/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet,
    ModuleViewSet,
    LessonViewSet,
    QuizViewSet,
    QuestionViewSet,
    ChoiceViewSet,
    StudentCourseModulesView,
    StudentCourseLessonsView,
)

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="courses")
router.register(r"modules", ModuleViewSet, basename="modules")
router.register(r"lessons", LessonViewSet, basename="lessons")
router.register(r"quizzes", QuizViewSet, basename="quizzes")
router.register(r"questions", QuestionViewSet, basename="questions")
router.register(r"choices", ChoiceViewSet, basename="choices")

urlpatterns = [
    path("", include(router.urls)),
    path("student-modules/", StudentCourseModulesView.as_view(), name="student-course-modules"),
    path("student-lessons/", StudentCourseLessonsView.as_view(), name="student-course-lessons"),
]
