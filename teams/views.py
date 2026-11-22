
# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Team, Operator
from accounts.decorators import role_required


@login_required
@role_required('ADMIN', 'SUPERVISOR')
def team_layout_list(request):
    """
    Saari teams ki list — jahan se supervisor apni team chune.
    """
    teams = Team.objects.filter(is_active=True).order_by('name')
    return render(request, 'teams/team_layout_list.html', {'teams': teams})


@login_required
@role_required('ADMIN', 'SUPERVISOR')
def team_layout_detail(request, team_id):
    """
    PPC-02 — Team Layout Plan (ek team ka standing setup).
    Online aur Offline operators alag sections me.
    """
    team = get_object_or_404(Team, pk=team_id)

    # Online operators (silai line)
    online_operators = Operator.objects.filter(
        team=team,
        operator_type='ONLINE',
        is_active=True
    ).select_related('default_operation', 'default_machine').order_by('full_name')

    # Offline operators (finishing)
    offline_operators = Operator.objects.filter(
        team=team,
        operator_type='OFFLINE',
        is_active=True
    ).select_related('default_operation', 'default_machine').order_by('full_name')

    # Totals calculate karo (PDF ke hisaab se)
    online_target = sum(op.target_per_hour for op in online_operators)
    online_planned = sum(op.planned_per_day for op in online_operators)
    offline_target = sum(op.target_per_hour for op in offline_operators)
    offline_planned = sum(op.planned_per_day for op in offline_operators)

    context = {
        'team': team,
        'online_operators': online_operators,
        'offline_operators': offline_operators,
        'online_target': online_target,
        'online_planned': online_planned,
        'offline_target': offline_target,
        'offline_planned': offline_planned,
    }
    return render(request, 'teams/team_layout_detail.html', context)