from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models

ADMIN_ROLE = "admin"
USER_ROLE = "user"


class UserManager(DjangoUserManager):
    def _create_user(self, username, email, password, **extra_fields):
        if not extra_fields.get("role"):
            raise ValueError("The role field must be provided.")
        return super()._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", ADMIN_ROLE)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "admin", "Admin"
        USER = "user", "User"

    role = models.CharField(max_length=32, choices=Roles.choices)
    full_name = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    departments = models.ManyToManyField(
        "invoices.Department",
        through="invoices.DepartmentAccess",
        related_name="users",
        blank=True,
    )

    objects = UserManager()

    REQUIRED_FIELDS = ["email", "role"]

    def __str__(self) -> str:
        return self.username
