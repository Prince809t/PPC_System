from django.db import models
from teams.models import Team, Operator
from django.conf import settings


class Order(models.Model):
    """
    Order master — factory ke saare orders.
    Order/Sample No. unique hoga (PDF ka rule: reports isi pe match karti hain).
    """

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    order_no = models.CharField(
        max_length=50,
        unique=True,
        help_text="Order / Sample No. — bilkul waisa hi likho jaisa order sheet pe hai"
    )
    style = models.CharField(max_length=100, blank=True)
    buyer = models.CharField(max_length=100, blank=True)
    order_qty = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING
    )
    order_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_no} — {self.style or 'No style'}"


class OperationAllocation(models.Model):
    """
    PPC-03 — Roz ka working plan.
    Har line: ek operator, ek order, ek operation, kitne ghante.
    Ek din me operator 2 order pe kaam kare to 2 lines.
    """

    class LineType(models.TextChoices):
        ONLINE = 'ONLINE', 'Online (Sewing)'
        OFFLINE = 'OFFLINE', 'Offline (Finishing)'

    # Plan ka header
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='allocations'
    )
    date = models.DateField(help_text="Kis din ka plan hai")
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'SUPERVISOR'},
        related_name='created_allocations'
    )
    shift_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=8.00
    )

    # Line item (ek operator ka ek kaam)
    operator = models.ForeignKey(
        Operator,
        on_delete=models.CASCADE,
        related_name='allocations'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='allocations'
    )
    style = models.CharField(
        max_length=100,
        blank=True,
        help_text="Order se auto-fill hoga ya manual"
    )
    operation = models.ForeignKey(
        'teams.Operation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='allocations'
    )
    line_type = models.CharField(
        max_length=10,
        choices=LineType.choices,
        default=LineType.ONLINE,
        help_text="ON / OFFLINE"
    )
    target_per_hour = models.PositiveIntegerField(
        default=0,
        help_text="Is kaam ka per hour target"
    )
    hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=8.00,
        help_text="Is kaam me kitne ghante lagenge"
    )
    planned_output = models.PositiveIntegerField(
        default=0,
        help_text="Auto-calculate: Target/hr × Hours"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'team', 'operator']
        # Ek din me ek operator ek order+operation pe ek hi line rakh sakta hai
        unique_together = [['date', 'operator', 'order', 'operation']]

    def save(self, *args, **kwargs):
        """
        Planned Output auto-calculate karo = Target/hr × Hours.
        PDF ka rule follow karte hue.
        String/None safe conversion ke saath.
        """
        try:
            target = int(self.target_per_hour or 0)
            hours = float(self.hours or 0)
            self.planned_output = int(target * hours)
        except (ValueError, TypeError):
            self.planned_output = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} — {self.operator.full_name} — {self.order.order_no}"