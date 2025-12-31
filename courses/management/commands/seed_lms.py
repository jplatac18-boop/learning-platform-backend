# courses/management/commands/seed_lms.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
import random

from courses.models import Course, Module, Lesson, Quiz, Question, Choice
from enrollments.models import Enrollment, LessonProgress, Submission
from users.models import InstructorProfile  # <-- importante

User = get_user_model()
fake = Faker("es_ES")

class Command(BaseCommand):
    help = "Genera datos de prueba para el LMS (instructores, estudiantes, cursos, módulos, etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--courses",
            type=int,
            default=10,
            help="Cantidad de cursos a crear (por defecto 10)",
        )

    def handle(self, *args, **options):
        num_courses = options["courses"]

        self.stdout.write(self.style.WARNING("Limpiando datos existentes..."))
        self._clear_data()

        self.stdout.write(self.style.WARNING("Creando usuarios..."))
        instructors, students = self._create_users()

        self.stdout.write(self.style.WARNING("Creando cursos completos..."))
        self._create_courses(instructors, students, num_courses)

        self.stdout.write(self.style.SUCCESS("Seed LMS completada."))

    # ---------- helpers ----------

    def _clear_data(self):
        Submission.objects.all().delete()
        LessonProgress.objects.all().delete()
        Enrollment.objects.all().delete()
        Choice.objects.all().delete()
        Question.objects.all().delete()
        Quiz.objects.all().delete()
        Lesson.objects.all().delete()
        Module.objects.all().delete()
        Course.objects.all().delete()

    def _create_users(self):
        instructors = []
        students = []

    def _create_users(self):
        instructors = []
        students = []

        # 5 instructores
        for i in range(5):
            username = f"instructor{i+1}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": fake.email(),
                    "role": "instructor",  # usa tu enum
                },
            )
            if created:
                user.set_password("123456")
            else:
                user.role = "instructor"
            user.instructor_enabled = True
            user.save()

            # perfil de instructor
            profile, _ = InstructorProfile.objects.get_or_create(user=user)
            instructors.append(profile)  # ahora guardamos perfiles

        # 20 estudiantes
        for i in range(20):
            username = f"student{i+1}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": fake.email(),
                    "role": "student",
                },
            )
            if created:
                user.set_password("123456")
            else:
                user.role = "student"
            user.student_enabled = True
            user.save()

            students.append(user)

        return instructors, students
    
    def _create_courses(self, instructors, students, num_courses: int):
        for i in range(num_courses):
            instructor_profile = random.choice(instructors)   

            course = Course.objects.create(
                titulo=fake.sentence(nb_words=4),
                descripcion=fake.paragraph(nb_sentences=5),
                categoria=random.choice(["programación", "diseño", "marketing", "datos"]),
                nivel=random.choice(["básico", "intermedio", "avanzado"]),
                duracion=random.randint(4, 40),
                estado=random.choice(["borrador", "publicado"]),
                instructor=instructor_profile.user,           
            )

            modules = self._create_modules(course)
            lessons = self._create_lessons(modules)
            quizzes = self._create_quizzes(course, modules)
            self._create_enrollments_and_progress(course, lessons, students)
            self._create_submissions(quizzes, students)

    def _create_modules(self, course):
        modules = []
        for order in range(1, random.randint(3, 6)):
            m = Module.objects.create(
                course=course,
                titulo=f"Módulo {order} - {fake.word()}",
                orden=order,
            )
            modules.append(m)
        return modules

    def _create_lessons(self, modules):
        lessons = []
        for m in modules:
            for order in range(1, random.randint(4, 8)):
                tipo = random.choice(["video", "texto", "archivo"])
                lesson = Lesson.objects.create(
                    module=m,
                    titulo=f"Lección {order} - {fake.word()}",
                    tipo = random.choice(["video", "texto"]),
                    contenido=fake.paragraph(nb_sentences=3),
                    url_video="https://www.youtube.com/watch?v=dQw4w9WgXcQ" if tipo == "video" else "",
                    archivo="" if tipo != "archivo" else "",
                    orden=order,
                )
                lessons.append(lesson)
        return lessons

    def _create_quizzes(self, course, modules):
        quizzes = []

        # Quiz a nivel de curso
        if random.random() < 0.7:
            q = Quiz.objects.create(
                course=course,
                module=None,
                titulo=f"Quiz final de {course.titulo}",
                descripcion=fake.sentence(nb_words=8),
            )
            quizzes.append(q)
            self._create_questions_and_choices(q)

        # Quizzes por algunos módulos
        for m in modules:
            if random.random() < 0.6:
                q = Quiz.objects.create(
                    course=None,
                    module=m,
                    titulo=f"Quiz del {m.titulo}",
                    descripcion=fake.sentence(nb_words=8),
                )
                quizzes.append(q)
                self._create_questions_and_choices(q)

        return quizzes

    def _create_questions_and_choices(self, quiz):
        for order in range(1, random.randint(3, 6)):
            question = Question.objects.create(
                quiz=quiz,
                texto=fake.sentence(nb_words=6),
                orden=order,
            )
            correct_index = random.randint(0, 3)
            for i in range(4):
                Choice.objects.create(
                    question=question,
                    texto=fake.sentence(nb_words=3),
                    correcta=(i == correct_index),
                )


    def _create_enrollments_and_progress(self, course, lessons, students):
        # matricula a 5–15 estudiantes
        enrolled_students = random.sample(
            students, k=random.randint(5, min(15, len(students)))
        )
        for s in enrolled_students:
            enrollment = Enrollment.objects.create(
                user=s,
                course=course,
                fecha=fake.date_time_this_year(),
                estado="activo",
                progreso=0,
            )

            # marca algunas lecciones como completadas
            completed_lessons = random.sample(
                lessons, k=random.randint(0, len(lessons))
            )

            if completed_lessons:
                for lesson in completed_lessons:
                    LessonProgress.objects.create(
                        enrollment=enrollment,
                        lesson=lesson,
                        completado=True,
                        completed_at=fake.date_time_this_year(),
                    )
                # porcentaje simple
                enrollment.progreso = int(
                    100 * len(completed_lessons) / max(1, len(lessons))
                )
                enrollment.save()

    def _create_submissions(self, quizzes, students):
        for quiz in quizzes:
            # algunos estudiantes hacen el quiz
            quiz_takers = random.sample(
                students, k=random.randint(3, min(10, len(students)))
            )
            questions = list(quiz.questions.all())
            if not questions:
                continue

            for s in quiz_takers:
                num_attempts = random.randint(1, 3)
                for attempt in range(1, num_attempts + 1):
                    answers = {}
                    correct_count = 0

                    for q in questions:
                        choices = list(q.choices.all())
                        if not choices:
                            continue
                        choice = random.choice(choices)
                        answers[str(q.id)] = choice.id
                        if choice.correcta:
                            correct_count += 1

                    score = int(100 * correct_count / max(1, len(questions)))

                    Submission.objects.create(
                        user=s,
                        quiz=quiz,
                        attempt=attempt,
                        score=score,
                        answers=answers,
                        fecha=fake.date_time_this_year(),
                    )

