from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date
from .models import (
    FaultCode,
    InitialQualityReport,
    InitialQualityFault,
    FinalQualityReport,
    FinalQualityFault,
)
from teams.models import Team, Operator, Operation
from planning.models import Order
from accounts.decorators import role_required


@login_required
@role_required('QC', 'ADMIN')
def initial_qc_list(request):
    """Saari PPC-04 reports."""
    reports = InitialQualityReport.objects.select_related(
        'order', 'team', 'qc_inspector'
    ).order_by('-date', '-created_at')
    return render(request, 'quality/initial_qc_list.html', {'reports': reports})


@login_required
@role_required('QC', 'ADMIN')
def initial_qc_create(request):
    """
    Nayi PPC-04 report banao — header + fault lines ek saath.
    """
    if request.method == 'POST':
        try:
            # Header
            order_id = request.POST.get('order')
            team_id = request.POST.get('team') or None
            report_date = request.POST.get('date')
            insp_from = request.POST.get('inspection_from')
            insp_to = request.POST.get('inspection_to')

            qty_presented = int(request.POST.get('qty_presented') or 0)
            total_checked = int(request.POST.get('total_qty_checked') or 0)
            total_passed = int(request.POST.get('total_qty_passed') or 0)

            report = InitialQualityReport.objects.create(
                order_id=order_id,
                team_id=team_id,
                date=report_date,
                qc_inspector=request.user,
                inspection_from=insp_from,
                inspection_to=insp_to,
                qty_presented=qty_presented,
                total_qty_checked=total_checked,
                total_qty_passed=total_passed,
            )

            # Fault lines
            times = request.POST.getlist('fault_time')
            bundles = request.POST.getlist('fault_bundle')
            codes = request.POST.getlist('fault_code')
            descs = request.POST.getlist('fault_description')
            operations = request.POST.getlist('fault_operation')
            operators = request.POST.getlist('fault_operator')
            qtys = request.POST.getlist('fault_qty')
            actions = request.POST.getlist('fault_action')

            for i in range(len(bundles)):
                if not bundles[i]:  # khali line skip
                    continue
                InitialQualityFault.objects.create(
                    report=report,
                    time=times[i] or '00:00',
                    bundle_lot_no=bundles[i],
                    fault_code_id=codes[i] if codes[i] else None,
                    fault_description=descs[i] if i < len(descs) else '',
                    operation_id=operations[i] if i < len(operations) and operations[i] else None,
                    operator_at_fault_id=operators[i] if i < len(operators) and operators[i] else None,
                    qty=int(qtys[i]) if qtys[i] else 0,
                    action=actions[i] if i < len(actions) else 'R',
                )

            # Summary calculate karo
            report.calculate_summary()

            messages.success(
                request,
                f"PPC-04 save ho gayi. Defect Rate: {report.defect_rate}%"
            )
            return redirect('initial_qc_detail', pk=report.pk)
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('initial_qc_create')

    # GET
    orders = Order.objects.exclude(status='COMPLETED').order_by('-created_at')
    teams = Team.objects.filter(is_active=True)
    operations = Operation.objects.filter(is_active=True).order_by('section', 'name')
    operators = Operator.objects.filter(is_active=True).order_by('full_name')
    fault_codes = FaultCode.objects.filter(is_active=True)

    context = {
        'orders': orders,
        'teams': teams,
        'operations': operations,
        'operators': operators,
        'fault_codes': fault_codes,
        'today': date.today().isoformat(),
    }
    return render(request, 'quality/initial_qc_form.html', context)


@login_required
@role_required('QC', 'ADMIN')
def initial_qc_detail(request, pk):
    """PPC-04 ki detail — PDF jaisa layout."""
    report = get_object_or_404(
        InitialQualityReport.objects.select_related('order', 'team', 'qc_inspector'),
        pk=pk
    )
    faults = report.fault_lines.select_related(
        'fault_code', 'operation', 'operator_at_fault'
    )
    context = {
        'report': report,
        'faults': faults,
    }
    return render(request, 'quality/initial_qc_detail.html', context)


@login_required
@role_required('QC', 'ADMIN')
def final_qc_list(request):
    """Saari PPC-05 reports."""
    reports = FinalQualityReport.objects.select_related(
        'order', 'team', 'qc_inspector'
    ).order_by('-date', '-created_at')
    return render(request, 'quality/final_qc_list.html', {'reports': reports})


@login_required
@role_required('QC', 'ADMIN')
def final_qc_create(request):
    """
    Nayi PPC-05 report banao.
    PPC-04 se boxes A, B, I auto-fill hote hain.
    """
    if request.method == 'POST':
        try:
            order_id = request.POST.get('order')
            team_id = request.POST.get('team') or None
            report_date = request.POST.get('date')
            insp_from = request.POST.get('inspection_from')
            insp_to = request.POST.get('inspection_to')
            qty_presented = int(request.POST.get('qty_presented') or 0)
            initial_report_id = request.POST.get('initial_report') or None

            # PPC-04 se boxes A, B, I copy karo
            qty_a = 0
            qty_b = 0
            rework_sent_dt = None

            if initial_report_id:
                try:
                    init_report = InitialQualityReport.objects.get(pk=initial_report_id)
                    qty_a = init_report.total_qty_checked
                    qty_b = init_report.total_qty_defective
                    rework_sent_dt = init_report.rework_sent_datetime
                except InitialQualityReport.DoesNotExist:
                    pass

            report = FinalQualityReport.objects.create(
                order_id=order_id,
                team_id=team_id,
                date=report_date,
                qc_inspector=request.user,
                inspection_from=insp_from,
                inspection_to=insp_to,
                qty_presented=qty_presented,
                initial_report_id=initial_report_id,
                qty_checked_at_initial=qty_a,
                qty_defective_at_initial=qty_b,
                qty_presented_at_final=qty_presented,
                rework_sent=rework_sent_dt,
            )

            # Fault lines
            times = request.POST.getlist('fault_time')
            bundles = request.POST.getlist('fault_bundle')
            codes = request.POST.getlist('fault_code')
            descs = request.POST.getlist('fault_description')
            operations = request.POST.getlist('fault_operation')
            operators = request.POST.getlist('fault_operator')
            qtys = request.POST.getlist('fault_qty')
            repeats = request.POST.getlist('fault_repeat')
            actions = request.POST.getlist('fault_action')

            for i in range(len(bundles)):
                if not bundles[i]:
                    continue
                FinalQualityFault.objects.create(
                    report=report,
                    time=times[i] or '00:00',
                    bundle_lot_no=bundles[i],
                    fault_code_id=codes[i] if codes[i] else None,
                    fault_description=descs[i] if i < len(descs) else '',
                    operation_id=operations[i] if i < len(operations) and operations[i] else None,
                    operator_at_fault_id=operators[i] if i < len(operators) and operators[i] else None,
                    qty=int(qtys[i]) if qtys[i] else 0,
                    repeat_fault=(repeats[i] == 'Y') if i < len(repeats) else False,
                    action=actions[i] if i < len(actions) else 'R',
                )

            report.calculate_summary()

            messages.success(
                request,
                f"PPC-05 save ho gayi. Final Defect Rate: {report.final_defect_rate}% | Rework Hours: {report.total_rework_hours}"
            )
            return redirect('final_qc_detail', pk=report.pk)
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('final_qc_create')

    # GET
    orders = Order.objects.exclude(status='COMPLETED').order_by('-created_at')
    teams = Team.objects.filter(is_active=True)
    operations = Operation.objects.filter(is_active=True).order_by('section', 'name')
    operators = Operator.objects.filter(is_active=True).order_by('full_name')
    fault_codes = FaultCode.objects.filter(is_active=True)
    initial_reports = InitialQualityReport.objects.select_related('order').order_by('-date')

    context = {
        'orders': orders,
        'teams': teams,
        'operations': operations,
        'operators': operators,
        'fault_codes': fault_codes,
        'initial_reports': initial_reports,
        'today': date.today().isoformat(),
    }
    return render(request, 'quality/final_qc_form.html', context)


@login_required
@role_required('QC', 'ADMIN')
def final_qc_detail(request, pk):
    """PPC-05 ki detail — PDF jaisa layout."""
    report = get_object_or_404(
        FinalQualityReport.objects.select_related('order', 'team', 'qc_inspector', 'initial_report'),
        pk=pk
    )
    faults = report.fault_lines.select_related(
        'fault_code', 'operation', 'operator_at_fault'
    )
    context = {
        'report': report,
        'faults': faults,
    }
    return render(request, 'quality/final_qc_detail.html', context)