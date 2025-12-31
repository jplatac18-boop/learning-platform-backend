from rest_framework import serializers
from .models import Enrollment, LessonProgress, Submission


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ("id", "user", "course", "fecha", "estado", "progreso")
        read_only_fields = ("id", "user", "fecha", "progreso")


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ("id", "enrollment", "lesson", "completado", "completed_at")
        read_only_fields = ("id", "completed_at")


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ("id", "user", "quiz", "attempt", "score", "answers", "fecha")
        read_only_fields = ("id", "user", "attempt", "score", "fecha")
