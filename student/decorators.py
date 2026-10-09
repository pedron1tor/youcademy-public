from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def student_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.occupation == "teacher":
            return redirect("dashboard")
        elif request.user.occupation == "Not specified":
            return redirect("onboard")
        elif request.user.occupation == "":
            return redirect("onboard")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
