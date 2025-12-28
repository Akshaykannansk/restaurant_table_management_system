from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test

def check_group(user, group_names):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=group_names).exists()

def role_required(*group_names):
    """
    Decorator for views that checks whether a user has a specific group/role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            
            if check_group(request.user, group_names):
                return view_func(request, *args, **kwargs)
            
            raise PermissionDenied
        return _wrapped_view
    return decorator
