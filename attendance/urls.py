from django.urls import path, re_path
from . import views

app_name = "attendance"

urlpatterns = [
    path('attendance/calendar/<int:subject_id>/', views.attendance_calendar_redirect, name='attendance_calendar_redirect'),
    path('mark/<int:subject_id>/', views.mark_attendance, name='mark_today_attendance'),  # today's attendance
    re_path(r'^mark/(?P<subject_id>\d+)(?:/(?P<date_str>[^/]+))?/$', views.mark_attendance, name='mark_attendance'),
    path('attendance/calendar/<int:subject_id>/<int:year>/<int:month>/', views.attendance_calendar, name='attendance_calendar'),
]
