from django.core.exceptions import ValidationError
from django.db import models


class Comment(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="comments")
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, null=True, blank=True, related_name="comments"
    )
    lesson = models.ForeignKey(
        "courses.Lesson", on_delete=models.CASCADE, null=True, blank=True, related_name="comments"
    )

    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.course and not self.lesson:
            raise ValidationError("El comentario debe pertenecer a un course o a una lesson.")
        if self.course and self.lesson:
            raise ValidationError("El comentario no puede pertenecer a course y lesson al mismo tiempo.")

    def __str__(self):
        return f"{self.user.username} - {self.texto[:20]}"


class CourseRating(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="course_ratings")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="ratings")

    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="unique_rating_user_course")
        ]

    def __str__(self):
        return f"{self.user.username} - {self.course.titulo} - {self.rating}"
