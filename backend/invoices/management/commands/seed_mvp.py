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
        demo_password = os.getenv("DEMO_USER_PASSWORD", "password")

        admin, created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                "email": admin_email,
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.email = admin_email
        admin.role = "admin"
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.set_password(admin_password)
        admin.save()
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created admin user {admin.username}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated admin user {admin.username}"))

        for department in Department.objects.all():
            DepartmentAccess.objects.update_or_create(
                user=admin,
                department=department,
                defaults={"role": "admin"},
            )

        created_demo_users = []
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
                user.email = f"{username}@example.com"
                user.role = role
                user.is_active = True
                user.set_password(demo_password)
                user.save()
                department = Department.objects.get(code=role)
                DepartmentAccess.objects.update_or_create(
                    user=user,
                    department=department,
                    defaults={"role": role},
                )
                created_demo_users.append((username, role, user_created))

        self.stdout.write(self.style.SUCCESS("Seed completed"))
        self.stdout.write("Credentials:")
        self.stdout.write(f"  admin -> login: {admin_username} | password: {admin_password}")
        if options["with_demo_users"]:
            for username, role, user_created in created_demo_users:
                action = "created" if user_created else "updated"
                self.stdout.write(
                    f"  {username} ({role}, {action}) -> login: {username} | password: {demo_password}"
                )
