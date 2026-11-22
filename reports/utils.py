from datetime import date, timedelta
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate
from teams.models import Operator
from production.models import OutputLog, DowntimeLog
from quality.models import InitialQualityFault, FinalQualityFault


def get_operator_performance(operator, start_date=None, end_date=None):
    """
    Ek operator ka pura performance calculate karo.
    """
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    # ===== 1. OUTPUT =====
    output_logs = OutputLog.objects.filter(
        operator=operator,
        date__range=[start_date, end_date]
    )
    total_pieces = output_logs.aggregate(total=Sum('pieces_completed'))['total'] or 0
    total_output_hours = 0
    for log in output_logs:
        total_output_hours += log.total_hours

    # ===== 2. DOWNTIME =====
    downtime_logs = DowntimeLog.objects.filter(
        operator=operator,
        date__range=[start_date, end_date]
    )
    total_downtime_hours = 0
    for log in downtime_logs:
        total_downtime_hours += log.total_hours

    # ===== 3. INITIAL FAULTS =====
    initial_faults = InitialQualityFault.objects.filter(
        operator_at_fault=operator,
        report__date__range=[start_date, end_date]
    )
    initial_defect_pieces = initial_faults.aggregate(total=Sum('qty'))['total'] or 0
    initial_fault_count = initial_faults.count()

    # ===== 4. FINAL FAULTS =====
    final_faults = FinalQualityFault.objects.filter(
        operator_at_fault=operator,
        report__date__range=[start_date, end_date]
    )
    final_defect_pieces = final_faults.aggregate(total=Sum('qty'))['total'] or 0
    final_fault_count = final_faults.count()

    # Repeat faults (jo Y the)
    repeat_faults = final_faults.filter(repeat_fault='Y')
    repeat_fault_pieces = repeat_faults.aggregate(total=Sum('qty'))['total'] or 0

    # ===== 5. REWORK HOURS =====
    rework_hours = round((initial_defect_pieces + final_defect_pieces) * 0.05, 2)

    # ===== 6. SCORE CALCULATE =====
    score = 100.0
    score -= (initial_defect_pieces + final_defect_pieces) * 0.5
    score -= repeat_fault_pieces * 1.0
    score -= total_downtime_hours * 1.0
    score -= rework_hours * 2.0

    if operator.target_per_hour and operator.team:
        planned = operator.target_per_hour * float(operator.team.shift_hours)
        if total_pieces >= planned:
            score += 5

    score = max(0, min(100, round(score, 2)))

    # ===== 7. GRADE =====
    if score >= 90:
        grade = 'A+'
        grade_color = 'success'
    elif score >= 80:
        grade = 'A'
        grade_color = 'success'
    elif score >= 70:
        grade = 'B'
        grade_color = 'primary'
    elif score >= 60:
        grade = 'C'
        grade_color = 'warning'
    elif score >= 50:
        grade = 'D'
        grade_color = 'warning'
    else:
        grade = 'F'
        grade_color = 'danger'

    return {
        'operator': operator,
        'start_date': start_date,
        'end_date': end_date,
        'total_pieces': total_pieces,
        'total_output_hours': round(total_output_hours, 2),
        'total_downtime_hours': round(total_downtime_hours, 2),
        'initial_defect_pieces': initial_defect_pieces,
        'initial_fault_count': initial_fault_count,
        'final_defect_pieces': final_defect_pieces,
        'final_fault_count': final_fault_count,
        'repeat_fault_pieces': repeat_fault_pieces,
        'rework_hours': rework_hours,
        'score': score,
        'grade': grade,
        'grade_color': grade_color,
    }


def get_team_performance(team, start_date=None, end_date=None):
    """
    Ek team ke saare operators ka aggregate performance.
    """
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    operators = Operator.objects.filter(team=team, is_active=True)
    operator_scores = []

    for op in operators:
        perf = get_operator_performance(op, start_date, end_date)
        operator_scores.append(perf)

    if operator_scores:
        avg_score = round(sum(p['score'] for p in operator_scores) / len(operator_scores), 2)
        total_pieces = sum(p['total_pieces'] for p in operator_scores)
        total_defects = sum(p['initial_defect_pieces'] + p['final_defect_pieces'] for p in operator_scores)
        total_repeat = sum(p['repeat_fault_pieces'] for p in operator_scores)
    else:
        avg_score = 0
        total_pieces = 0
        total_defects = 0
        total_repeat = 0

    return {
        'team': team,
        'operator_scores': operator_scores,
        'avg_score': avg_score,
        'total_pieces': total_pieces,
        'total_defects': total_defects,
        'total_repeat_faults': total_repeat,
        'operator_count': len(operator_scores),
    }


def get_order_quality_summary(order):
    """
    Ek order ka pura quality summary — PPC-04 + PPC-05 se.
    """
    from quality.models import InitialQualityReport, FinalQualityReport

    initial_reports = InitialQualityReport.objects.filter(order=order)
    final_reports = FinalQualityReport.objects.filter(order=order)

    total_checked = sum(r.total_qty_checked for r in initial_reports)
    total_defective_initial = sum(r.total_qty_defective for r in initial_reports)
    total_rework_sent = sum(r.qty_sent_for_rework for r in initial_reports)
    total_rejected = sum(r.qty_rejected for r in initial_reports)

    total_presented_final = sum(r.qty_presented_at_final for r in final_reports)
    total_defective_final = sum(r.qty_defective_at_final for r in final_reports)
    total_repeat_faults = sum(r.repeat_faults_failed_rework for r in final_reports)
    total_rework_hours = sum(float(r.total_rework_hours or 0) for r in final_reports)
    total_passed_packing = sum(r.qty_passed_to_packing for r in final_reports)

    return {
        'order': order,
        'total_checked': total_checked,
        'total_defective_initial': total_defective_initial,
        'total_rework_sent': total_rework_sent,
        'total_rejected': total_rejected,
        'total_presented_final': total_presented_final,
        'total_defective_final': total_defective_final,
        'total_repeat_faults': total_repeat_faults,
        'total_rework_hours': round(total_rework_hours, 2),
        'total_passed_packing': total_passed_packing,
    }


def get_dashboard_admin():
    """
    Admin dashboard ke liye saara summary data.
    """
    from teams.models import Team, Operator
    from planning.models import Order
    from production.models import OutputLog, DowntimeLog
    from quality.models import InitialQualityReport, FinalQualityReport

    total_teams = Team.objects.filter(is_active=True).count()
    total_operators = Operator.objects.filter(is_active=True).count()
    total_orders = Order.objects.exclude(status='COMPLETED').count()

    total_output = OutputLog.objects.aggregate(total=Sum('pieces_completed'))['total'] or 0

    total_downtime = 0
    for log in DowntimeLog.objects.all():
        total_downtime += log.total_hours

    initial_reports = InitialQualityReport.objects.all()
    total_checked = sum(r.total_qty_checked for r in initial_reports)
    total_defective = sum(r.total_qty_defective for r in initial_reports)
    overall_defect_rate = round((total_defective / total_checked) * 100, 2) if total_checked > 0 else 0

    final_reports = FinalQualityReport.objects.all()
    total_rework_hours = sum(float(r.total_rework_hours or 0) for r in final_reports)

    team_output = []
    for team in Team.objects.filter(is_active=True)[:6]:
        output = OutputLog.objects.filter(team=team).aggregate(
            total=Sum('pieces_completed')
        )['total'] or 0
        team_output.append({
            'name': team.name,
            'output': output,
        })

    trend_labels = []
    trend_data = []
    for i in range(6, -1, -1):
        day = date.today() - timedelta(days=i)
        trend_labels.append(day.strftime('%d %b'))
        day_reports = InitialQualityReport.objects.filter(date=day)
        day_checked = sum(r.total_qty_checked for r in day_reports)
        day_defective = sum(r.total_qty_defective for r in day_reports)
        rate = round((day_defective / day_checked) * 100, 2) if day_checked > 0 else 0
        trend_data.append(rate)

    return {
        'total_teams': total_teams,
        'total_operators': total_operators,
        'total_orders': total_orders,
        'total_output': total_output,
        'total_downtime': round(total_downtime, 2),
        'overall_defect_rate': overall_defect_rate,
        'total_rework_hours': round(total_rework_hours, 2),
        'team_output': team_output,
        'trend_labels': trend_labels,
        'trend_data': trend_data,
    }


def get_dashboard_supervisor(user):
    """
    Supervisor dashboard — apni team ka data.
    """
    from teams.models import Team, Operator
    from production.models import OutputLog, DowntimeLog

    team = Team.objects.filter(supervisor=user).first()
    if not team:
        return {
            'no_team': True,
            'team': None,
        }

    today = date.today()

    today_output = OutputLog.objects.filter(
        team=team, date=today
    ).aggregate(total=Sum('pieces_completed'))['total'] or 0

    today_downtime = 0
    for log in DowntimeLog.objects.filter(team=team, date=today):
        today_downtime += log.total_hours

    operators_count = Operator.objects.filter(team=team, is_active=True).count()
    perf = get_team_performance(team)

    return {
        'no_team': False,
        'team': team,
        'today_output': today_output,
        'today_downtime': round(today_downtime, 2),
        'operators_count': operators_count,
        'avg_score': perf['avg_score'],
        'operator_scores': perf['operator_scores'],
    }


def get_dashboard_qc(user):
    """
    QC dashboard — pending inspections, defect trends.
    """
    from production.models import OutputLog
    from quality.models import InitialQualityReport, FinalQualityReport
    from quality.models import InitialQualityFault

    pending_qc = OutputLog.objects.filter(qc_checked=False).count()

    total_initial = InitialQualityReport.objects.count()
    total_final = FinalQualityReport.objects.count()

    initial_reports = InitialQualityReport.objects.all()
    total_checked = sum(r.total_qty_checked for r in initial_reports)
    total_defective = sum(r.total_qty_defective for r in initial_reports)
    overall_defect_rate = round((total_defective / total_checked) * 100, 2) if total_checked > 0 else 0

    top_faults = InitialQualityFault.objects.values(
        'fault_code__code', 'fault_code__name'
    ).annotate(total_qty=Sum('qty')).order_by('-total_qty')[:5]

    fault_labels = [f"{f['fault_code__code']}" for f in top_faults if f['fault_code__code']]
    fault_data = [f['total_qty'] or 0 for f in top_faults]

    recent_initial = InitialQualityReport.objects.select_related('order').order_by('-created_at')[:5]
    recent_final = FinalQualityReport.objects.select_related('order').order_by('-created_at')[:5]

    return {
        'pending_qc': pending_qc,
        'total_initial': total_initial,
        'total_final': total_final,
        'overall_defect_rate': overall_defect_rate,
        'fault_labels': fault_labels,
        'fault_data': fault_data,
        'recent_initial': recent_initial,
        'recent_final': recent_final,
    }


def get_dashboard_operator(user):
    """
    Operator dashboard — apna aaj ka data.
    """
    from production.models import OutputLog, DowntimeLog

    operator = getattr(user, 'operator_profile', None)
    if not operator:
        return {
            'no_profile': True,
        }

    today = date.today()

    today_output = OutputLog.objects.filter(
        operator=operator, date=today
    ).aggregate(total=Sum('pieces_completed'))['total'] or 0

    today_downtime = 0
    for log in DowntimeLog.objects.filter(operator=operator, date=today):
        today_downtime += log.total_hours

    perf = get_operator_performance(operator)

    return {
        'no_profile': False,
        'operator': operator,
        'today_output': today_output,
        'today_downtime': round(today_downtime, 2),
        'planned_per_day': operator.planned_per_day,
        'perf': perf,
    }