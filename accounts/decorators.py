# from django.http import HttpResponseForbidden
# from functools import wraps


# def role_required(*allowed_roles):
#     """
#     Decorator factory — sirf allowed roles wale users ko view chalane deta hai.
    
#     Use: @role_required('ADMIN', 'SUPERVISOR')
#     """
#     def decorator(view_func):
#         @wraps(view_func)
#         def wrapper(request, *args, **kwargs):
#             # Login check
#             if not request.user.is_authenticated:
#                 from django.shortcuts import redirect
#                 return redirect('login')

#             # Role check
#             if request.user.role not in allowed_roles and not request.user.is_superuser:
#                 return HttpResponseForbidden(
#                     "<h2>403 Forbidden</h2>"
#                     "<p>Tumhara is page pe access nahi hai.</p>"
#                     "<a href='/dashboard/'>Wapas Dashboard</a>"
#                 )

#             return view_func(request, *args, **kwargs)
#         return wrapper
#     return decorator


from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from functools import wraps


def role_required(*allowed_roles):
    """
    Decorator — sirf allowed roles wale users ko view chalane deta hai.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Login check
            if not request.user.is_authenticated:
                return redirect('login')

            # Role check
            if request.user.role not in allowed_roles and not request.user.is_superuser:
                # Professional 403 page render karo
                return render(request, '403.html', status=403)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator