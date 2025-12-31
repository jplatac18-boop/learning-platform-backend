from django.db.models import Max, Q
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.models import Course, Lesson, Quiz, Question, Choice
from .models import Enrollment, LessonProgress, Submission
from .serializers import EnrollmentSerializer, LessonProgressSerializer, SubmissionSerializer
from .permissions import (
    CanReadEnrollments,
    CanReadLessonProgress,
    CanReadSubmissions,
    IsStudentEnabled,
)


def _ip(user):
    return getattr(user, "instructor_profile", None)


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.select_related("user", "course", "course__instructor").all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, CanReadEnrollments]

    # Bloquear CRUD directo
    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed("POST")

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return self.queryset

        if user.student_enabled:
            return self.queryset.filter(user=user)

        ip = _ip(user)
        if user.instructor_enabled and ip:
            return self.queryset.filter(course__instructor=ip)

        return self.queryset.none()

    @action(
        detail=False,
        methods=["post"],
        url_path="enroll",
        permission_classes=[IsAuthenticated, IsStudentEnabled],
    )
    def enroll(self, request):
        course_id = request.data.get("course_id")
        if not course_id:
            return Response({"course_id": "Requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(id=course_id, estado="publicado")
        except Course.DoesNotExist:
            return Response(
                {"detail": "Curso no existe o no está publicado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user,
            course=course,
        )
        data = EnrollmentSerializer(enrollment).data
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["get"],
        url_path="my",
        permission_classes=[IsAuthenticated, IsStudentEnabled],
    )
    def my(self, request):
        qs = Enrollment.objects.filter(user=request.user).select_related("course")
        return Response(EnrollmentSerializer(qs, many=True).data)


class LessonProgressViewSet(viewsets.ModelViewSet):
    queryset = LessonProgress.objects.select_related(
        "enrollment",
        "enrollment__user",
        "enrollment__course",
        "lesson",
        "lesson__module",
        "lesson__module__course",
    ).all()
    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated, CanReadLessonProgress]

    # Bloquear CRUD directo
    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed("POST")

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset

        if user.is_staff:
            pass
        elif user.student_enabled:
            qs = qs.filter(enrollment__user=user)
        else:
            ip = _ip(user)
            if user.instructor_enabled and ip:
                qs = qs.filter(enrollment__course__instructor=ip)
            else:
                return self.queryset.none()

        # NUEVO: permitir filtrar por curso
        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(lesson__module__course_id=course_id)

        return qs

    @action(
        detail=False,
        methods=["post"],
        url_path="complete",
        permission_classes=[IsAuthenticated, IsStudentEnabled],
    )
    def complete(self, request):
        lesson_id = request.data.get("lesson_id")
        if not lesson_id:
            return Response({"lesson_id": "Requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lesson = Lesson.objects.select_related("module", "module__course").get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({"detail": "Lección no existe."}, status=status.HTTP_404_NOT_FOUND)

        try:
            enrollment = Enrollment.objects.get(
                user=request.user,
                course=lesson.module.course,
                estado="activo",
            )
        except Enrollment.DoesNotExist:
            return Response(
                {"detail": "No estás matriculado en este curso."},
                status=status.HTTP_403_FORBIDDEN,
            )

        progress, _ = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
        )

        progress.completado = True
        if progress.completed_at is None:
            progress.completed_at = timezone.now()
        progress.save(update_fields=["completado", "completed_at"])

        total_lessons = Lesson.objects.filter(module__course=enrollment.course).count()
        completed = LessonProgress.objects.filter(
            enrollment=enrollment,
            completado=True,
            lesson__module__course=enrollment.course,
        ).count()

        enrollment.progreso = 0 if total_lessons == 0 else round((completed / total_lessons) * 100, 2)
        enrollment.save(update_fields=["progreso"])

        return Response(LessonProgressSerializer(progress).data, status=status.HTTP_200_OK)


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.select_related(
        "user",
        "quiz",
        "quiz__course",
        "quiz__module",
        "quiz__module__course",
    ).all()
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated, CanReadSubmissions]

    # Bloquear CRUD directo
    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed("POST")

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return self.queryset

        if user.student_enabled:
            return self.queryset.filter(user=user)

        ip = _ip(user)
        if user.instructor_enabled and ip:
            return (
                self.queryset.filter(
                    Q(quiz__course__instructor=ip) | Q(quiz__module__course__instructor=ip)
                ).distinct()
            )

        return self.queryset.none()

    @action(
        detail=False,
        methods=["post"],
        url_path="submit",
        permission_classes=[IsAuthenticated, IsStudentEnabled],
    )
    def submit(self, request):
        quiz_id = request.data.get("quiz_id")
        answers = request.data.get("answers", {})

        if not quiz_id:
            return Response({"quiz_id": "Requerido."}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(answers, dict):
            return Response(
                {"answers": "Debe ser un objeto JSON {question_id: choice_id}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            quiz = Quiz.objects.select_related("course", "module", "module__course").get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({"detail": "Quiz no existe."}, status=status.HTTP_404_NOT_FOUND)

        course = quiz.course or (quiz.module.course if quiz.module_id else None)
        if not course:
            return Response(
                {"detail": "Quiz mal configurado (sin course/module)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if course.estado != "publicado":
            return Response({"detail": "Curso no publicado."}, status=status.HTTP_403_FORBIDDEN)

        if not Enrollment.objects.filter(user=request.user, course=course, estado="activo").exists():
            return Response(
                {"detail": "No estás matriculado en este curso."},
                status=status.HTTP_403_FORBIDDEN,
            )

        last_attempt = (
            Submission.objects.filter(user=request.user, quiz=quiz)
            .aggregate(m=Max("attempt"))
            .get("m")
            or 0
        )
        attempt = last_attempt + 1

        question_ids = list(Question.objects.filter(quiz=quiz).values_list("id", flat=True))
        if not question_ids:
            return Response({"detail": "Quiz sin preguntas."}, status=status.HTTP_400_BAD_REQUEST)

        correct = 0
        total = len(question_ids)

        for qid in question_ids:
            choice_id = answers.get(str(qid)) or answers.get(qid)
            if not choice_id:
                continue
            if Choice.objects.filter(id=choice_id, question_id=qid, correcta=True).exists():
                correct += 1

        score = round((correct / total) * 100, 2)

        submission = Submission.objects.create(
            user=request.user,
            quiz=quiz,
            attempt=attempt,
            score=score,
            answers=answers,
        )
        return Response(SubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)
