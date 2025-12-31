from django.test import TestCase
from django.contrib.auth import get_user_model

from users.models import InstructorProfile
from courses.models import Course, Module, Lesson, Quiz
from .models import Enrollment, LessonProgress, Submission


User = get_user_model()


class BaseEnrollmentSetupMixin:
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

        cls.student_user = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="testpass123",
        )
        if hasattr(cls.student_user, "role"):
            cls.student_user.role = "student"
            cls.student_user.save(update_fields=["role"])


class EnrollmentModelTest(BaseEnrollmentSetupMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.enrollment = Enrollment.objects.create(
            user=cls.student_user,
            course=cls.course,
            estado="activo",
            progreso=0,
        )

    def test_enrollment_creation(self):
        self.assertEqual(self.enrollment.user.username, "student")
        self.assertEqual(self.enrollment.course.titulo, "Curso de prueba")
        self.assertEqual(self.enrollment.progreso, 0)


class LessonProgressModelTest(BaseEnrollmentSetupMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.module = Module.objects.create(course=cls.course, titulo="Módulo 1", orden=1)
        cls.lesson = Lesson.objects.create(
            module=cls.module,
            titulo="Lección 1",
            tipo="texto",
            contenido="Contenido",
            url_video="",
            orden=1,
        )
        cls.progress = LessonProgress.objects.create(
            user=cls.student_user,
            lesson=cls.lesson,
            completado=True,
        )

    def test_lesson_progress_creation(self):
        self.assertTrue(self.progress.completado)
        self.assertEqual(self.progress.lesson.titulo, "Lección 1")


class SubmissionModelTest(BaseEnrollmentSetupMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.quiz = Quiz.objects.create(course=cls.course, titulo="Quiz 1", descripcion="Desc quiz")
        cls.submission = Submission.objects.create(user=cls.student_user, quiz=cls.quiz)

    def test_submission_creation(self):
        self.assertEqual(self.submission.user.username, "student")
        self.assertEqual(self.submission.quiz.titulo, "Quiz 1")
