from django.contrib import messages
from django.shortcuts import render


def password_change_done(request):
    messages.success(request, "Password changed successfully")
    return render(request, 'bookings/home.html')
