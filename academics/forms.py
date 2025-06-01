from django import forms
from .models import Subject, Course, Session, Semester, Holiday, TeacherProfile
from users.models import CustomUser  


class AddCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name']

    def clean_name(self):
        name = self.cleaned_data['name'].strip().lower()
        if Course.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("Course with this name already exists.")
        return name

class AddSessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['name', 'start_date', 'end_date', 'course']


class AddSemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['name', 'course', 'session', 'order']


class AddSubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'course', 'session', 'semester', 'teachers']
        widgets = {
            'teachers': forms.CheckboxSelectMultiple
        }


class HolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ['date', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
