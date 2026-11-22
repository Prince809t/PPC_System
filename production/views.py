# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from django.utils import timezone
# from datetime import date
# from .models import OutputLog, DowntimeLog
# from teams.models import Operator
# from planning.models import Order
# from teams.models import Operation
# from accounts.decorators import role_required


# def get_operator_for_user(user):
#     """
#     Login user se operator profile nikalo.
#     Agar user ke paas operator_profile hai to woh return karo.
#     """
#     if hasattr(user, 'operator_profile'):
#         return user.operator_profile
#     return None


# @login_required
# def my_output_list(request):
#     """
#     Operator apna output list dekhe.
#     Admin/Supervisor sab ka dekh sakte hain.
#     """
#     today = date.today()

#     if request.user.role == 'OPERATOR':
#         operator = get_operator_for_user(request.user)
#         if not operator:
#             messages.error(request, "Tumhara operator profile nahi mila. Admin se contact karo.")
#             return redirect('dashboard')
#         logs = OutputLog.objects.filter(operator=operator).order_by('-date', '-start_time')[:50]
#     else:
#         # Admin/Supervisor — sab ka data
#         logs = OutputLog.objects.all().order_by('-date', '-start_time')[:100]

#     return render(request, 'production/my_output_list.html', {'logs': logs})


# @login_required
# @role_required('OPERATOR', 'ADMIN', 'SUPERVISOR')
# def output_create(request):
#     """
#     Nayi output line banao.
#     Operator apna bhare, Admin/Supervisor kisi ka bhi bhar sake.
#     """
#     # Operator determine karo
#     if request.user.role == 'OPERATOR':
#         operator = get_operator_for_user(request.user)
#         if not operator:
#             messages.error(request, "Tumhara operator profile nahi mila.")
#             return redirect('dashboard')
#         operators = [operator]  # sirf khud
#     else:
#         operators = Operator.objects.filter(is_active=True).select_related('team')
#         operator = None

#     if request.method == 'POST':
#         try:
#             operator_id = request.POST.get('operator') or (operator.id if operator else None)
#             if not operator_id:
#                 raise ValueError("Operator select karo")

#             op_obj = Operator.objects.get(pk=operator_id)
#             order_id = request.POST.get('order')
#             operation_id = request.POST.get('operation') or None
#             log_date = request.POST.get('date')
#             start_time = request.POST.get('start_time')
#             end_time = request.POST.get('end_time')
#             pieces = request.POST.get('pieces_completed') or 0

#             # ===== VALIDATION =====
#             if not order_id:
#                 raise ValueError("Order select karo")

#             if not start_time or not end_time:
#                 raise ValueError("Start time aur End time dono zaroori hain")

#             # Time comparison — start < end hona chahiye
#             from datetime import datetime
#             start_dt = datetime.strptime(start_time, "%H:%M")
#             end_dt = datetime.strptime(end_time, "%H:%M")
#             if end_dt <= start_dt:
#                 raise ValueError("End time, Start time se bada hona chahiye")

#             pieces = int(pieces)
#             if pieces < 0:
#                 raise ValueError("Pieces negative nahi ho sakte")

#             # ===== SAVE =====
#             log = OutputLog.objects.create(
#                 operator=op_obj,
#                 team=op_obj.team,
#                 order_id=order_id,
#                 operation_id=operation_id,
#                 date=log_date,
#                 start_time=start_time,
#                 end_time=end_time,
#                 pieces_completed=pieces,
#             )

#             messages.success(
#                 request,
#                 f"Output save ho gaya — {log.pieces_completed} pieces"
#             )
#             return redirect('my_output_list')
#         except ValueError as e:
#             messages.error(request, f"Validation Error: {e}")
#             return redirect('output_create')
#         except Exception as e:
#             messages.error(request, f"Error: {e}")
#             return redirect('output_create')

#     # GET
#     orders = Order.objects.exclude(status='COMPLETED').order_by('-created_at')
#     operations = Operation.objects.filter(is_active=True).order_by('section', 'name')

#     context = {
#         'operators': operators,
#         'orders': orders,
#         'operations': operations,
#         'today': date.today().isoformat(),
#         'is_operator': request.user.role == 'OPERATOR',
#     }
#     return render(request, 'production/output_form.html', context)


# @login_required
# def downtime_list(request):
#     """
#     Operator apne downtime dekh sake.
#     Admin/Supervisor sab ka.
#     """
#     if request.user.role == 'OPERATOR':
#         operator = get_operator_for_user(request.user)
#         if not operator:
#             messages.error(request, "Tumhara operator profile nahi mila.")
#             return redirect('dashboard')
#         logs = DowntimeLog.objects.filter(operator=operator).order_by('-date', '-start_time')[:50]
#     else:
#         logs = DowntimeLog.objects.all().order_by('-date', '-start_time')[:100]

#     return render(request, 'production/downtime_list.html', {'logs': logs})


# @login_required
# @role_required('OPERATOR', 'ADMIN', 'SUPERVISOR')
# def downtime_create(request):
#     """
#     Nayi downtime entry banao.
#     """
#     if request.user.role == 'OPERATOR':
#         operator = get_operator_for_user(request.user)
#         if not operator:
#             messages.error(request, "Tumhara operator profile nahi mila.")
#             return redirect('dashboard')
#         operators = [operator]
#     else:
#         operators = Operator.objects.filter(is_active=True).select_related('team')

#     if request.method == 'POST':
#         try:
#             operator_id = request.POST.get('operator')
#             if not operator_id:
#                 raise ValueError("Operator select karo")

#             op_obj = Operator.objects.get(pk=operator_id)
#             reason = request.POST.get('reason')
#             log_date = request.POST.get('date')
#             start_time = request.POST.get('start_time')
#             end_time = request.POST.get('end_time')
#             notes = request.POST.get('notes', '')

#             log = DowntimeLog.objects.create(
#                 operator=op_obj,
#                 team=op_obj.team,
#                 reason=reason,
#                 date=log_date,
#                 start_time=start_time,
#                 end_time=end_time,
#                 notes=notes,
#             )

#             messages.success(
#                 request,
#                 f"Downtime save ho gaya — {log.duration_hours} ghante"
#             )
#             return redirect('downtime_list')
#         except Exception as e:
#             messages.error(request, f"Error: {e}")
#             return redirect('downtime_create')

#     context = {
#         'operators': operators,
#         'today': date.today().isoformat(),
#         'is_operator': request.user.role == 'OPERATOR',
#         'reasons': DowntimeLog.Reason.choices,
#     }
#     return render(request, 'production/downtime_form.html', context)


# @login_required
# @role_required('QC', 'ADMIN')
# def qc_pending_list(request):
#     """
#     QC ke liye — jo output abhi tak check nahi hue.
#     """
#     pending = OutputLog.objects.filter(qc_checked=False).select_related(
#         'operator', 'order', 'operation'
#     ).order_by('-date', 'operator')
#     return render(request, 'production/qc_pending_list.html', {'pending': pending})


# @login_required
# @role_required('QC', 'ADMIN')
# def qc_mark_checked(request, pk):
#     """
#     QC mark kare ki pieces check ho gaye.
#     """
#     log = get_object_or_404(OutputLog, pk=pk)
#     if request.method == 'POST':
#         log.qc_checked = True
#         log.qc_checked_by = request.user
#         log.qc_checked_at = timezone.now()
#         log.save()
#         messages.success(request, f"{log.pieces_completed} pieces QC checked mark ho gaye.")
#     return redirect('qc_pending_list')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date
from .models import OutputLog, DowntimeLog
from teams.models import Operator
from planning.models import Order
from teams.models import Operation
from accounts.decorators import role_required


def get_operator_for_user(user):
    """
    Login user se operator profile nikalo.
    Agar user ke paas operator_profile hai to woh return karo.
    """
    if hasattr(user, 'operator_profile'):
        return user.operator_profile
    return None


@login_required
def my_output_list(request):
    """
    Operator apna output list dekhe.
    Admin/Supervisor sab ka dekh sakte hain.
    """
    today = date.today()

    if request.user.role == 'OPERATOR':
        operator = get_operator_for_user(request.user)
        if not operator:
            messages.error(request, "Tumhara operator profile nahi mila. Admin se contact karo.")
            return redirect('dashboard')
        logs = OutputLog.objects.filter(operator=operator).order_by('-date', '-start_time')[:50]
    else:
        # Admin/Supervisor — sab ka data
        logs = OutputLog.objects.all().order_by('-date', '-start_time')[:100]

    return render(request, 'production/my_output_list.html', {'logs': logs})


@login_required
@role_required('OPERATOR', 'ADMIN', 'SUPERVISOR')
def output_create(request):
    """
    Nayi output line banao.
    Operator apna bhare, Admin/Supervisor kisi ka bhi bhar sake.
    """
    # Operator determine karo
    if request.user.role == 'OPERATOR':
        operator = get_operator_for_user(request.user)
        if not operator:
            messages.error(request, "Tumhara operator profile nahi mila.")
            return redirect('dashboard')
        operators = [operator]  # sirf khud
    else:
        operators = Operator.objects.filter(is_active=True).select_related('team')
        operator = None

    if request.method == 'POST':
        try:
            operator_id = request.POST.get('operator') or (operator.id if operator else None)
            if not operator_id:
                raise ValueError("Operator select karo")

            op_obj = Operator.objects.get(pk=operator_id)
            order_id = request.POST.get('order')
            operation_id = request.POST.get('operation') or None
            log_date = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            pieces = request.POST.get('pieces_completed') or 0

            # ===== VALIDATION =====
            if not order_id:
                raise ValueError("Order select karo")

            if not start_time or not end_time:
                raise ValueError("Start time aur End time dono zaroori hain")

            # Time comparison — start < end hona chahiye
            from datetime import datetime
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")
            if end_dt <= start_dt:
                raise ValueError("End time, Start time se bada hona chahiye")

            pieces = int(pieces)
            if pieces < 0:
                raise ValueError("Pieces negative nahi ho sakte")

            # ===== SAVE =====
            log = OutputLog.objects.create(
                operator=op_obj,
                team=op_obj.team,
                order_id=order_id,
                operation_id=operation_id,
                date=log_date,
                start_time=start_time,
                end_time=end_time,
                pieces_completed=pieces,
            )

            messages.success(
                request,
                f"Output save ho gaya — {log.pieces_completed} pieces"
            )
            return redirect('my_output_list')
        except ValueError as e:
            messages.error(request, f"Validation Error: {e}")
            return redirect('output_create')
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('output_create')

    # GET
    orders = Order.objects.exclude(status='COMPLETED').order_by('-created_at')
    operations = Operation.objects.filter(is_active=True).order_by('section', 'name')

    context = {
        'operators': operators,
        'orders': orders,
        'operations': operations,
        'today': date.today().isoformat(),
        'is_operator': request.user.role == 'OPERATOR',
    }
    return render(request, 'production/output_form.html', context)


@login_required
def downtime_list(request):
    """
    Operator apne downtime dekh sake.
    Admin/Supervisor sab ka.
    """
    if request.user.role == 'OPERATOR':
        operator = get_operator_for_user(request.user)
        if not operator:
            messages.error(request, "Tumhara operator profile nahi mila.")
            return redirect('dashboard')
        logs = DowntimeLog.objects.filter(operator=operator).order_by('-date', '-start_time')[:50]
    else:
        logs = DowntimeLog.objects.all().order_by('-date', '-start_time')[:100]

    return render(request, 'production/downtime_list.html', {'logs': logs})


@login_required
@role_required('OPERATOR', 'ADMIN', 'SUPERVISOR')
def downtime_create(request):
    """
    Nayi downtime entry banao.
    """
    if request.user.role == 'OPERATOR':
        operator = get_operator_for_user(request.user)
        if not operator:
            messages.error(request, "Tumhara operator profile nahi mila.")
            return redirect('dashboard')
        operators = [operator]
    else:
        operators = Operator.objects.filter(is_active=True).select_related('team')

    if request.method == 'POST':
        try:
            operator_id = request.POST.get('operator')
            if not operator_id:
                raise ValueError("Operator select karo")

            op_obj = Operator.objects.get(pk=operator_id)
            reason = request.POST.get('reason')
            log_date = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            notes = request.POST.get('notes', '')

            # ===== VALIDATION =====
            if not start_time or not end_time:
                raise ValueError("Start time aur End time dono zaroori hain")

            from datetime import datetime
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")
            if end_dt <= start_dt:
                raise ValueError("End time, Start time se bada hona chahiye")

            log = DowntimeLog.objects.create(
                operator=op_obj,
                team=op_obj.team,
                reason=reason,
                date=log_date,
                start_time=start_time,
                end_time=end_time,
                notes=notes,
            )

            messages.success(
                request,
                f"Downtime save ho gaya — {log.duration_hours} ghante"
            )
            return redirect('downtime_list')
        except ValueError as e:
            messages.error(request, f"Validation Error: {e}")
            return redirect('downtime_create')
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('downtime_create')

    context = {
        'operators': operators,
        'today': date.today().isoformat(),
        'is_operator': request.user.role == 'OPERATOR',
        'reasons': DowntimeLog.Reason.choices,
    }
    return render(request, 'production/downtime_form.html', context)


@login_required
@role_required('QC', 'ADMIN')
def qc_pending_list(request):
    """
    QC ke liye — jo output abhi tak check nahi hue.
    """
    pending = OutputLog.objects.filter(qc_checked=False).select_related(
        'operator', 'order', 'operation'
    ).order_by('-date', 'operator')
    return render(request, 'production/qc_pending_list.html', {'pending': pending})


@login_required
@role_required('QC', 'ADMIN')
def qc_mark_checked(request, pk):
    """
    QC mark kare ki pieces check ho gaye.
    """
    log = get_object_or_404(OutputLog, pk=pk)
    if request.method == 'POST':
        log.qc_checked = True
        log.qc_checked_by = request.user
        log.qc_checked_at = timezone.now()
        log.save()
        messages.success(request, f"{log.pieces_completed} pieces QC checked mark ho gaye.")
    return redirect('qc_pending_list')