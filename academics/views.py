from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import AddSubjectForm
from .forms import AddSessionForm
from .forms import AddSemesterForm
from .forms import AddSubjectForm
from .models import Subject, Course, Session, Semester,Subject
from django.contrib.auth.decorators import login_required
from .forms import AddCourseForm 
from django.contrib import messages

#course views
@login_required
def add_course(request):
    if request.user.role != 'dean':
        return redirect('home')

    if request.method == 'POST':
        form = AddCourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Course added successfully!")
            return redirect('add_course')
        else:
            messages.error(request, "Failed to add course. Please fix the errors below.")
    else:
        form = AddCourseForm()

    courses = Course.objects.all()  # for viewing below the form
    return render(request, 'academics/add_course.html', {'form': form, 'courses': courses})


@login_required
def edit_course(request, course_id):
    if request.user.role != 'dean':
        return redirect('home')

    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = AddCourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully.")
            return redirect('add_course')
        else:
            messages.error(request, "Failed to update course.")
    else:
        form = AddCourseForm(instance=course)

    return render(request, 'academics/edit_course.html', {'form': form, 'course': course})


@login_required
def delete_course(request, course_id):
    if request.user.role != 'dean':
        return redirect('home')

    course = get_object_or_404(Course, id=course_id)
    course.delete()
    messages.success(request, "Course deleted successfully.")
    return redirect('add_course')


@login_required
def view_courses(request):
    if request.user.role != 'dean':
        return redirect('home')

    courses = Course.objects.all()
    return render(request, 'academics/view_courses.html', {'courses': courses})


#session views
@login_required
def add_session(request):
    if request.user.role != 'dean':
        return redirect('home')

    if request.method == 'POST':
        form = AddSessionForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            course = form.cleaned_data['course']
            if Session.objects.filter(name=name, course=course).exists():
                messages.error(request, "This session already exists for the selected course.")
            else:
                form.save()
                messages.success(request, "Session added successfully.")
                return redirect('add_session')
    else:
        form = AddSessionForm()
    return render(request, 'academics/add_session.html', {'form': form})


@login_required
def view_sessions(request):
    if request.user.role != 'dean':
        return redirect('home')

    sessions = Session.objects.all()
    return render(request, 'academics/view_sessions.html', {'sessions': sessions})


@login_required
def edit_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)

    if request.method == 'POST':
        form = AddSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, "Session updated successfully.")
            return redirect('view_sessions')
    else:
        form = AddSessionForm(instance=session)

    return render(request, 'academics/edit_session.html', {'form': form})


@login_required
def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    session.delete()
    messages.success(request, "Session deleted successfully.")
    return redirect('view_sessions')

#semester views
from django.db.models import Max

@login_required
def add_semester(request):
    if request.user.role != 'dean':
        return redirect('home')

    if request.method == 'POST':
        form = AddSemesterForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            course = form.cleaned_data['course']
            session = form.cleaned_data['session']

            # Check if semester already exists
            if Semester.objects.filter(name=name, course=course, session=session).exists():
                messages.error(request, "Semester already exists.")
            else:
                # Get the max order for this course & session, default 0 if none
                max_order = Semester.objects.filter(course=course, session=session).aggregate(
                    Max('order')
                )['order__max'] or 0

                semester = form.save(commit=False)
                semester.order = max_order + 1  # Assign next order number
                semester.save()

                messages.success(request, "Semester added successfully.")
                return redirect('view_semesters')
    else:
        form = AddSemesterForm()

    return render(request, 'academics/add_semester.html', {'form': form})

@login_required
def view_semesters(request):
    if request.user.role != 'dean':
        return redirect('home')
    
    semesters = Semester.objects.all().order_by('course', 'session', 'name')
    return render(request, 'academics/view_semesters.html', {'semesters': semesters})

@login_required
def edit_semester(request, semester_id):
    if request.user.role != 'dean':
        return redirect('home')

    semester = Semester.objects.get(id=semester_id)
    form = AddSemesterForm(request.POST or None, instance=semester)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Semester updated successfully.")
        return redirect('view_semesters')

    return render(request, 'academics/edit_semester.html', {'form': form})

@login_required
def delete_semester(request, semester_id):
    if request.user.role != 'dean':
        return redirect('home')

    semester = Semester.objects.get(id=semester_id)
    semester.delete()
    messages.success(request, "Semester deleted successfully.")
    return redirect('view_semesters')

#subject views
@login_required
def add_subject(request):
    if request.user.role != 'dean':
        return redirect('home')

    if request.method == 'POST':
        form = AddSubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()  
            messages.success(request, "Subject added successfully.")
            return redirect('add_subject')
    else:
        form = AddSubjectForm()

    return render(request, 'academics/add_subject.html', {'form': form})


@login_required
def view_subjects(request):
    if request.user.role != 'dean':
        return redirect('home')

    subjects = Subject.objects.all().order_by('course', 'session', 'semester', 'name')
    return render(request, 'academics/view_subjects.html', {'subjects': subjects})

@login_required
def edit_subject(request, subject_id):
    if request.user.role != 'dean':
        return redirect('home')

    subject = Subject.objects.get(id=subject_id)
    form = AddSubjectForm(request.POST or None, instance=subject)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Subject updated successfully.")
        return redirect('view_subjects')

    return render(request, 'academics/edit_subject.html', {'form': form})

@login_required
def delete_subject(request, subject_id):
    if request.user.role != 'dean':
        return redirect('home')

    subject = Subject.objects.get(id=subject_id)
    subject.delete()
    messages.success(request, "Subject deleted successfully.")
    return redirect('view_subjects')

