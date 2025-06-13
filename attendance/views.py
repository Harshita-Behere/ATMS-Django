from datetime import date
from calendar import monthrange
import io

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.http import (
    JsonResponse,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseBadRequest,
)

from django.db.models import Count, Q
from django.template.loader import get_template, render_to_string

from xhtml2pdf import pisa      #for downloading att report

from users.models import CustomUser, TeacherProfile, StudentProfile
from academics.models import Course, Session, Semester, Subject, Holiday
from .models import AttendanceRecord

from .forms import DeanAttendanceFilterForm


def ajax_load_sessions(request):
    course_id = request.GET.get('course_id')
    sessions = Session.objects.filter(course_id=course_id).values('id', 'name')
    return JsonResponse(list(sessions), safe=False)

def ajax_load_semesters(request):
    session_id = request.GET.get('session_id')
    semesters = Semester.objects.filter(session_id=session_id).values('id', 'name')
    return JsonResponse(list(semesters), safe=False)


@login_required
def attendance_calendar_redirect(request, subject_id):
    today = timezone.localdate()
    return redirect('attendance:attendance_calendar', subject_id=subject_id, year=today.year, month=today.month)

@login_required
def attendance_calendar(request, subject_id, year=None, month=None):
    subject = get_object_or_404(Subject, id=subject_id)
    today = timezone.localdate()

    if year is None or month is None:
        return redirect('attendance:attendance_calendar', subject_id=subject_id, year=today.year, month=today.month)

    year = int(year)
    month = int(month)
    num_days = monthrange(year, month)[1]

    days = []
    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        records = AttendanceRecord.objects.filter(subject=subject, date=current_date)
        daily_status = {record.student_id: record.status for record in records}
        days.append({'date': current_date, 'status_dict': daily_status})

    students = StudentProfile.objects.filter(
        course=subject.course,
        session=subject.session,
        semester=subject.semester
    )

    context = {
        'subject': subject,
        'year': year,
        'month': month,
        'days': days,
        'students': students,
    }
    return render(request, 'attendance/attendance_calendar.html', context)




@login_required
def mark_attendance(request, subject_id, date_str=None):
    subject = get_object_or_404(Subject, id=subject_id)
    selected_date = parse_date(date_str) if date_str else timezone.localdate()

    
    if date_str and not selected_date:
        messages.error(request, "Invalid date format.")
        today = date.today()
        return redirect('attendance:attendance_calendar', subject_id=subject.id, year=today.year, month=today.month)

    # Check if weekend 
    if selected_date.weekday() in (5, 6):
        messages.warning(request, f"{selected_date.strftime('%A, %b %d, %Y')} is a weekend. Attendance cannot be marked.")
        return redirect('attendance:attendance_calendar', subject_id=subject.id, year=selected_date.year, month=selected_date.month)

    # Check if declared holiday
    is_holiday = Holiday.objects.filter(date=selected_date).exists()
    if is_holiday:
        messages.warning(request, f"{selected_date.strftime('%A, %b %d, %Y')} is a declared holiday. Attendance cannot be marked.")
        return redirect('attendance:attendance_calendar', subject_id=subject.id, year=selected_date.year, month=selected_date.month)

    
    students = StudentProfile.objects.filter(
        course=subject.course,
        session=subject.session,
        semester=subject.semester
    )

    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'Absent')
            try:
                attendance_record, created = AttendanceRecord.objects.get_or_create(
                    student=student.user,
                    subject=subject,
                    date=selected_date,
                    defaults={
                        'status': status,
                        'teacher': request.user,
                        'session': subject.session,
                        'semester': subject.semester,
                    }
                )
                if not created:
                    attendance_record.status = status
                    attendance_record.teacher = request.user  # optional: update teacher if needed
                    attendance_record.save()

            except IntegrityError:
                messages.error(request, f"Attendance for {student.user.get_full_name()} on {selected_date} already exists and couldn't be saved again.")
                continue


        messages.success(request, f"Attendance for {selected_date} saved successfully.")
        return redirect('attendance:attendance_calendar', subject_id=subject.id, year=selected_date.year, month=selected_date.month)

    attendance_records = AttendanceRecord.objects.filter(subject=subject, date=selected_date)
    attendance_dict = {record.student_id: record.status for record in attendance_records}

    return render(request, 'attendance/mark_attendance.html', {
        'subject': subject,
        'students': students,
        'attendance_dict': attendance_dict,
        'date': selected_date,
    })


def dean_view_attendance(request):
    students = []
    subjects = []
    attendance_data = {}

    if request.method == 'POST':
        form = DeanAttendanceFilterForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data['course']
            session = form.cleaned_data['session']
            semester = form.cleaned_data['semester']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            subjects = Subject.objects.filter(course=course, session=session, semester=semester)
            students = StudentProfile.objects.filter(course=course, session=session, semester=semester)

            for student in students:
                attendance_data[student.id] = {}
                for subject in subjects:
                    total_classes = AttendanceRecord.objects.filter(
                        student=student.user,
                        subject=subject,
                        date__range=[start_date, end_date]
                    ).count()

                    present_count = AttendanceRecord.objects.filter(
                        student=student.user,
                        subject=subject,
                        status='Present',
                        date__range=[start_date, end_date]
                    ).count()

                    attendance_data[student.id][subject.name] = {
                        'present': present_count,
                        'total': total_classes,
                        'percentage': round((present_count / total_classes) * 100, 2) if total_classes > 0 else 0
                    }
    else:
        form = DeanAttendanceFilterForm()

    context = {
        'form': form,
        'students': students,
        'subjects': subjects,
        'attendance_data': attendance_data
    }
    return render(request, 'attendance/dean_view_attendance.html', context)


def dean_download_attendance_pdf(request):
    course_id = request.GET.get('course')
    session_id = request.GET.get('session')
    semester_id = request.GET.get('semester')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not all([course_id, session_id, semester_id, start_date, end_date]):
        return HttpResponseBadRequest("Missing required filter parameters.")

    course = Course.objects.get(id=course_id)
    session = Session.objects.get(id=session_id)
    semester = Semester.objects.get(id=semester_id)

    subjects = Subject.objects.filter(course=course, session=session, semester=semester)
    students = StudentProfile.objects.filter(course=course, session=session, semester=semester)

    attendance_data = {}

    for student in students:
        attendance_data[student.id] = {}
        for subject in subjects:
            total_classes = AttendanceRecord.objects.filter(
                student=student.user,
                subject=subject,
                date__range=[start_date, end_date]
            ).count()

            present_count = AttendanceRecord.objects.filter(
                student=student.user,
                subject=subject,
                status='Present',
                date__range=[start_date, end_date]
            ).count()

            attendance_data[student.id][subject.name] = {
                'present': present_count,
                'total': total_classes,
                'percentage': round((present_count / total_classes) * 100, 2) if total_classes > 0 else 0
            }

    context = {
        'students': students,
        'subjects': subjects,
        'attendance_data': attendance_data,
        'filters': {
            'course': course,
            'session': session,
            'semester': semester,
            'start_date': start_date,
            'end_date': end_date,
        }
    }

    html = render_to_string('attendance/pdf_dean_template.html', context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="attendance_{course.name}_{session.name}_{semester.name}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response


@login_required
def teacher_view_attendance(request, subject_id):
    user = request.user

    
    try:
        teacher_profile = user.teacherprofile
    except TeacherProfile.DoesNotExist:
        return HttpResponseForbidden("No teacher profile found.")

    subject = get_object_or_404(Subject, id=subject_id)


    if not subject.teachers.filter(id=teacher_profile.id).exists():
        return HttpResponseForbidden("You are not assigned to this subject.")

    students = CustomUser.objects.filter(
        role='student',
        studentprofile__course=subject.course,
        studentprofile__session=subject.session,
        studentprofile__semester=subject.semester
    ).distinct()

    attendance_data = {}
    for student in students:
        total_classes = AttendanceRecord.objects.filter(student=student, subject=subject).count()
        present_count = AttendanceRecord.objects.filter(student=student, subject=subject, status='Present').count()

        percentage = round((present_count / total_classes) * 100, 2) if total_classes > 0 else 0
        attendance_data[student.id] = {
            'present': present_count,
            'total': total_classes,
            'percentage': percentage,
            'student': student,
        }

    context = {
        'subject': subject,
        'attendance_data': attendance_data.values(),
    }

    return render(request, 'attendance/teacher_view_attendance.html', context)




def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


@login_required
def download_teacher_attendance_pdf(request, subject_id):
    user = request.user
    teacher_profile = getattr(user, 'teacherprofile', None)
    if not teacher_profile:
        return HttpResponseForbidden("No teacher profile found.")

    subject = get_object_or_404(Subject, id=subject_id)

    if not subject.teachers.filter(id=teacher_profile.id).exists():
        return HttpResponseForbidden("You are not assigned to this subject.")

    students = CustomUser.objects.filter(
        role='student',
        studentprofile__course=subject.course,
        studentprofile__session=subject.session,
        studentprofile__semester=subject.semester
    ).distinct()

    attendance_data = []
    for student in students:
        total = AttendanceRecord.objects.filter(student=student, subject=subject).count()
        present = AttendanceRecord.objects.filter(student=student, subject=subject, status='Present').count()
        percentage = round((present / total) * 100, 2) if total > 0 else 0
        attendance_data.append({
            'student': student,
            'present': present,
            'total': total,
            'percentage': percentage,
        })

    context = {
        'subject': subject,
        'attendance_data': attendance_data
    }

    return render_to_pdf('attendance/pdf_template.html', context)
