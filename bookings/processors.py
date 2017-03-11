from bookings.models import ResourceCategory


def resource_and_category_list(request):
    resource_category_list = ResourceCategory.objects.all()

    return {
        'all_resource_categories': resource_category_list,
    }
