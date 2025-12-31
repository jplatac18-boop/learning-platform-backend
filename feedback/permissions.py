from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsStudentEnabled(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.is_staff or getattr(u, "student_enabled", False)))


class CanReadFeedback(BasePermission):
    """
    Lectura pública SOLO de cursos publicados.
    Si el curso no está publicado: solo admin o instructor dueño.
    """
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        u = request.user
        course = getattr(obj, "course", None)

        if course and getattr(course, "estado", None) == "publicado":
            return True

        if not u or not u.is_authenticated:
            return False

        if u.is_staff:
            return True

        if getattr(u, "instructor_enabled", False):
            ip = getattr(u, "instructor_profile", None)
            return bool(ip and getattr(course, "instructor_id", None) == ip.id)

        return False


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        return bool(u.is_staff or getattr(obj, "user_id", None) == u.id)

