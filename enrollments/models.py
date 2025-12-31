from django.db import models
from django.utils import timezone


class Enrollment(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        INACTIVO = "inactivo", "Inactivo"

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="enrollments")

    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    progreso = models.FloatField(default=0)  # 0..100

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="unique_enrollment_user_course")
        ]

    def __str__(self):
        return f"{self.user.username} - {self.course.titulo}"


class LessonProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.CASCADE, related_name="progress_entries")

    completado = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["enrollment", "lesson"], name="unique_progress_per_lesson_enrollment")
        ]

    def mark_completed(self):
        self.completado = True
        self.completed_at = timezone.now()

    def __str__(self):
        return f"{self.enrollment.user.username} - {self.lesson.titulo}"


class Submission(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="submissions")
    quiz = models.ForeignKey("courses.Quiz", on_delete=models.CASCADE, related_name="submissions")

    attempt = models.PositiveIntegerField()
    score = models.FloatField(default=0)  # 0..100
    answers = models.JSONField(default=dict, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "quiz", "attempt"], name="unique_submission_attempt")
        ]
        ordering = ["-fecha", "-attempt"]

    def __str__(self):
        return f"{self.user.username} - {self.quiz.titulo} (attempt {self.attempt})"
