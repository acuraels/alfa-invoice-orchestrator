import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from invoices.constants import COUNTERPARTIES, DEPARTMENTS
from invoices.models import Counterparty, Department, DepartmentAccess


class Command(BaseCommand):
    help = "Seed departments, counterparties, admin and role users"

    def add_arguments(self, parser):
        parser.add_argument("--with-demo-users", action="store_true", help="Create demo role users")

    def handle(self, *args, **options):
        User = get_user_model()

        for dep in DEPARTMENTS:
            Department.objects.update_or_create(
                id=dep["id"],
                defaults={
                    "code": dep["code"],
                    "name": dep["name"],
                    "mnemonic": dep["mnemonic"],
                    "is_active": True,
                },
            )

        for cp in COUNTERPARTIES:
            Counterparty.objects.update_or_create(
                id=cp["id"],
                defaults={
                    "name": cp["name"],
                    "inn": cp["inn"],
                    "kpp": cp["kpp"],
                    "is_active": True,
                },
            )

        admin_username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
        admin_email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
        admin_password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")

        admin, created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                "email": admin_email,
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password(admin_password)
            admin.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS(f"Created admin user {admin.username}"))

        for department in Department.objects.all():
            DepartmentAccess.objects.update_or_create(
                user=admin,
                department=department,
                defaults={"role": "admin"},
            )

        if options["with_demo_users"]:
            demo_users = [
                ("factoring_user", "factoring"),
                ("accounting_user", "accounting"),
                ("taxation_user", "taxation"),
                ("acquiring_user", "acquiring"),
            ]
            for username, role in demo_users:
                user, user_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": f"{username}@example.com",
                        "role": role,
                        "is_active": True,
                    },
                )
                if user_created:
                    user.set_password("password")
                    user.save(update_fields=["password"])
                department = Department.objects.get(code=role)
                DepartmentAccess.objects.update_or_create(
                    user=user,
                    department=department,
                    defaults={"role": role},
                )

        self.stdout.write(self.style.SUCCESS("Seed completed"))
