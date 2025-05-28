from django.db import models
from users.models import CustomUser
from academics.models import Session, Semester

class LeaveApplication(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    reason = models.TextField()
    from_date = models.DateField()
    to_date = models.DateField()
    applied_on = models.DateTimeField(auto_now_add=True)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ], default='Pending')

    def __str__(self):
        return f"{self.user.get_full_name()} | {self.role} | {self.status}"

