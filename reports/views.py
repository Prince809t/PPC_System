from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .utils import (
    get_operator_performance,
    get_team_performance,
    get_order_quality_summary,
)
from teams.models import Team, Operator
from planning.models import Order
from accounts.decorators import role_required


@login_required
@role_required('ADMIN', 'SUPERVISOR')
def operator_performance_list(request):
    """
    Saare operators ka performance — date filter ke saath.
    """
    # Default: last 30 din
    end_date_str = request.GET.get('end_date', date.today().isoformat())
    start_date_str = request.GET.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    team_filter = request.GET.get('team', '')

    from datetime import datetime
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    operators = Operator.objects.filter(is_active=True).select_related('team')
    if team_filter:
        operators = operators.filter(team_id=team_filter)

    performances = [get_operator_performance(op, start_date, end_date) for op in operators]
    # Sort by score (high to low)
    performances.sort(key=lambda x: x['score'], reverse=True)

    teams = Team.objects.filter(is_active=True)

    context = {
        'performances': performances,
        'teams': teams,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'team_filter': team_filter,
    }
    return render(request, 'reports/operator_performance.html', context)


@login_required
@role_required('ADMIN', 'SUPERVISOR')
def operator_performance_detail(request, pk):
    """
    Ek operator ka detailed performance report.
    """
    operator = get_object_or_404(Operator, pk=pk)

    # Default: last 30 din
    end_date_str = request.GET.get('end_date', date.today().isoformat())
    start_date_str = request.GET.get('start_date', (date.today() - timedelta(days=30)).isoformat())

    from datetime import datetime
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    perf = get_operator_performance(operator, start_date, end_date)

    context = {
        'perf': perf,
        'start_date': start_date_str,
        'end_date': end_date_str,
    }
    return render(request, 'reports/operator_performance_detail.html', context)


@login_required
@role_required('ADMIN', 'SUPERVISOR')
def team_performance(request):
    """
    Saari teams ka aggregate performance.
    """
    end_date_str = request.GET.get('end_date', date.today().isoformat())
    start_date_str = request.GET.get('start_date', (date.today() - timedelta(days=30)).isoformat())

    from datetime import datetime
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    teams = Team.objects.filter(is_active=True)
    team_perfs = [get_team_performance(t, start_date, end_date) for t in teams]

    context = {
        'team_perfs': team_perfs,
        'start_date': start_date_str,
        'end_date': end_date_str,
    }
    return render(request, 'reports/team_performance.html', context)


@login_required
@role_required('ADMIN', 'SUPERVISOR', 'QC')
def order_quality(request):
    """
    Har order ka quality summary.
    """
    orders = Order.objects.all().order_by('-created_at')[:50]
    order_summaries = [get_order_quality_summary(o) for o in orders]

    context = {
        'order_summaries': order_summaries,
    }
    return render(request, 'reports/order_quality.html', context)