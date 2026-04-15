def filter_queryset_by_role(queryset, user, department_field: str = "department"):
    if not getattr(user, "is_authenticated", False):
        return queryset.none()

    if getattr(user, "is_superuser", False):
        return queryset

    departments = getattr(user, "departments", None)
    if departments is None:
        return queryset.none()

    if department_field.endswith("__code"):
        department_values = list(departments.values_list("code", flat=True))
    else:
        department_values = list(departments.values_list("id", flat=True))

    if not department_values:
        return queryset.none()

    return queryset.filter(**{f"{department_field}__in": department_values})


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
