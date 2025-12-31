# courses/views.py
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Course, Module, Lesson, Quiz, Question, Choice
from enrollments.models import Enrollment
from .permissions import IsInstructorEnabledOrAdmin, CanReadCourse, IsCourseOwnerOrAdmin
from .serializers import (
    CourseListSerializer,
    CourseDetailSerializer,
    CourseCreateUpdateSerializer,
    ModuleSerializer,
    LessonSerializer,
    QuizSerializer,
    QuestionSerializer,
    ChoiceSerializer,
)


def get_instructor_profile(user):
    return getattr(user, "instructor_profile", None)


# =========================
# Courses
# =========================
class CourseViewSet(viewsets.ModelViewSet):
    # Solo seguimos la FK instructor; el modelo User ya no tiene "user"
    queryset = (
        Course.objects
        .select_related("instructor")  # antes: "instructor", "instructor__user"
        .all()
    )

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAuthenticated(), IsInstructorEnabledOrAdmin()]

    def get_serializer_class(self):
        if self.action == "list":
            return CourseListSerializer
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseCreateUpdateSerializer

    def get_queryset(self):
        qs = self.queryset
        user = getattr(self.request, "user", None)

        if not user or not user.is_authenticated:
            return qs.filter(estado=Course.Estado.PUBLICADO)

        if user.is_staff:
            return qs

        ip = get_instructor_profile(user)
        if ip is not None:
            return qs.filter(
                Q(estado=Course.Estado.PUBLICADO) | Q(instructor=ip)
            ).distinct()

        return qs.filter(estado=Course.Estado.PUBLICADO)

    def perform_create(self, serializer):
        user = self.request.user

        if user.is_staff:
            instructor = serializer.validated_data.get("instructor")
            if instructor is None:
                raise PermissionDenied("Debes indicar un instructor para el curso.")
            serializer.save(instructor=instructor)
            return

        ip = get_instructor_profile(user)
        if ip is None:
            raise PermissionDenied("InstructorProfile no encontrado para el usuario.")
        serializer.save(instructor=ip)

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        if not CanReadCourse().has_object_permission(request, self, obj):
            return Response(
                {"detail": "No permitido."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        if not IsCourseOwnerOrAdmin().has_object_permission(request, self, obj):
            return Response(
                {"detail": "No permitido."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if not IsCourseOwnerOrAdmin().has_object_permission(request, self, obj):
            return Response(
                {"detail": "No permitido."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["post"],
        url_path="publish",
        permission_classes=[IsAuthenticated, IsInstructorEnabledOrAdmin],
    )
    def publish(self, request, pk=None):
        course = self.get_object()
        if not IsCourseOwnerOrAdmin().has_object_permission(request, self, course):
            return Response(
                {"detail": "No permitido."},
                status=status.HTTP_403_FORBIDDEN,
            )
        course.estado = Course.Estado.PUBLICADO
        course.save(update_fields=["estado"])
        return Response(CourseDetailSerializer(course).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="draft",
        permission_classes=[IsAuthenticated, IsInstructorEnabledOrAdmin],
    )
    def draft(self, request, pk=None):
        course = self.get_object()
        if not IsCourseOwnerOrAdmin().has_object_permission(request, self, course):
            return Response(
                {"detail": "No permitido."},
                status=status.HTTP_403_FORBIDDEN,
            )
        course.estado = Course.Estado.BORRADOR
        course.save(update_fields=["estado"])
        return Response(CourseDetailSerializer(course).data)


# =========================
# Modules (INSTRUCTOR)
# =========================
class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.select_related("course", "course__instructor", "course__instructor__user").all()
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated, IsInstructorEnabledOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset

        if not user.is_staff:
            ip = get_instructor_profile(user)
            if ip is None:
                return qs.none()
            qs = qs.filter(course__instructor=ip)

        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(course_id=course_id)

        return qs


# =========================
# Lessons (INSTRUCTOR)
# =========================
class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.select_related(
        "module",
        "module__course",
        "module__course__instructor",
        "module__course__instructor__user",
    ).all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsInstructorEnabledOrAdmin]
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # <- aquí acepta JSON también

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset

        if not user.is_staff:
            ip = get_instructor_profile(user)
            if ip is None:
                return qs.none()
            qs = qs.filter(module__course__instructor=ip)

        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(module__course_id=course_id)

        module_id = self.request.query_params.get("module_id")
        if module_id:
            qs = qs.filter(module_id=module_id)

        return qs


# =========================
# Quizzes
# =========================
class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.select_related(
        "module",
        "course",
        "module__course",
        "course__instructor",
        "module__course__instructor",
    ).all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsInstructorEnabledOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset

        if not user.is_staff:
            ip = get_instructor_profile(user)
            if ip is None:
                return qs.none()
            qs = qs.filter(Q(course__instructor=ip) | Q(module__course__instructor=ip)).distinct()

        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(course_id=course_id)

        module_id = self.request.query_params.get("module_id")
        if module_id:
            qs = qs.filter(module_id=module_id)

        return qs


# =========================
# Questions
# =========================
class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.select_related(
        "quiz",
        "quiz__course",
        "quiz__module",
        "quiz__module__course",
    ).all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated, IsInstructorEnabledOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset

        if not user.is_staff:
            ip = get_instructor_profile(user)
            if ip is None:
                return qs.none()
            qs = qs.filter(
                Q(quiz__course__instructor=ip) | Q(quiz__module__course__instructor=ip)
            ).distinct()

        quiz_id = self.request.query_params.get("quiz_id")
        if quiz_id:
            qs = qs.filter(quiz_id=quiz_id)

        return qs


# =========================
# Choices
# =========================
class ChoiceViewSet(viewsets.ModelViewSet):
    queryset = Choice.objects.select_related(
        "question",
        "question__quiz",
        "question__quiz__course",
        "question__quiz__module",
        "question__quiz__module__course",
    ).all()
    serializer_class = ChoiceSerializer
    permission_classes = [IsAuthenticated, IsInstructorEnabledOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset

        if not user.is_staff:
            ip = get_instructor_profile(user)
            if ip is None:
                return qs.none()
            qs = qs.filter(
                Q(question__quiz__course__instructor=ip)
                | Q(question__quiz__module__course__instructor=ip)
            ).distinct()

        question_id = self.request.query_params.get("question_id")
        if question_id:
            qs = qs.filter(question_id=question_id)

        return qs


# =========================
# Endpoints de lectura para ESTUDIANTES
# =========================
class StudentCourseModulesView(APIView):
    """
    GET /api/courses/student-modules/?course_id=ID
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        course_id = request.query_params.get("course_id")
        if not course_id:
            return Response({"detail": "course_id requerido."}, status=status.HTTP_400_BAD_REQUEST)

        modules = Module.objects.filter(course_id=course_id).order_by("orden")
        data = ModuleSerializer(modules, many=True).data
        return Response(data)


class StudentCourseLessonsView(APIView):
    """
    GET /api/courses/student-lessons/?course_id=ID[&module_id=ID]
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        course_id = request.query_params.get("course_id")
        if not course_id:
            return Response({"detail": "course_id requerido."}, status=status.HTTP_400_BAD_REQUEST)

        qs = Lesson.objects.select_related("module", "module__course").filter(
            module__course_id=course_id
        )

        module_id = request.query_params.get("module_id")
        if module_id:
            qs = qs.filter(module_id=module_id)

        qs = qs.order_by("module__orden", "orden")
        data = LessonSerializer(qs, many=True).data
        return Response(data)
