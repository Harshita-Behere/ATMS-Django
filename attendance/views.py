from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.contrib import messages
from calendar import monthrange
from datetime import date
from academics.models import Subject
from users.models import StudentProfile
from .models import AttendanceRecord

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

    students = StudentProfile.objects.filter(
        course=subject.course,
        session=subject.session,
        semester=subject.semester
    )

    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'Absent')
            attendance_record, created = AttendanceRecord.objects.get_or_create(
                student=student.user,
                subject=subject,
                teacher=request.user,
                session=subject.session,
                semester=subject.semester,
                date=selected_date,
                defaults={'status': status}
            )
            if not created:
                attendance_record.status = status
                attendance_record.save()

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
