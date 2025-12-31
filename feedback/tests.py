from django.test import TestCase
from django.contrib.auth import get_user_model

from users.models import InstructorProfile
from courses.models import Course, Module, Lesson
from .models import Comment, CourseRating


User = get_user_model()


class BaseFeedbackSetupMixin:
    @classmethod
    def setUpTestData(cls):
        cls.instructor_user = User.objects.create_user(
            username="instructor",
            email="instructor@example.com",
            password="testpass123",
        )
        if hasattr(cls.instructor_user, "role"):
            cls.instructor_user.role = "instructor"
            cls.instructor_user.save(update_fields=["role"])

        cls.instructor_profile = InstructorProfile.objects.create(
            user=cls.instructor_user,
            bio="Bio",
            especialidad="Backend",
            redes_sociales="https://example.com",
        )

        cls.course = Course.objects.create(
            instructor=cls.instructor_profile,
            titulo="Curso de prueba",
            descripcion="Descripción de prueba",
            categoria="Tecnología",
            nivel="Básico",
            duracion=60,
            imagen="",
            estado="publicado",
        )

        cls.module = Module.objects.create(course=cls.course, titulo="Módulo 1", orden=1)
        cls.lesson = Lesson.objects.create(
            module=cls.module,
            titulo="Lección 1",
            tipo="texto",
            contenido="Contenido",
            url_video="",
            orden=1,
        )

        cls.student_user = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="testpass123",
        )
        if hasattr(cls.student_user, "role"):
            cls.student_user.role = "student"
            cls.student_user.save(update_fields=["role"])


class CommentModelTest(BaseFeedbackSetupMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment_course = Comment.objects.create(
            user=cls.student_user,
            course=cls.course,
            texto="Comentario en curso",
        )
        cls.comment_lesson = Comment.objects.create(
            user=cls.student_user,
            lesson=cls.lesson,
            texto="Comentario en lección",
        )

    def test_comment_course_creation(self):
        self.assertEqual(self.comment_course.course, self.course)
        self.assertIsNone(self.comment_course.lesson)

    def test_comment_lesson_creation(self):
        self.assertEqual(self.comment_lesson.lesson, self.lesson)
        self.assertIsNone(self.comment_lesson.course)


class CourseRatingModelTest(BaseFeedbackSetupMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.rating = CourseRating.objects.create(user=cls.student_user, course=cls.course, rating=5)

    def test_rating_creation(self):
        self.assertEqual(self.rating.rating, 5)
        self.assertEqual(self.rating.course, self.course)
