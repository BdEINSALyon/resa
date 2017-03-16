from bookings.models import ResourceCategory


def resource_and_category_list(request):
    if request.user.is_authenticated():
        resource_category_list = ResourceCategory.objects.all()
    else:
        resource_category_list = ResourceCategory.objects.filter(public=True)

    return {
        'all_resource_categories': resource_category_list,
    }
