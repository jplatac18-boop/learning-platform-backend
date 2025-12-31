from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import User, InstructorProfile, StudentProfile
from courses.models import Course, Module, Lesson
from enrollments.models import Enrollment, LessonProgress
from feedback.models import Comment, CourseRating


class Command(BaseCommand):
    help = "Crea datos demo: usuarios (student/instructor/admin), perfiles, curso, módulos, lecciones y feedback"

    def handle(self, *args, **options):
        # 1. Usuarios base
        student, _ = User.objects.get_or_create(
            username="student1",
            defaults={"email": "student@test.com"},
        )
        student.set_password("Test1234!")
        student.save()

        instructor_user, _ = User.objects.get_or_create(
            username="instructor1",
            defaults={"email": "instructor@test.com"},
        )
        instructor_user.set_password("Test1234!")
        instructor_user.save()

        admin, _ = User.objects.get_or_create(
            username="admin1",
            defaults={
                "email": "admin@test.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.set_password("Test1234!")
        admin.save()

        # 2. Perfiles
        student_profile, _ = StudentProfile.objects.get_or_create(
            user=student,
            defaults={
                "nombre": "Student",
                "apellido": "Demo",
            },
        )

        instructor_profile, _ = InstructorProfile.objects.get_or_create(
            user=instructor_user,
            defaults={
                "bio": "Instructor demo de React.",
                "especialidad": "Python/React",
                "redes_sociales": "https://example.com",
            },
        )

        # 3. Curso demo
        course, _ = Course.objects.get_or_create(
            titulo="Curso Demo React",
            defaults={
                "descripcion": "Curso de ejemplo para pruebas de la plataforma.",
                "categoria": "Tecnología",   # asegúrate de que existe en tus choices
                "nivel": "Básico",
                "duracion": 60,
                "estado": "publicado",
                "instructor": instructor_profile,
                "imagen": "",
            },
        )

        # 4. Módulo y lecciones
        module1, _ = Module.objects.get_or_create(
            course=course,
            orden=1,
            defaults={
                "titulo": "Introducción",
            },
        )

        lesson1, _ = Lesson.objects.get_or_create(
            module=module1,
            orden=1,
            defaults={
                "titulo": "Bienvenida",
                "contenido": "Lección de bienvenida.",
            },
        )

        lesson2, _ = Lesson.objects.get_or_create(
            module=module1,
            orden=2,
            defaults={
                "titulo": "Instalación",
                "contenido": "Instala las herramientas necesarias.",
            },
        )

        # 5. Enrollment del estudiante en el curso
        enrollment, _ = Enrollment.objects.get_or_create(
            user=student,
            course=course,
            defaults={
                "fecha": timezone.now(),
                "progreso": 50,
                "estado": "activo",   # usa un valor válido de tus choices
            },
        )

        # 6. Progreso de una lección
        LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson1,
        )

        # 7. Comentario de ejemplo
        Comment.objects.get_or_create(
            course=course,
            user=student,
        )

        # 8. Rating de ejemplo (rating es NOT NULL)
        CourseRating.objects.get_or_create(
            course=course,
            user=student,
            defaults={
                "rating": 5,
            },
        )

        self.stdout.write(self.style.SUCCESS("Seed demo creada correctamente."))
