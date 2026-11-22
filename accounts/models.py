from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User Model — Django ke default user ko extend karta hai.
    Har user ka ek role hoga: OPERATOR, SUPERVISOR, QC, ADMIN.
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        SUPERVISOR = 'SUPERVISOR', 'Supervisor'
        QC = 'QC', 'QC Inspector'
        OPERATOR = 'OPERATOR', 'Operator'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.OPERATOR,
        help_text="User ka role — kya kaam karega"
    )

    def __str__(self):
        return f"{self.username} ({self.role})"