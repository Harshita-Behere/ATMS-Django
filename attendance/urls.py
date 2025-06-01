from django.urls import path, re_path
from . import views
from .views import dean_view_attendance, teacher_view_attendance

app_name = "attendance"

urlpatterns = [
    path('attendance/calendar/<int:subject_id>/', views.attendance_calendar_redirect, name='attendance_calendar_redirect'),
    path('mark/<int:subject_id>/', views.mark_attendance, name='mark_today_attendance'),
    re_path(r'^mark/(?P<subject_id>\d+)(?:/(?P<date_str>[^/]+))?/$', views.mark_attendance, name='mark_attendance'),
    path('attendance/calendar/<int:subject_id>/<int:year>/<int:month>/', views.attendance_calendar, name='attendance_calendar'),
    path('dean/view-attendance/', dean_view_attendance, name='dean_view_attendance'),
    path('ajax/load-sessions/', views.ajax_load_sessions, name='ajax_load_sessions'),
    path('ajax/load-semesters/', views.ajax_load_semesters, name='ajax_load_semesters'),
    path('teacher/view-attendance/<int:subject_id>/', teacher_view_attendance, name='teacher_view_attendance'),
    path('download-attendance/<int:subject_id>/', views.download_teacher_attendance_pdf, name='download_teacher_attendance_pdf'),
    path('dean/download-attendance-pdf/', views.dean_download_attendance_pdf, name='dean_download_attendance_pdf'),

]
