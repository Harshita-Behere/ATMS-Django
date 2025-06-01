# to automatically create DeanProfile, StudentProfile and TeacherProfile right after a dean user is created.

from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import CustomUser, DeanProfile, TeacherProfile, StudentProfile
from academics.models import School, Course, Session, Semester


@receiver(post_save, sender=CustomUser)
def create_dean_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'dean':
        default_school = School.objects.first()
        DeanProfile.objects.get_or_create(user=instance, defaults={'school': default_school})


@receiver(post_save, sender=CustomUser)
def create_student_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'student':
        if instance.course:
            StudentProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'course': instance.course,
                    'session': Session.objects.first(),
                    'semester': Semester.objects.first()
                }
            )



@receiver(post_save, sender=CustomUser)
def create_teacher_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'teacher':
        TeacherProfile.objects.get_or_create(user=instance)
