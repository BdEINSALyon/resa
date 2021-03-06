from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from bookings.adhesion import AdhesionAPI


@login_required
def api_va(request, va_key):
    va_info = AdhesionAPI.get_va(va_key)
    va_info = {key: va_info[key] for key in ['first_name', 'last_name', 'email', 'phone']}
    return JsonResponse(va_info)
