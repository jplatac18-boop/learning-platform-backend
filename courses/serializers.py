from rest_framework import serializers
from .models import Course, Module, Lesson, Quiz, Question, Choice


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ("id", "module", "titulo", "tipo", "contenido", "url_video", "archivo", "orden")


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ("id", "course", "titulo", "orden", "lessons")


class CourseListSerializer(serializers.ModelSerializer):
    # OJO: esto devuelve el ID del InstructorProfile
    instructor_id = serializers.IntegerField(source="instructor.id", read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "instructor_id",
            "titulo",
            "categoria",
            "nivel",
            "duracion",
            "imagen",
            "estado",
            "created_at",
            "updated_at",
        )


class CourseDetailSerializer(serializers.ModelSerializer):
    instructor_id = serializers.IntegerField(source="instructor.id", read_only=True)
    modules = ModuleSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "instructor_id",
            "titulo",
            "descripcion",
            "categoria",
            "nivel",
            "duracion",
            "imagen",
            "estado",
            "created_at",
            "updated_at",
            "modules",
        )


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    # read_only porque lo debe setear el backend en perform_create/perform_update
    instructor = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Course
        fields = ("id", "instructor", "titulo", "descripcion", "categoria", "nivel", "duracion", "imagen", "estado")


class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ("id", "module", "course", "titulo", "descripcion")


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ("id", "question", "texto", "correcta")


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ("id", "quiz", "texto", "orden", "choices")
