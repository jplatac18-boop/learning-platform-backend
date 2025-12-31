from rest_framework import serializers
from .models import Comment, CourseRating


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "user", "course", "lesson", "texto", "fecha")
        read_only_fields = ("id", "user", "fecha")

    def validate(self, attrs):
        course = attrs.get("course")
        lesson = attrs.get("lesson")

        if not course and not lesson:
            raise serializers.ValidationError("Debes enviar course o lesson.")
        if course and lesson:
            raise serializers.ValidationError("No envíes course y lesson a la vez.")

        # inferir course desde lesson
        if lesson and not course:
            attrs["course"] = lesson.module.course

        return attrs


class CourseRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseRating
        fields = ("id", "user", "course", "rating", "fecha")
        read_only_fields = ("id", "user", "fecha")
