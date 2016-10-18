from bookings.models import ResourceCategory, Resource


def resource_and_category_list(request):
    resource_category_list = ResourceCategory.objects.all().order_by('name')
    resource_list = Resource.objects.all().order_by('name')

    return {
        'all_resource_categories': resource_category_list,
        'all_resources': resource_list
    }
