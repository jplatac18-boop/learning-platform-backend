from rest_framework.permissions import BasePermission, SAFE_METHODS


def _ip(user):
    return getattr(user, "instructor_profile", None)


class IsStudentEnabled(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.is_staff or getattr(u, "student_enabled", False)))


class IsInstructorEnabled(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.is_staff or getattr(u, "instructor_enabled", False)))


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_staff)


class CanReadEnrollments(BasePermission):
    """
    Lectura:
      - Admin: todo
      - Student enabled: solo sus enrollments
      - Instructor enabled: enrollments de cursos donde es dueño
    """
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and request.method in SAFE_METHODS)

    def has_object_permission(self, request, view, obj):
        u = request.user
        if u.is_staff:
            return True

        if obj.user_id == u.id:
            return bool(getattr(u, "student_enabled", False))

        ip = _ip(u)
        if getattr(u, "instructor_enabled", False) and ip:
            return obj.course.instructor_id == ip.id

        return False


class CanReadLessonProgress(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and request.method in SAFE_METHODS)

    def has_object_permission(self, request, view, obj):
        u = request.user
        if u.is_staff:
            return True

        if obj.enrollment.user_id == u.id:
            return bool(getattr(u, "student_enabled", False))

        ip = _ip(u)
        if getattr(u, "instructor_enabled", False) and ip:
            return obj.enrollment.course.instructor_id == ip.id

        return False


class CanReadSubmissions(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and request.method in SAFE_METHODS)

    def has_object_permission(self, request, view, obj):
        u = request.user
        if u.is_staff:
            return True

        if obj.user_id == u.id:
            return bool(getattr(u, "student_enabled", False))

        ip = _ip(u)
        if getattr(u, "instructor_enabled", False) and ip:
            course = obj.quiz.course or (obj.quiz.module.course if obj.quiz.module_id else None)
            return bool(course and course.instructor_id == ip.id)

        return False
