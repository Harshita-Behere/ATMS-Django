import random
import string
from datetime import datetime

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.db.models import Q

from .forms import (
    CustomUserCreationForm,
    CustomLoginForm,
    AddTeacherForm,
    EditTeacherForm,
    AddStudentForm,
    EditStudentForm,
)


from .models import CustomUser, StudentProfile, TeacherProfile
from academics.models import Course, Session, Semester, Subject
from attendance.models import AttendanceRecord
from user_messages.models import Message
 


#for emailing password to student  - later
# from django.core.mail import send_mail
# from django.conf import settings

#bulk import
import openpyxl
from django.core.mail import send_mail

#bulk promote
from django.db.models import F


User = get_user_model()

def generate_random_password(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def register(request):
    courses = Course.objects.all()
    sessions = Session.objects.all()
    semesters = Semester.objects.all()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            role = form.cleaned_data.get('role')
            user.role = role
            user.save()

            if role == 'teacher':
                TeacherProfile.objects.create(user=user)

            elif role == 'student':
                course_id = request.POST.get('course')
                session_id = request.POST.get('session')
                semester_id = request.POST.get('semester')

                if course_id and session_id and semester_id:
                    student_profile = StudentProfile.objects.create(
                        user=user,
                        course_id=course_id,
                        session_id=session_id,
                        semester_id=semester_id
                    )
                    matching_subjects = Subject.objects.filter(
                        course_id=course_id,
                        session_id=session_id,
                        semester_id=semester_id
                    )
                    Subject.objects.filter(course=..., session=..., semester=...)

                else:
                    messages.error(request, "All student fields must be filled.")
                    return render(request, 'users/register.html', {
                        'form': form,
                        'courses': courses,
                        'sessions': sessions,
                        'semesters': semesters,
                    })

            messages.success(request, "Registration successful. Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {
        'form': form,
        'courses': courses,
        'sessions': sessions,
        'semesters': semesters,
    })


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    authentication_form = CustomLoginForm

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return redirect('redirect_user')


@login_required
def redirect_user(request):
    user = request.user
    if user.role == 'dean':
        return redirect('dean_dashboard')
    elif user.role == 'teacher':
        return redirect('teacher_dashboard')
    elif user.role == 'student':
        return redirect('student_dashboard')
    else:
        return redirect('login')



#teacher
@login_required
def teacher_dashboard(request):
    try:
        teacher_profile = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        return render(request, 'users/error.html', {
            'message': "Teacher profile not found. Please contact admin."
        })

    subjects = Subject.objects.filter(teachers=teacher_profile)

    #messages
    messages = Message.objects.filter(for_teachers=True).order_by('-created_at')

    return render(request, 'users/teacher_dashboard.html', {
        'profile': teacher_profile,
        'subjects': subjects,
        'messages': messages,  
    })


#student
@login_required
def student_dashboard(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        return render(request, 'users/error.html', {
            'message': "Student profile not found. Please contact admin."
        })

    subjects = Subject.objects.filter(
        course=student_profile.course,
        session=student_profile.session,
        semester=student_profile.semester
    )

    #messages
    messages = Message.objects.filter(for_students=True).order_by('-created_at')

    return render(request, 'users/student_dashboard.html', {
        'profile': student_profile,
        'subjects': subjects,
        'messages': messages,  
    })


@login_required
def student_attendance_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    student = request.user

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    attendance_records = AttendanceRecord.objects.filter(
        student=student,
        subject=subject
    )

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            attendance_records = attendance_records.filter(date__range=(start, end))
        except ValueError:
            pass

    total_classes = attendance_records.count()
    present_classes = attendance_records.filter(status='Present').count()
    percentage = round((present_classes / total_classes) * 100, 2) if total_classes > 0 else 0

   
    if percentage >= 75:
        css_class = 'text-green'
    elif percentage >= 50:
        css_class = 'text-orange'
    else:
        css_class = 'text-red'

    return render(request, 'users/student_attendance_detail.html', {
        'subject': subject,
        'attendance_records': attendance_records.order_by('date'),
        'start_date': start_date,
        'end_date': end_date,
        'percentage': percentage,
        'total_classes': total_classes,
        'present_classes': present_classes,
        'css_class': css_class, 
    })

#dean
@login_required
def dean_dashboard(request):
    if request.user.role != 'dean':
        return redirect('login')
    return render(request, 'users/dean_dashboard.html')


@login_required
def add_teacher(request):
    if request.user.role != 'dean':
        return redirect('home')

    if request.method == 'POST':
        form = AddTeacherForm(request.POST, request=request)
        if form.is_valid():
            user = form.save(commit=False)
            password = generate_random_password()
            username_base = user.email.split('@')[0]
            user.username = username_base + str(random.randint(100, 999))
            user.set_password(password)
            user.role = 'teacher'
            user.school = request.user.school
            user.save()

            TeacherProfile.objects.create(user=user)

            send_mail(
                'Welcome to the Attendance System',
                f'Your account has been created.\n\nUsername: {user.username}\nPassword: {password}\nLogin here: http://127.0.0.1:8000/login/', #to be replaced by actual login page url before hosting
                'harshitabehere2005@gmail.com',  # Replace with dean's gmail
                [user.email],
                fail_silently=False,
            )

            messages.success(request, 'Teacher added successfully and login credentials emailed.')
            return redirect('view_teachers')
        else:
            messages.error(request, 'Form submission failed. Please correct the errors.')
    else:
        form = AddTeacherForm(request=request)

    return render(request, 'users/add_teacher.html', {'form': form})

@login_required
def view_teachers(request):
    if request.user.role != 'dean':
        return redirect('home')

    teachers = TeacherProfile.objects.filter(user__school=request.user.school).select_related('user')
    return render(request, 'users/view_teachers.html', {'teachers': teachers})




@login_required
def edit_teacher(request, teacher_id):
    if request.user.role != 'dean':
        return redirect('home')

    

    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    user = teacher.user

    if request.method == 'POST':
        form = EditTeacherForm(request.POST, instance=teacher, user_instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher details updated.')
            return redirect('view_teachers')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EditTeacherForm(instance=teacher, user_instance=user)

    return render(request, 'users/edit_teacher.html', {'form': form})


@login_required
def delete_teacher(request, teacher_id):
    if request.user.role != 'dean':
        return redirect('home')

    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    teacher.user.delete()  
    messages.success(request, 'Teacher deleted successfully.')
    return redirect('view_teachers')


@login_required
def manage_students(request):
    if request.user.role != 'dean':
        return redirect('home')

    courses = Course.objects.all()
    sessions = Session.objects.all()
    semesters = Semester.objects.all()

    selected_course = request.GET.get('course')
    selected_session = request.GET.get('session')
    selected_semester = request.GET.get('semester')

    students = StudentProfile.objects.all()

    if selected_course and selected_course != 'All':
        students = students.filter(course_id=selected_course)
    if selected_session and selected_session != 'All':
        students = students.filter(session_id=selected_session)
    if selected_semester and selected_semester != 'All':
        students = students.filter(semester_id=selected_semester)

    form = AddStudentForm()

    if request.method == 'POST':
        form = AddStudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student added successfully.")
            return redirect('manage_students')

    return render(request, 'users/manage_students.html', {
        'courses': courses,
        'sessions': sessions,
        'semesters': semesters,
        'selected_course': selected_course,
        'selected_session': selected_session,
        'selected_semester': selected_semester,
        'students': students,
        'form': form,
        'request': request,
    })

@login_required
def toggle_student_status(request, student_id):
    if request.user.role != 'dean':
        return redirect('home')

    student = get_object_or_404(StudentProfile, id=student_id)
    student.is_active = not student.is_active
    student.save()
    messages.success(request, f"Student {'activated' if student.is_active else 'deactivated'} successfully.")
    return redirect('manage_students')




@login_required
def add_student(request):
    if request.user.role != 'dean':
        return redirect('home')

    if request.method == 'POST':
        form = AddStudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.user.school = request.user.school
            student.user.save()
            student.save()

            generated_password = form.generated_password  

            messages.success(
                request,
                f"Student added successfully. Temporary password: {generated_password}"
            )
            return redirect('manage_students')
    else:
        form = AddStudentForm()

    return render(request, 'users/add_student.html', {'form': form})



#email the password to the user (during adding students manually)-- uncomment and replace

# @login_required
# def add_student(request):
#     if request.user.role != 'dean':
#         return redirect('home')

#     if request.method == 'POST':
#         form = AddStudentForm(request.POST)
#         if form.is_valid():
#             student = form.save(commit=False)
#             student.user.school = request.user.school
#             student.user.save()
#             student.save()

#             # Securely email the password to the student
#             subject = 'Your Student Account Details'
#             message = (
#                 f"Hi {student.user.first_name},\n\n"
#                 f"Your student account has been created successfully.\n\n"
#                 f"Username: {student.user.username}\n"
#                 f"Temporary Password: {form.generated_password}\n\n"
#                 "Please login and change your password as soon as possible."
#             )
#             recipient = [student.user.email]

#             send_mail(subject, message, settings.EMAIL_HOST_USER, recipient, fail_silently=False)

#             messages.success(request, f"Student added successfully. Credentials have been sent via email.")
#             return redirect('manage_students')
#     else:
#         form = AddStudentForm()

#     return render(request, 'users/add_student.html', {'form': form})


@login_required
def bulk_add_students(request):
    if request.method == 'POST' and request.user.role == 'dean':
        course_id = request.POST.get('course')
        session_id = request.POST.get('session')
        semester_id = request.POST.get('semester')
        excel_file = request.FILES.get('excel_file')

        if not all([course_id, session_id, semester_id, excel_file]):
            messages.error(request, "All fields are required.")
            return redirect('manage_students')

        course = Course.objects.get(id=course_id)
        session = Session.objects.get(id=session_id)
        semester = Semester.objects.get(id=semester_id)

        try:
            wb = openpyxl.load_workbook(excel_file)
            sheet = wb.active

            for i, row in enumerate(sheet.iter_rows(min_row=2), start=2): #skipping headers
                email = str(row[0].value).strip()
                first_name = str(row[1].value).strip()
                last_name = str(row[2].value).strip()
                enrollment_number = str(row[3].value).strip()

                if CustomUser.objects.filter(username=email).exists():
                    continue  #skipping duplicates 

                password = CustomUser.objects.make_random_password()
                user = CustomUser.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                    role='student',
                    school=request.user.school
                )

                StudentProfile.objects.create(
                    user=user,
                    course=course,
                    session=session,
                    semester=semester,
                    enrollment_number=enrollment_number
                )

                # for password email - during bulk add
                send_mail(
                    subject="Your Student Account Credentials",
                    message=(
                        f"Hello {first_name},\n\n"
                        f"Your student account has been created.\n"
                        f"Username: {email}\nTemporary Password: {password}\n"
                        "Please change your password after your first login.\n\nThank you."
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )

            messages.success(request, "Students added and notified successfully.")

        except Exception as e:
            messages.error(request, f"Error reading Excel file: {str(e)}")

        return redirect('manage_students')


@login_required
def promote_students(request):
    if request.method == "POST":
        course_id = request.POST.get("course_id")
        session_id = request.POST.get("session_id")
        semester_id = request.POST.get("semester_id")
        selected_ids = request.POST.getlist("selected_students")

        if not semester_id:
            messages.error(request, "Please select a semester to promote.")
            return redirect('manage_students')

        
        current_semester = get_object_or_404(Semester, id=semester_id)

        
        students = StudentProfile.objects.filter(
            course_id=course_id,
            session_id=session_id,
            semester_id=semester_id
        )

        
        if selected_ids:
            students = students.filter(id__in=selected_ids)

        
        try:
            next_semester = Semester.objects.get(
                course=current_semester.course,
                session=current_semester.session,
                order=current_semester.order + 1
            )
        except Semester.DoesNotExist:
            messages.warning(request, "No next semester found for promotion.")  #not working
            return redirect('manage_students')

    
        promoted_count = 0
        for student in students:
            student.semester = next_semester
            student.save()
            promoted_count += 1

        messages.success(request, f"{promoted_count} student(s) promoted to {next_semester.name}.")
        return redirect('manage_students')

    
    messages.error(request, "Invalid request method.")
    return redirect('manage_students')
    
@login_required
def edit_student(request, student_id):
    if request.user.role != 'dean':
        return redirect('home')

    student_profile = get_object_or_404(StudentProfile, id=student_id)
    student_user = student_profile.user

    if request.method == 'POST':
        form = EditStudentForm(request.POST, instance=student_profile, user_instance=student_user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully.')
            return redirect('manage_students')
    else:
        form = EditStudentForm(instance=student_profile, user_instance=student_user)

    return render(request, 'users/edit_student.html', {'form': form})



@login_required
def delete_student(request, student_id):
    if request.user.role != 'dean':
        messages.error(request, "You don't have permission to delete students.")
        return redirect('manage_students') 

    student = get_object_or_404(StudentProfile, id=student_id)

    # deleting associated user
    user = student.user
    student.delete()
    user.delete()

    messages.success(request, f"Student '{user.username}' deleted successfully.")
    return redirect('manage_students') 