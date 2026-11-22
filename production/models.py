from django.db import models
from teams.models import Team, Operator, Operation
from planning.models import Order
from django.conf import settings


class OutputLog(models.Model):
    """
    Operator Daily Output Sheet — har line ek kaam ka record.
    Jab bhi operator naya order ya operation shuru kare, nayi line bane.
    """

    # Header info
    operator = models.ForeignKey(
        Operator,
        on_delete=models.CASCADE,
        related_name='output_logs'
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='output_logs',
        help_text="Team auto-fill hoga operator se"
    )
    date = models.DateField(help_text="Kis din ka output hai")

    # Kaam ki detail
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='output_logs'
    )
    operation = models.ForeignKey(
        Operation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='output_logs'
    )

    # Time tracking
    start_time = models.TimeField(help_text="Kaam shuru karne ka time")
    end_time = models.TimeField(help_text="Kaam khatam karne ka time")

    # Output
    pieces_completed = models.PositiveIntegerField(
        default=0,
        help_text="Is period me kitne pieces bane"
    )

    # QC
    qc_checked = models.BooleanField(
        default=False,
        help_text="QC ne pieces check kar liye?"
    )
    qc_checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'QC'},
        related_name='qc_checked_outputs',
        help_text="Kis QC ne check kiya"
    )
    qc_checked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="QC ne kab check kiya"
    )

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'operator', 'start_time']
        verbose_name = 'Output Log'
        verbose_name_plural = 'Output Logs'

    def __str__(self):
        return f"{self.date} — {self.operator.full_name} — {self.pieces_completed} pcs"

    @property
    def total_hours(self):
        """Start se end tak kitne ghante lage (rough)."""
        if self.start_time and self.end_time:
            from datetime import datetime, date
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)
            diff = (end - start).total_seconds() / 3600
            return round(diff, 2)
        return 0

    @property
    def duration_hours(self):
        return self.total_hours

    def save(self, *args, **kwargs):
        """
        Team auto-fill karo operator se (agar nahi diya).
        """
        if not self.team and self.operator and self.operator.team:
            self.team = self.operator.team
        super().save(*args, **kwargs)


class DowntimeLog(models.Model):
    """
    Break / Downtime Log — jab bhi kaam ruke.
    Lunch, chai, machine problem, kaam ka wait — sab yahan.
    """

    class Reason(models.TextChoices):
        LUNCH = 'LUNCH', 'Lunch Break'
        TEA = 'TEA', 'Tea Break'
        MACHINE = 'MACHINE', 'Machine Problem'
        WAITING = 'WAITING', 'Waiting for Work'
        POWER = 'POWER', 'Power Outage'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'
        OTHER = 'OTHER', 'Other'

    operator = models.ForeignKey(
        Operator,
        on_delete=models.CASCADE,
        related_name='downtime_logs'
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='downtime_logs'
    )
    date = models.DateField()

    reason = models.CharField(
        max_length=15,
        choices=Reason.choices,
        default=Reason.OTHER
    )
    start_time = models.TimeField()
    end_time = models.TimeField()

    notes = models.TextField(
        blank=True,
        help_text="Agar 'Other' hai to detail likho"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'start_time']

    def __str__(self):
        return f"{self.date} — {self.operator.full_name} — {self.get_reason_display()}"

    @property
    def total_hours(self):
        """Start se end tak kitne ghante lage. String/Time dono handle karta hai."""
        if not self.start_time or not self.end_time:
            return 0
        try:
            from datetime import datetime, date

            start = self.start_time
            end = self.end_time

            if isinstance(start, str):
                start = datetime.strptime(start, "%H:%M").time()
            if isinstance(end, str):
                end = datetime.strptime(end, "%H:%M").time()

            start_dt = datetime.combine(date.today(), start)
            end_dt = datetime.combine(date.today(), end)
            diff = (end_dt - start_dt).total_seconds() / 3600
            return round(diff, 2)
        except (ValueError, TypeError):
            return 0

    def save(self, *args, **kwargs):
        if not self.team and self.operator and self.operator.team:
            self.team = self.operator.team
        super().save(*args, **kwargs)