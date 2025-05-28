from django.urls import path
from . import views

urlpatterns = [
    path('apply/', views.apply_leave, name='apply_leave'),
    path('student/leaves/', views.student_leave_status, name='student_leave_status'),
    path('dean/manage/', views.manage_leaves, name='manage_leaves'),  
]
