from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import Course, Module, Lesson, Quiz, Question, Choice

User = get_user_model()


class BaseCourseSetupMixin:
    @classmethod
    def setUpTestData(cls):
        cls.instructor_user = User.objects.create_user(
            username="instructor",
            email="instructor@example.com",
            password="testpass123",
            role="instructor",
            instructor_enabled=True,
        )

        cls.instructor_profile = cls.instructor_user.instructor_profile
        cls.instructor_profile.bio = "Bio"
        cls.instructor_profile.especialidad = "Backend"
        cls.instructor_profile.redes_sociales = "https://example.com"
        cls.instructor_profile.save()

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


class CourseModelTest(BaseCourseSetupMixin, TestCase):
    def test_course_creation(self):
        self.assertEqual(self.course.titulo, "Curso de prueba")
        self.assertEqual(self.course.instructor, self.instructor_profile)
        self.assertEqual(self.course.estado, "publicado")


class ModuleModelTest(BaseCourseSetupMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.module = Module.objects.create(course=cls.course, titulo="Módulo 1", orden=1)

    def test_module_creation(self):
        self.assertEqual(self.module.course, self.course)
        self.assertEqual(self.module.orden, 1)


class LessonModelTest(BaseCourseSetupMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.module = Module.objects.create(course=cls.course, titulo="Módulo 1", orden=1)
        cls.lesson = Lesson.objects.create(
            module=cls.module,
            titulo="Lección 1",
            tipo="video",
            contenido="",
            url_video="https://example.com/video",
            orden=1,
        )

    def test_lesson_creation(self):
        self.assertEqual(self.lesson.module, self.module)
        self.assertEqual(self.lesson.tipo, "video")


class QuizModelTest(BaseCourseSetupMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.quiz = Quiz.objects.create(course=cls.course, titulo="Quiz 1", descripcion="Desc quiz")

    def test_quiz_creation(self):
        self.assertEqual(self.quiz.course, self.course)
        self.assertEqual(self.quiz.titulo, "Quiz 1")


class QuestionModelTest(BaseCourseSetupMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.quiz = Quiz.objects.create(course=cls.course, titulo="Quiz 1", descripcion="Desc quiz")
        cls.question = Question.objects.create(quiz=cls.quiz, texto="Pregunta 1", orden=1)

    def test_question_creation(self):
        self.assertEqual(self.question.quiz, self.quiz)
        self.assertEqual(self.question.orden, 1)


class ChoiceModelTest(BaseCourseSetupMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.quiz = Quiz.objects.create(course=cls.course, titulo="Quiz 1", descripcion="Desc quiz")
        cls.question = Question.objects.create(quiz=cls.quiz, texto="Pregunta 1", orden=1)
        cls.choice = Choice.objects.create(question=cls.question, texto="Opción A", correcta=True)

    def test_choice_creation(self):
        self.assertEqual(self.choice.question, self.question)
        self.assertTrue(self.choice.correcta)
