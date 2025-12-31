from django.contrib import admin
from .models import Course, Module, Lesson, Quiz, Question, Choice

admin.site.register(Course)
admin.site.register(Module)
admin.site.register(Lesson)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Choice)
