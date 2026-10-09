from django.conf import settings
from pages.models import Course
def custom_context(request):
    if request.user.is_authenticated:
        if request.user.admin:
          diagnostic = True
          tour = True
        else:
          diagnostic = request.user.diagnostic
          tour = request.user.tour
    else: 
        diagnostic = None
        tour = None
    return {
        'PROD': settings.PROD,
        'user_id' : request.user.id if request.user.is_authenticated else None,
        'name': request.user.name if request.user.is_authenticated else None, 
        'courses': Course.objects.filter(students=request.user) if request.user.is_authenticated else None, 
        'color': request.user.color if request.user.is_authenticated else None, 
        'diagnostic': diagnostic, 
        'tour': tour, 
}