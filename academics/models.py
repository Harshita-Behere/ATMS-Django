from django.db import models
from django.conf import settings 
from users.models import TeacherProfile

SCHOOL_CHOICES = (
    ('science_tech', 'School of Science and Technology'),
    ('forensic_science', 'School of Forensic Sciences'),
    ('legal_studies', 'School of Legal Studies'),
)

class School(models.Model):
    code = models.CharField(max_length=50, choices=SCHOOL_CHOICES, unique=True)
    
    def __str__(self):
        return dict(SCHOOL_CHOICES).get(self.code, self.code)

class Course(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Session(models.Model):
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    course = models.ForeignKey('Course', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.course.name})"

class Semester(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()  

    class Meta:
        unique_together = ('name', 'course', 'session')
        ordering = ['order']  # semester order (not working)

    def __str__(self):
        return f"{self.name} ({self.session} - {self.course})"

class Subject(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    teachers = models.ManyToManyField(TeacherProfile, related_name='subjects')

    def __str__(self):
        return self.name

# class Subject(models.Model):
#     name = models.CharField(max_length=255)
#     course = models.ForeignKey(Course, on_delete=models.CASCADE)
#     session = models.ForeignKey(Session, on_delete=models.CASCADE)
#     semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
#     teachers = models.ManyToManyField(TeacherProfile)

#     class Meta:
#         unique_together = ('name', 'course', 'session', 'semester')

#     def __str__(self):
#         return f"{self.name} ({self.course}, {self.session}, {self.semester})"
