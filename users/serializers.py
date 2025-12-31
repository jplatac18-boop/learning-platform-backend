from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import StudentProfile, InstructorProfile

User = get_user_model()

class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id","username","email","first_name","last_name","role","is_active",
            "student_enabled","instructor_enabled",
        )

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "first_name", "last_name", "role")
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserMeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")

class UserAdminFlagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("student_enabled", "instructor_enabled", "is_active", "role")

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

class StudentProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = StudentProfile
        fields = ("id", "user", "nombre", "apellido")

class InstructorProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = InstructorProfile
        fields = ("id", "user", "bio", "especialidad", "redes_sociales")
