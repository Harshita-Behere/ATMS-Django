from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, School, StudentProfile

# inline admin for StudentProfile
class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'role', 'school', 'is_staff']

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'school')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'school')}),
    )

    def get_inline_instances(self, request, obj=None):
        """
        Show StudentProfile inline only if the user is a student.
        """
        inlines = []
        if obj and obj.role == 'student':
            inlines.append(StudentProfileInline(self.model, self.admin_site))
        return inlines

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(School)

