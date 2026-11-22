from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from .decorators import role_required


class CustomLoginView(auth_views.LoginView):
    """Login ke baad role ke hisaab se redirect."""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True  

    def get_success_url(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return '/dashboard/'
        return '/dashboard/'
    


class CustomLogoutView(auth_views.LogoutView):
    """Logout ke baad login page pe bhejo."""
    next_page = 'login'


@login_required
def dashboard(request):
    """
    Role-wise dashboard with real data.
    """
    from reports.utils import (
        get_dashboard_admin,
        get_dashboard_supervisor,
        get_dashboard_qc,
        get_dashboard_operator,
    )

    role = request.user.role
    context = {'user': request.user}

    if role == 'ADMIN':
        context.update(get_dashboard_admin())
        return render(request, 'accounts/dashboard_admin.html', context)
    elif role == 'SUPERVISOR':
        context.update(get_dashboard_supervisor(request.user))
        return render(request, 'accounts/dashboard_supervisor.html', context)
    elif role == 'QC':
        context.update(get_dashboard_qc(request.user))
        return render(request, 'accounts/dashboard_qc.html', context)
    elif role == 'OPERATOR':
        context.update(get_dashboard_operator(request.user))
        return render(request, 'accounts/dashboard_operator.html', context)

    return render(request, 'accounts/dashboard.html', context)