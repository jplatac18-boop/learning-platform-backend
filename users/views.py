from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import StudentProfile, InstructorProfile
from .serializers import (
    UserPublicSerializer,
    UserCreateSerializer,
    UserMeUpdateSerializer,
    UserAdminFlagsSerializer,
    PasswordChangeSerializer,
    StudentProfileSerializer,
    InstructorProfileSerializer,
)
from .permissions import IsAdmin, IsSelfOrAdmin, IsSelfProfileOrAdmin

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_permissions(self):
        # Público SOLO para register
        if self.action in ("register_student", "register_instructor"):
            return [AllowAny()]

        if self.action in ("me", "change_password"):
            return [IsAuthenticated()]

        if self.action in ("list", "destroy", "set_role", "enable_student", "enable_instructor", "admin_flags", "create"):
            return [IsAdmin()]

        return [IsAuthenticated(), IsSelfOrAdmin()]

    def get_serializer_class(self):
        if self.action in ("register_student", "register_instructor"):
            return UserCreateSerializer
        if self.action == "me":
            return UserMeUpdateSerializer
        if self.action in ("admin_flags",):
            return UserAdminFlagsSerializer
        return UserPublicSerializer

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):
        if request.method == "GET":
            return Response(UserPublicSerializer(request.user).data)
        serializer = UserMeUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserPublicSerializer(request.user).data)

    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data["old_password"]):
            return Response({"detail": "Contraseña actual incorrecta."}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "Contraseña actualizada."})

    @action(detail=False, methods=["post"], url_path="register-student")
    def register_student(self, request):
        data = request.data.copy()
        data["role"] = "student"

        user_serializer = UserCreateSerializer(data=data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        profile, _ = StudentProfile.objects.get_or_create(user=user)
        profile.nombre = request.data.get("nombre", profile.nombre)
        profile.apellido = request.data.get("apellido", profile.apellido)
        profile.save()

        user.student_enabled = True
        user.instructor_enabled = False
        user.save(update_fields=["student_enabled", "instructor_enabled"])

        return Response(UserPublicSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="register-instructor")
    def register_instructor(self, request):
        data = request.data.copy()
        data["role"] = "instructor"

        user_serializer = UserCreateSerializer(data=data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        profile, _ = InstructorProfile.objects.get_or_create(user=user)
        profile.bio = request.data.get("bio", profile.bio)
        profile.especialidad = request.data.get("especialidad", profile.especialidad)
        profile.redes_sociales = request.data.get("redes_sociales", profile.redes_sociales)
        profile.save()

        user.instructor_enabled = True
        user.student_enabled = True
        user.save(update_fields=["student_enabled", "instructor_enabled"])

        return Response(UserPublicSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="set-role")
    def set_role(self, request, pk=None):
        user = self.get_object()
        role = request.data.get("role")
        if role not in ("student", "instructor", "admin"):
            return Response({"detail": "Role inválido."}, status=status.HTTP_400_BAD_REQUEST)
        user.role = role
        user.save(update_fields=["role"])
        return Response(UserPublicSerializer(user).data)

    @action(detail=True, methods=["patch"], url_path="enable-student")
    def enable_student(self, request, pk=None):
        user = self.get_object()
        enabled = request.data.get("enabled")
        if enabled is None:
            return Response({"detail": "Falta 'enabled' (true/false)."}, status=status.HTTP_400_BAD_REQUEST)
        user.student_enabled = bool(enabled)
        user.save(update_fields=["student_enabled"])
        return Response(UserPublicSerializer(user).data)

    @action(detail=True, methods=["patch"], url_path="enable-instructor")
    def enable_instructor(self, request, pk=None):
        user = self.get_object()
        enabled = request.data.get("enabled")
        if enabled is None:
            return Response({"detail": "Falta 'enabled' (true/false)."}, status=status.HTTP_400_BAD_REQUEST)
        user.instructor_enabled = bool(enabled)
        user.save(update_fields=["instructor_enabled"])
        return Response(UserPublicSerializer(user).data)

    @action(detail=True, methods=["patch"], url_path="admin-flags")
    def admin_flags(self, request, pk=None):
        user = self.get_object()
        serializer = UserAdminFlagsSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserPublicSerializer(user).data)


class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.select_related("user").all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated, IsSelfProfileOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InstructorProfileViewSet(viewsets.ModelViewSet):
    queryset = InstructorProfile.objects.select_related("user").all()
    serializer_class = InstructorProfileSerializer
    permission_classes = [IsAuthenticated, IsSelfProfileOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
