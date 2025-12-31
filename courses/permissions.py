from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsInstructorEnabledOrAdmin(BasePermission):
    """
    Permite acciones autenticadas solo a:
    - admin/staff
    - usuarios con instructor_enabled=True
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or getattr(request.user, "instructor_enabled", False))
        )


class CanReadCourse(BasePermission):
    """
    - Lectura pública si el curso está publicado.
    - Si no está publicado: solo admin o el instructor dueño.
    """
    def has_object_permission(self, request, view, obj):
        # Lectura pública
        if request.method in SAFE_METHODS and obj.estado == "publicado":
            return True

        # No autenticado: no puede leer borradores
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin: puede leer todo
        if request.user.is_staff:
            return True

        # Instructor habilitado y dueño del curso (InstructorProfile)
        ip = getattr(request.user, "instructor_profile", None)
        return bool(getattr(request.user, "instructor_enabled", False) and ip and obj.instructor_id == ip.id)


class IsCourseOwnerOrAdmin(BasePermission):
    """
    Escritura/edición/borrado:
    - admin/staff
    - instructor habilitado dueño del curso
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True

        ip = getattr(request.user, "instructor_profile", None)
        return bool(getattr(request.user, "instructor_enabled", False) and ip and obj.instructor_id == ip.id)
