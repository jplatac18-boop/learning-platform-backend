from django.contrib import admin
from .models import Comment, CourseRating


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "lesson", "fecha")
    search_fields = ("user__username", "texto", "course__titulo", "lesson__titulo")
    list_filter = ("course", "fecha")


@admin.register(CourseRating)
class CourseRatingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "rating", "fecha")
    search_fields = ("user__username", "course__titulo")
    list_filter = ("rating", "course")
