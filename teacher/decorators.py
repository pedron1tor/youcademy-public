from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from asgiref.sync import sync_to_async
def teacher_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.occupation == "student":
            return redirect("student_home")
        elif request.user.occupation == "Not specified": 
            return redirect("onboard")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# async def async_teacher_required(view_func):
#     @wraps(view_func)
#     async def wrapped_view(request, *args, **kwargs):
#         is_teacher = await sync_to_async(lambda: request.user.occupation == "teacher")()
#         if not is_teacher:
#             return redirect("dashboard")
#         return await view_func(request, *args, **kwargs)
#     return wrapped_view
