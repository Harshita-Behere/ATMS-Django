from django.contrib import admin
from .models import Course, Subject, Session, Semester, TeacherProfile
admin.site.register(Course)
admin.site.register(Subject)
admin.site.register(Session)
admin.site.register(Semester)
admin.site.register(TeacherProfile)


