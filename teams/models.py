from django.db import models
from django.conf import settings


class Operation(models.Model):
    """
    Operation master — garment banane ke saare operations.
    Jaise: Shoulder Join, Sleeve Attach, Hem, Button Attach, etc.
    """

    class Section(models.TextChoices):
        ONLINE = 'ONLINE', 'Online (Sewing Line)'
        OFFLINE = 'OFFLINE', 'Offline (Finishing)'

    name = models.CharField(max_length=100, unique=True)
    section = models.CharField(
        max_length=10,
        choices=Section.choices,
        default=Section.ONLINE,
        help_text="Online = silai line, Offline = finishing"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['section', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_section_display()})"


class Machine(models.Model):
    """
    Machine / Workstation master.
    Har machine ka ek unique number hoga.
    """

    class MachineType(models.TextChoices):
        SEWING = 'SEWING', 'Sewing Machine'
        OVERLOCK = 'OVERLOCK', 'Overlock Machine'
        FLATLOCK = 'FLATLOCK', 'Flatlock Machine'
        BUTTON = 'BUTTON', 'Button Attach Machine'
        IRON = 'IRON', 'Iron / Press'
        CHECKING = 'CHECKING', 'Checking Table'
        PACKING = 'PACKING', 'Packing Table'
        TRIMMING = 'TRIMMING', 'Trimming Station'
        OTHER = 'OTHER', 'Other'

    machine_no = models.CharField(max_length=20, unique=True)
    machine_type = models.CharField(
        max_length=20,
        choices=MachineType.choices,
        default=MachineType.SEWING
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['machine_no']

    def __str__(self):
        return f"{self.machine_no} - {self.get_machine_type_display()}"


class Team(models.Model):
    """
    Team master — 5-6 teams ho sakti hain.
    Har team ka ek supervisor hoga.
    """

    name = models.CharField(max_length=50, unique=True)
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'SUPERVISOR'},
        related_name='supervised_teams',
        help_text="Supervisor user (accounts app se)"
    )
    shift_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=8.00,
        help_text="Shift ke ghante (jaise 8.00, 9.00)"
    )
    effective_from = models.DateField(
        help_text="Team kab se effective hai"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Operator(models.Model):
    """
    Operator master — har worker ki info.
    Team se link + User account se link (login ke liye).
    """

    class OperatorType(models.TextChoices):
        ONLINE = 'ONLINE', 'Online (Sewing)'
        OFFLINE = 'OFFLINE', 'Offline (Finishing)'

    # User account link (login ke liye) - optional
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'OPERATOR'},
        related_name='operator_profile',
        help_text="Operator ka login account (agar hai)"
    )

    # Basic info
    full_name = models.CharField(max_length=100)
    employee_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Factory ka employee code"
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operators',
        help_text="Kaunsi team me hai"
    )

    operator_type = models.CharField(
        max_length=10,
        choices=OperatorType.choices,
        default=OperatorType.ONLINE,
        help_text="Online = silai line, Offline = finishing"
    )

    # Standing assignment (PPC-02 ke liye)
    default_operation = models.ForeignKey(
        Operation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operators',
        help_text="Default operation jo karta hai"
    )
    default_machine = models.ForeignKey(
        Machine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operators',
        help_text="Default machine/workstation"
    )
    target_per_hour = models.PositiveIntegerField(
        default=0,
        help_text="Per hour kitne pieces target hain"
    )
    planned_per_day = models.PositiveIntegerField(
        default=0,
        help_text="Auto-calculate: Target/hr × Shift Hours (save pe bharega)"
    )

    # Status
    is_active = models.BooleanField(default=True)
    joined_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['team', 'full_name']

    def save(self, *args, **kwargs):
        """
        Planned/Day auto-calculate karo = Target/hr × Shift Hours.
        PPC-02 PDF ka rule: Planned/Day = Target per Hour × Shift Hours
        String/None safe conversion ke saath.
        """
        try:
            if self.team and self.target_per_hour:
                target = int(self.target_per_hour or 0)
                shift = float(self.team.shift_hours or 0)
                self.planned_per_day = int(target * shift)
            else:
                self.planned_per_day = 0
        except (ValueError, TypeError):
            self.planned_per_day = 0
        super().save(*args, **kwargs)

    def __str__(self):
        team_name = self.team.name if self.team else "No Team"
        return f"{self.full_name} ({self.employee_code}) — {team_name}"