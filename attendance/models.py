from django.db import models
from users.models import CustomUser
from academics.models import Subject, Semester, Session

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Leave', 'Leave'),
    ]

    student = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='attendance_records'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    teacher = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'},
        related_name='marked_attendance_records'
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('student', 'subject', 'date')  # prevent duplicate

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.subject.name} - {self.date} - {self.status}"
