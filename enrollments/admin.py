from django.contrib import admin
from .models import Enrollment, LessonProgress, Submission


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "estado", "progreso", "fecha")
    list_filter = ("estado", "course")
    search_fields = ("user__username", "user__email", "course__titulo")
    ordering = ("-fecha",)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("id", "enrollment", "lesson", "completado", "completed_at")
    list_filter = ("completado",)
    search_fields = ("enrollment__user__username", "lesson__titulo", "enrollment__course__titulo")
    ordering = ("-completed_at", "-id")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "quiz", "attempt", "score", "fecha")
    list_filter = ("quiz",)
    search_fields = ("user__username", "quiz__titulo")
    ordering = ("-fecha", "-attempt")
