from django.db import models
from django.conf import settings
from django.utils import timezone
from teams.models import Team, Operator, Operation
from planning.models import Order


class FaultCode(models.Model):
    """
    Fault Codes master — 01 se 16 tak (PDF fixed).
    """

    code = models.CharField(
        max_length=5,
        unique=True,
        help_text="01, 02, ... 16"
    )
    name = models.CharField(
        max_length=100,
        help_text="Broken stitch, Skip stitch, etc."
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.name}"


class InitialQualityReport(models.Model):
    """
    PPC-04 — Initial Offline Quality Report.
    Silai ke baad, finishing se pehle inspection.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='initial_qc_reports'
    )
    style = models.CharField(max_length=100, blank=True)
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initial_qc_reports'
    )
    date = models.DateField(help_text="Inspection ki date")
    qc_inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'QC'},
        related_name='initial_qc_reports'
    )

    inspection_from = models.TimeField(help_text="Inspection shuru kab hui")
    inspection_to = models.TimeField(help_text="Inspection khatam kab hui")

    qty_presented = models.PositiveIntegerField(
        default=0,
        help_text="Total kitne pieces inspection ke liye aaye"
    )

    # Summary boxes A-H
    total_qty_checked = models.PositiveIntegerField(
        default=0,
        help_text="Box A — Total pieces checked"
    )
    total_qty_passed = models.PositiveIntegerField(
        default=0,
        help_text="Box B — Passed pieces"
    )
    total_qty_defective = models.PositiveIntegerField(
        default=0,
        help_text="Box C — Defective pieces (auto from fault log)"
    )
    defect_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Box D — Defect Rate % (C ÷ A)"
    )
    qty_sent_for_rework = models.PositiveIntegerField(
        default=0,
        help_text="Box E — Rework ke liye bheje"
    )
    qty_rejected = models.PositiveIntegerField(
        default=0,
        help_text="Box F — Reject hue"
    )
    rework_sent_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Box G — Rework kab bheja (date & time)"
    )
    most_frequent_fault_code = models.ForeignKey(
        FaultCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text="Box H — Sabse zyada aane wala fault code (auto)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        unique_together = [['order', 'date', 'team']]

    def __str__(self):
        return f"PPC-04 — {self.order.order_no} — {self.date}"

    def calculate_summary(self):
        """
        Summary boxes auto-calculate karo fault lines se.
        String/None safe conversion ke saath.
        """
        faults = self.fault_lines.all()

        try:
            self.total_qty_defective = sum(int(f.qty or 0) for f in faults)
            self.qty_sent_for_rework = sum(int(f.qty or 0) for f in faults if f.action == 'R')
            self.qty_rejected = sum(int(f.qty or 0) for f in faults if f.action == 'RJ')
        except (ValueError, TypeError):
            self.total_qty_defective = 0
            self.qty_sent_for_rework = 0
            self.qty_rejected = 0

        try:
            checked = int(self.total_qty_checked or 0)
            defective = int(self.total_qty_defective or 0)
            if checked > 0:
                self.defect_rate = round((defective / checked) * 100, 2)
            else:
                self.defect_rate = 0
        except (ValueError, TypeError, ZeroDivisionError):
            self.defect_rate = 0

        if faults.exists():
            from django.db.models import Sum
            top = faults.values('fault_code').annotate(
                total_qty=Sum('qty')
            ).order_by('-total_qty').first()
            if top and top['fault_code']:
                self.most_frequent_fault_code_id = top['fault_code']

        self.save()

    def save(self, *args, **kwargs):
        if not self.style and self.order:
            self.style = self.order.style
        super().save(*args, **kwargs)


class InitialQualityFault(models.Model):
    """
    PPC-04 — Fault Log ki har line.
    """

    class Action(models.TextChoices):
        REWORK = 'R', 'Rework'
        REJECT = 'RJ', 'Reject'

    report = models.ForeignKey(
        InitialQualityReport,
        on_delete=models.CASCADE,
        related_name='fault_lines'
    )

    time = models.TimeField(help_text="Fault kab mila")
    bundle_lot_no = models.CharField(max_length=50)
    fault_code = models.ForeignKey(
        FaultCode,
        on_delete=models.SET_NULL,
        null=True,
        related_name='initial_faults'
    )
    fault_description = models.CharField(max_length=200, blank=True)
    operation = models.ForeignKey(
        Operation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initial_faults'
    )
    operator_at_fault = models.ForeignKey(
        Operator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initial_faults',
        help_text="Kis operator ki galti thi"
    )
    qty = models.PositiveIntegerField(default=0)
    action = models.CharField(
        max_length=5,
        choices=Action.choices,
        default=Action.REWORK
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['time']

    def __str__(self):
        return f"{self.bundle_lot_no} — {self.fault_code} — Qty {self.qty}"


class FinalQualityReport(models.Model):
    """
    PPC-05 — Final Offline Quality Report.
    Packing stage pe jo faults bache.
    Rework & Recovery A-L.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='final_qc_reports'
    )
    style = models.CharField(max_length=100, blank=True)
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='final_qc_reports'
    )
    date = models.DateField(help_text="Inspection ki date")
    qc_inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'QC'},
        related_name='final_qc_reports'
    )

    inspection_from = models.TimeField()
    inspection_to = models.TimeField()
    qty_presented = models.PositiveIntegerField(
        default=0,
        help_text="Final pe kitne pieces aaye"
    )

    # Link to initial (PPC-04)
    initial_report = models.ForeignKey(
        InitialQualityReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='final_reports'
    )

    # A, B, C — PPC-04 se
    qty_checked_at_initial = models.PositiveIntegerField(
        default=0,
        help_text="Box A — PPC-04 box A se copy"
    )
    qty_defective_at_initial = models.PositiveIntegerField(
        default=0,
        help_text="Box B — PPC-04 box C se copy"
    )
    initial_defect_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Box C — Initial Defect Rate % (B ÷ A)"
    )

    # D, E, F
    qty_presented_at_final = models.PositiveIntegerField(
        default=0,
        help_text="Box D — Final pe aaye pieces"
    )
    qty_defective_at_final = models.PositiveIntegerField(
        default=0,
        help_text="Box E — Final pe defective"
    )
    final_defect_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Box F — Final Defect Rate % (E ÷ D)"
    )

    # G, H
    defects_cleared_by_rework = models.PositiveIntegerField(
        default=0,
        help_text="Box G — Defects Cleared by Rework (B − E)"
    )
    repeat_faults_failed_rework = models.PositiveIntegerField(
        default=0,
        help_text="Box H — Repeat Faults (failed rework)"
    )

    # I, J, K
    rework_sent = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Box I — Rework Sent Date & Time"
    )
    rework_complete = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Box J — Rework Complete Date & Time"
    )
    total_rework_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Box K — Total Rework Hours (J − I) — TRUE COST OF POOR QUALITY"
    )

    # L
    qty_passed_to_packing = models.PositiveIntegerField(
        default=0,
        help_text="Box L — Qty Passed to Packing (D − E)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        unique_together = [['order', 'date', 'team']]

    def __str__(self):
        return f"PPC-05 — {self.order.order_no} — {self.date}"

    def calculate_summary(self):
        """
        Rework & Recovery boxes auto-calculate karo.
        """
        faults = self.fault_lines.all()

        # Box E
        try:
            self.qty_defective_at_final = sum(int(f.qty or 0) for f in faults)
        except (ValueError, TypeError):
            self.qty_defective_at_final = 0

        # Box H — repeat faults (Y mark wale lines ka qty sum)
        try:
            repeat_lines = faults.filter(repeat_fault='Y')
            self.repeat_faults_failed_rework = sum(int(f.qty or 0) for f in repeat_lines)
        except (ValueError, TypeError):
            self.repeat_faults_failed_rework = 0

        # Box C — Initial Defect Rate % = B ÷ A
        try:
            a = int(self.qty_checked_at_initial or 0)
            b = int(self.qty_defective_at_initial or 0)
            self.initial_defect_rate = round((b / a) * 100, 2) if a > 0 else 0
        except (ValueError, TypeError, ZeroDivisionError):
            self.initial_defect_rate = 0

        # Box F — Final Defect Rate % = E ÷ D
        try:
            d = int(self.qty_presented_at_final or 0)
            e = int(self.qty_defective_at_final or 0)
            self.final_defect_rate = round((e / d) * 100, 2) if d > 0 else 0
        except (ValueError, TypeError, ZeroDivisionError):
            self.final_defect_rate = 0

        # Box G — Defects Cleared by Rework = B − E
        try:
            b = int(self.qty_defective_at_initial or 0)
            e = int(self.qty_defective_at_final or 0)
            self.defects_cleared_by_rework = max(b - e, 0)
        except (ValueError, TypeError):
            self.defects_cleared_by_rework = 0

        # Box K — Total Rework Hours = J − I
        try:
            if self.rework_sent and self.rework_complete:
                diff = (self.rework_complete - self.rework_sent).total_seconds() / 3600
                self.total_rework_hours = round(diff, 2)
            else:
                self.total_rework_hours = 0
        except (ValueError, TypeError):
            self.total_rework_hours = 0

        # Box L — Qty Passed to Packing = D − E
        try:
            d = int(self.qty_presented_at_final or 0)
            e = int(self.qty_defective_at_final or 0)
            self.qty_passed_to_packing = max(d - e, 0)
        except (ValueError, TypeError):
            self.qty_passed_to_packing = 0

        self.save()

    def save(self, *args, **kwargs):
        if not self.style and self.order:
            self.style = self.order.style
        super().save(*args, **kwargs)


class FinalQualityFault(models.Model):
    """
    PPC-05 — Fault Log ki har line (packing stage pe).
    Initial se ek extra column: REPEAT FAULT? Y/N
    """

    class Action(models.TextChoices):
        REWORK = 'R', 'Rework'
        REJECT = 'RJ', 'Reject'

    class RepeatFault(models.TextChoices):
        YES = 'Y', 'Yes — Repeat Fault'
        NO = 'N', 'No — New Fault'

    report = models.ForeignKey(
        FinalQualityReport,
        on_delete=models.CASCADE,
        related_name='fault_lines'
    )

    time = models.TimeField(help_text="Fault kab mila")
    bundle_lot_no = models.CharField(max_length=50)
    fault_code = models.ForeignKey(
        FaultCode,
        on_delete=models.SET_NULL,
        null=True,
        related_name='final_faults'
    )
    fault_description = models.CharField(max_length=200, blank=True)
    operation = models.ForeignKey(
        Operation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='final_faults'
    )
    operator_at_fault = models.ForeignKey(
        Operator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='final_faults'
    )
    qty = models.PositiveIntegerField(default=0)

    # YEH CHANGE HUA HAI — BooleanField se CharField
    repeat_fault = models.CharField(
        max_length=1,
        choices=RepeatFault.choices,
        default=RepeatFault.NO,
        help_text="PDF ka rule: Y jab wahi fault dobara aaye jo pehle rework ho chuka tha"
    )

    action = models.CharField(
        max_length=5,
        choices=Action.choices,
        default=Action.REWORK
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['time']

    def __str__(self):
        repeat = " [REPEAT]" if self.repeat_fault == 'Y' else ""
        return f"{self.bundle_lot_no} — {self.fault_code}{repeat} — Qty {self.qty}"





# from django.db import models
# from teams.models import Team, Operator, Operation
# from planning.models import Order
# from django.conf import settings


# class OutputLog(models.Model):
#     """
#     Operator Daily Output Sheet — har line ek kaam ka record.
#     """

#     operator = models.ForeignKey(
#         Operator,
#         on_delete=models.CASCADE,
#         related_name='output_logs'
#     )
#     team = models.ForeignKey(
#         Team,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='output_logs',
#         help_text="Team auto-fill hoga operator se"
#     )
#     date = models.DateField(help_text="Kis din ka output hai")

#     order = models.ForeignKey(
#         Order,
#         on_delete=models.CASCADE,
#         related_name='output_logs'
#     )
#     operation = models.ForeignKey(
#         Operation,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='output_logs'
#     )

#     start_time = models.TimeField(help_text="Kaam shuru karne ka time")
#     end_time = models.TimeField(help_text="Kaam khatam karne ka time")

#     pieces_completed = models.PositiveIntegerField(
#         default=0,
#         help_text="Is period me kitne pieces bane"
#     )

#     qc_checked = models.BooleanField(
#         default=False,
#         help_text="QC ne pieces check kar liye?"
#     )
#     qc_checked_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         limit_choices_to={'role': 'QC'},
#         related_name='qc_checked_outputs'
#     )
#     qc_checked_at = models.DateTimeField(
#         null=True,
#         blank=True
#     )

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['-date', 'operator', 'start_time']
#         verbose_name = 'Output Log'
#         verbose_name_plural = 'Output Logs'

#     def __str__(self):
#         return f"{self.date} — {self.operator.full_name} — {self.pieces_completed} pcs"

#     @property
#     def total_hours(self):
#         """Start se end tak kitne ghante lage."""
#         if not self.start_time or not self.end_time:
#             return 0
#         try:
#             from datetime import datetime, date
#             start = self.start_time
#             end = self.end_time
#             if isinstance(start, str):
#                 start = datetime.strptime(start, "%H:%M").time()
#             if isinstance(end, str):
#                 end = datetime.strptime(end, "%H:%M").time()
#             start_dt = datetime.combine(date.today(), start)
#             end_dt = datetime.combine(date.today(), end)
#             diff = (end_dt - start_dt).total_seconds() / 3600
#             return round(diff, 2)
#         except (ValueError, TypeError):
#             return 0

#     def save(self, *args, **kwargs):
#         if not self.team and self.operator and self.operator.team:
#             self.team = self.operator.team
#         super().save(*args, **kwargs)


# class DowntimeLog(models.Model):
#     """
#     Break / Downtime Log.
#     """

#     class Reason(models.TextChoices):
#         LUNCH = 'LUNCH', 'Lunch Break'
#         TEA = 'TEA', 'Tea Break'
#         MACHINE = 'MACHINE', 'Machine Problem'
#         WAITING = 'WAITING', 'Waiting for Work'
#         POWER = 'POWER', 'Power Outage'
#         MAINTENANCE = 'MAINTENANCE', 'Maintenance'
#         OTHER = 'OTHER', 'Other'

#     operator = models.ForeignKey(
#         Operator,
#         on_delete=models.CASCADE,
#         related_name='downtime_logs'
#     )
#     team = models.ForeignKey(
#         Team,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='downtime_logs'
#     )
#     date = models.DateField()

#     reason = models.CharField(
#         max_length=15,
#         choices=Reason.choices,
#         default=Reason.OTHER
#     )
#     start_time = models.TimeField()
#     end_time = models.TimeField()

#     notes = models.TextField(
#         blank=True,
#         help_text="Agar 'Other' hai to detail likho"
#     )

#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['-date', 'start_time']

#     def __str__(self):
#         return f"{self.date} — {self.operator.full_name} — {self.get_reason_display()}"

#     @property
#     def total_hours(self):
#         """Start se end tak kitne ghante lage."""
#         if not self.start_time or not self.end_time:
#             return 0
#         try:
#             from datetime import datetime, date
#             start = self.start_time
#             end = self.end_time
#             if isinstance(start, str):
#                 start = datetime.strptime(start, "%H:%M").time()
#             if isinstance(end, str):
#                 end = datetime.strptime(end, "%H:%M").time()
#             start_dt = datetime.combine(date.today(), start)
#             end_dt = datetime.combine(date.today(), end)
#             diff = (end_dt - start_dt).total_seconds() / 3600
#             return round(diff, 2)
#         except (ValueError, TypeError):
#             return 0

#     @property
#     def duration_hours(self):
#         """
#         Downtime duration — reports/utils.py isi ko use karta hai.
#         Same as total_hours (alias).
#         """
#         return self.total_hours

#     def save(self, *args, **kwargs):
#         if not self.team and self.operator and self.operator.team:
#             self.team = self.operator.team
#         super().save(*args, **kwargs)