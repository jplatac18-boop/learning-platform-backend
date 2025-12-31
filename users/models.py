from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Estudiante"
        INSTRUCTOR = "instructor", "Instructor"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=15, choices=Role.choices, default=Role.STUDENT)

    # Flags reales de habilitación
    student_enabled = models.BooleanField(default=True)
    instructor_enabled = models.BooleanField(default=False)

    # Fix para evitar choques con auth.User
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to.",
        related_name="custom_user_groups",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="custom_user_permissions",
        related_query_name="user",
    )

    def save(self, *args, **kwargs):
        # Admin: marcar como staff (y opcionalmente superuser)
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            # self.is_superuser = True  # opcional

        # Instructor: habilitar flag de instructor
        if self.role == self.Role.INSTRUCTOR:
            self.instructor_enabled = True

        # Estudiante: asegurar flag de estudiante
        if self.role == self.Role.STUDENT:
            self.student_enabled = True

        super().save(*args, **kwargs)

    @property
    def has_student_profile(self):
        return hasattr(self, "student_profile")

    @property
    def has_instructor_profile(self):
        return hasattr(self, "instructor_profile")


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    nombre = models.CharField(max_length=100, blank=True, default="")
    apellido = models.CharField(max_length=100, blank=True, default="")

    def __str__(self):
        return f"StudentProfile({self.user.username})"


class InstructorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="instructor_profile",
    )
    bio = models.TextField(blank=True, default="")
    especialidad = models.CharField(max_length=100, blank=True, default=""
    )
    redes_sociales = models.URLField(blank=True, default="")

    def __str__(self):
        return f"InstructorProfile({self.user.username})"


@receiver(post_save, sender=User)
def ensure_profiles_for_user(sender, instance, created, **kwargs):
    if not created:
        return
    StudentProfile.objects.get_or_create(user=instance)
    InstructorProfile.objects.get_or_create(user=instance)
