from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages


def password_change_done(request):
    messages.success(request, "Password changed successfully")
    return render(request, 'bookings/home.html')
