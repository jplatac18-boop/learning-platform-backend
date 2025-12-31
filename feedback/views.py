from django.db.models import Avg, Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from courses.models import Course
from enrollments.models import Enrollment
from .models import Comment, CourseRating
from .serializers import CommentSerializer, CourseRatingSerializer
from .permissions import CanReadFeedback, IsOwnerOrAdmin, IsStudentEnabled


def can_user_write_feedback(user, course: Course) -> bool:
    if user.is_staff:
        return True
    if not getattr(user, "student_enabled", False):
        return False
    if course.estado != "publicado":
        return False
    return Enrollment.objects.filter(user=user, course=course, estado="activo").exists()


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related(
        "user", "course", "lesson", "lesson__module", "lesson__module__course"
    ).all()
    serializer_class = CommentSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [CanReadFeedback()]

        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrAdmin()]

        # create
        return [IsAuthenticated(), IsStudentEnabled()]

    def get_queryset(self):
        qs = self.queryset

        course_id = self.request.query_params.get("course_id")
        lesson_id = self.request.query_params.get("lesson_id")
        if course_id:
            qs = qs.filter(course_id=course_id)
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)

        user = getattr(self.request, "user", None)

        if not user or not user.is_authenticated:
            return qs.filter(course__estado="publicado")

        if user.is_staff:
            return qs

        if getattr(user, "instructor_enabled", False):
            ip = getattr(user, "instructor_profile", None)
            if not ip:
                return qs.filter(course__estado="publicado")
            return qs.filter(Q(course__estado="publicado") | Q(course__instructor=ip)).distinct()

        return qs.filter(course__estado="publicado")

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise MethodNotAllowed("POST")

        course = serializer.validated_data.get("course")
        if not course:
            raise ValidationError({"course": "No se pudo inferir el curso."})

        if not can_user_write_feedback(self.request.user, course):
            raise PermissionDenied("No permitido (requiere estar enrolado y curso publicado).")

        serializer.save(user=self.request.user)


class CourseRatingViewSet(viewsets.ModelViewSet):
    queryset = CourseRating.objects.select_related("user", "course").all()
    serializer_class = CourseRatingSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "summary"):
            return [CanReadFeedback()] if self.action != "summary" else [AllowAny()]

        if self.action == "rate":
            return [IsAuthenticated(), IsStudentEnabled()]

        # Bloqueamos create tradicional
        if self.action == "create":
            return [IsAuthenticated()]

        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed("POST")  # usar /rate/

    def get_queryset(self):
        qs = self.queryset
        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(course_id=course_id)

        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            return qs.filter(course__estado="publicado")

        if user.is_staff:
            return qs

        if getattr(user, "instructor_enabled", False):
            ip = getattr(user, "instructor_profile", None)
            if not ip:
                return qs.filter(course__estado="publicado")
            return qs.filter(Q(course__estado="publicado") | Q(course__instructor=ip)).distinct()

        return qs.filter(course__estado="publicado")

    @action(detail=False, methods=["post"], url_path="rate")
    def rate(self, request):
        course_id = request.data.get("course_id")
        rating = request.data.get("rating")

        if not course_id:
            raise ValidationError({"course_id": "Requerido."})
        if rating is None:
            raise ValidationError({"rating": "Requerido."})

        try:
            rating = int(rating)
        except ValueError:
            raise ValidationError({"rating": "Debe ser entero 1..5."})

        if rating < 1 or rating > 5:
            raise ValidationError({"rating": "Debe estar entre 1 y 5."})

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"detail": "Curso no existe."}, status=status.HTTP_404_NOT_FOUND)

        if not can_user_write_feedback(request.user, course):
            raise PermissionDenied("No permitido (requiere estar enrolado y curso publicado).")

        obj, created = CourseRating.objects.update_or_create(
            user=request.user,
            course=course,
            defaults={"rating": rating},
        )

        data = CourseRatingSerializer(obj).data
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="summary", permission_classes=[AllowAny])
    def summary(self, request):
        course_id = request.query_params.get("course_id")
        if not course_id:
            raise ValidationError({"course_id": "Requerido."})

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"detail": "Curso no existe."}, status=status.HTTP_404_NOT_FOUND)

        if course.estado != "publicado":
            raise PermissionDenied("Curso no publicado.")

        agg = CourseRating.objects.filter(course=course).aggregate(
            avg=Avg("rating"),
            count=Count("id"),
        )

        return Response(
            {
                "course_id": course.id,
                "avg_rating": None if agg["avg"] is None else round(float(agg["avg"]), 2),
                "ratings_count": agg["count"],
            }
        )
