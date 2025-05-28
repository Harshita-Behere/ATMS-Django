from django.shortcuts import render
from django.http import HttpResponse

def apply_leave(request):
    return HttpResponse("Apply for leave")

def student_leave_status(request):
    return HttpResponse("View student leave status")

def manage_leaves(request):
    return HttpResponse("Dean: Manage student leaves")

