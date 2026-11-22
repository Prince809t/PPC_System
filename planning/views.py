from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date
from .models import Order, OperationAllocation
from teams.models import Team, Operator
from accounts.decorators import role_required


@login_required
@role_required('ADMIN', 'SUPERVISOR')
def allocation_list(request):
    """
    Saare allocation plans ki list — date ke hisaab se filter.
    """
    selected_date = request.GET.get('date', date.today().isoformat())
    allocations = OperationAllocation.objects.filter(
        date=selected_date
    ).select_related('team', 'operator', 'order', 'operation').order_by('team', 'operator')

    context = {
        'allocations': allocations,
        'selected_date': selected_date,
    }
    return render(request, 'planning/allocation_list.html', context)


@login_required
@role_required('ADMIN', 'SUPERVISOR')
def allocation_create(request):
    """
    Nayi allocation line banao (PPC-03).
    """
    if request.method == 'POST':
        team_id = request.POST.get('team')
        operator_id = request.POST.get('operator')
        order_id = request.POST.get('order')
        operation_id = request.POST.get('operation')
        line_type = request.POST.get('line_type')
        target = request.POST.get('target_per_hour')
        hours = request.POST.get('hours')
        alloc_date = request.POST.get('date')

        try:
            # Duplicate check — same date, operator, order, operation
            from .models import OperationAllocation
            existing = OperationAllocation.objects.filter(
                date=alloc_date,
                operator_id=operator_id,
                order_id=order_id,
                operation_id=operation_id if operation_id else None,
            ).exists()

            if existing:
                messages.warning(
                    request,
                    "Yeh allocation pehle se exist karti hai (same date, operator, order, operation)."
                )
                return redirect(f"/planning/allocation/?date={alloc_date}")

            allocation = OperationAllocation.objects.create(
                team_id=team_id,
                operator_id=operator_id,
                order_id=order_id,
                operation_id=operation_id if operation_id else None,
                line_type=line_type,
                target_per_hour=target or 0,
                hours=hours or 0,
                date=alloc_date,
                supervisor=request.user,
            )
            messages.success(
                request,
                f"Allocation save ho gayi — Planned Output: {allocation.planned_output} pieces"
            )
            return redirect(f"/planning/allocation/?date={alloc_date}")
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('allocation_create')

    # GET — form dikhao
    teams = Team.objects.filter(is_active=True).order_by('name')
    operators = Operator.objects.filter(is_active=True).select_related('team').order_by('team', 'full_name')
    orders = Order.objects.exclude(status='COMPLETED').order_by('-created_at')

    # Operations aur unka section
    from teams.models import Operation
    operations = Operation.objects.filter(is_active=True).order_by('section', 'name')

    context = {
        'teams': teams,
        'operators': operators,
        'orders': orders,
        'operations': operations,
        'today': date.today().isoformat(),
    }
    return render(request, 'planning/allocation_form.html', context)


@login_required
@role_required('ADMIN', 'SUPERVISOR')
def allocation_delete(request, pk):
    """
    Allocation delete karo.
    """
    allocation = get_object_or_404(OperationAllocation, pk=pk)
    alloc_date = allocation.date
    if request.method == 'POST':
        allocation.delete()
        messages.success(request, "Allocation delete ho gayi.")
    return redirect(f"/planning/allocation/?date={alloc_date}")


@login_required
@role_required('ADMIN', 'SUPERVISOR')
def order_list(request):
    """
    Saare orders ki list.
    """
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'planning/order_list.html', {'orders': orders})


@login_required
@role_required('ADMIN', 'SUPERVISOR')
def order_create(request):
    """
    Naya order banao.
    """
    if request.method == 'POST':
        order_no = request.POST.get('order_no')
        style = request.POST.get('style', '')
        buyer = request.POST.get('buyer', '')
        order_qty = request.POST.get('order_qty', 0)
        status = request.POST.get('status', 'PENDING')
        order_date = request.POST.get('order_date') or None

        try:
            Order.objects.create(
                order_no=order_no,
                style=style,
                buyer=buyer,
                order_qty=order_qty,
                status=status,
                order_date=order_date,
            )
            messages.success(request, f"Order {order_no} save ho gaya.")
            return redirect('order_list')
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('order_create')

    return render(request, 'planning/order_form.html')