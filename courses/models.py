import os
from django.db import models
from django.core.exceptions import ValidationError


def lesson_upload_path(instance, filename):
    course_id = instance.module.course_id
    module_id = instance.module_id
    return f"lessons/course_{course_id}/module_{module_id}/{filename}"


class Course(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        PUBLICADO = "publicado", "Publicado"

    # IMPORTANTE: consistente con tus ViewSets (InstructorProfile)
    instructor = models.ForeignKey(
        "users.InstructorProfile",
        on_delete=models.CASCADE,
        related_name="courses",
    )

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=100)
    nivel = models.CharField(max_length=50)
    duracion = models.IntegerField()
    imagen = models.URLField(blank=True, default="")
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.BORRADOR)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo

    @property
    def is_published(self):
        return self.estado == self.Estado.PUBLICADO


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    titulo = models.CharField(max_length=200)
    orden = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["course", "orden"], name="unique_module_order_per_course")
        ]
        ordering = ["orden", "id"]

    def __str__(self):
        return self.titulo


class Lesson(models.Model):
    class Tipo(models.TextChoices):
        VIDEO = "video", "Video"
        TEXTO = "texto", "Texto"
        ARCHIVO = "archivo", "Archivo"

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    contenido = models.TextField(blank=True, default="")
    url_video = models.URLField(blank=True, default="")
    archivo = models.FileField(upload_to=lesson_upload_path, blank=True, null=True)
    orden = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["module", "orden"], name="unique_lesson_order_per_module")
        ]
        ordering = ["orden", "id"]

    def clean(self):
        if self.tipo == self.Tipo.VIDEO:
            if not self.url_video:
                raise ValidationError({"url_video": "url_video es obligatorio cuando tipo=video."})

        elif self.tipo == self.Tipo.TEXTO:
            if not self.contenido:
                raise ValidationError({"contenido": "contenido es obligatorio cuando tipo=texto."})

        elif self.tipo == self.Tipo.ARCHIVO:
            if not self.archivo:
                raise ValidationError({"archivo": "archivo es obligatorio cuando tipo=archivo."})
            ext = os.path.splitext(self.archivo.name)[1].lower()
            if ext != ".pdf":
                raise ValidationError({"archivo": "Solo se permite PDF."})

    def __str__(self):
        return self.titulo


class Quiz(models.Model):
    """
    Un quiz puede colgar directamente de Course o de Module (uno de los dos).
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="quizzes",
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="quizzes",
    )

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, default="")  # <--- NUEVO CAMPO
    orden = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    (models.Q(course__isnull=False) & models.Q(module__isnull=True))
                    | (models.Q(course__isnull=True) & models.Q(module__isnull=False))
                ),
                name="quiz_course_xor_module",
            ),
        ]
        ordering = ["orden", "id"]

    def clean(self):
        if not self.course and not self.module:
            raise ValidationError("El quiz debe pertenecer a un course o a un module.")
        if self.course and self.module:
            raise ValidationError("El quiz no puede pertenecer a course y module al mismo tiempo.")

    def __str__(self):
        return self.titulo

    """
    Un quiz puede colgar directamente de Course o de Module (uno de los dos).
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name="quizzes")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True, related_name="quizzes")

    titulo = models.CharField(max_length=200)
    orden = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    (models.Q(course__isnull=False) & models.Q(module__isnull=True)) |
                    (models.Q(course__isnull=True) & models.Q(module__isnull=False))
                ),
                name="quiz_course_xor_module",
            ),
        ]
        ordering = ["orden", "id"]

    def clean(self):
        if not self.course and not self.module:
            raise ValidationError("El quiz debe pertenecer a un course o a un module.")
        if self.course and self.module:
            raise ValidationError("El quiz no puede pertenecer a course y module al mismo tiempo.")

    def __str__(self):
        return self.titulo


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    texto = models.TextField()
    orden = models.IntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["quiz", "orden"], name="unique_question_order_per_quiz")
        ]
        ordering = ["orden", "id"]

    def __str__(self):
        return f"Q{self.orden}: {self.texto[:40]}"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    texto = models.CharField(max_length=255)
    correcta = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.texto
