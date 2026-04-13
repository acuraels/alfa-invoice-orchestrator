from collections.abc import Mapping

ROLE_DEPARTMENT_MAP: Mapping[str, str] = {
    "factoring": "factoring",
    "accounting": "accounting",
    "taxation": "taxation",
    "acquiring": "acquiring",
}


def get_department_for_role(role: str | None) -> str | None:
    if role is None:
        return None
    return ROLE_DEPARTMENT_MAP.get(role)


def filter_queryset_by_role(queryset, user, department_field: str = "department"):
    if not getattr(user, "is_authenticated", False):
        return queryset.none()

    if getattr(user, "is_superuser", False) or getattr(user, "role", None) == "admin":
        return queryset

    department = get_department_for_role(getattr(user, "role", None))
    if department is None:
        return queryset.none()

    return queryset.filter(**{department_field: department})


class RoleScopedQuerysetMixin:
    role_scope_department_field = "department"

    def get_role_scope_department_field(self) -> str:
        return self.role_scope_department_field

    def apply_role_scope(self, queryset):
        return filter_queryset_by_role(
            queryset=queryset,
            user=self.request.user,
            department_field=self.get_role_scope_department_field(),
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.apply_role_scope(queryset)
