from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from invoices.models import Department
from users.models import User


class DepartmentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("id", "name")


class UserSummarySerializer(serializers.ModelSerializer):
    login = serializers.CharField(source="username")
    full_name = serializers.SerializerMethodField()
    departments = DepartmentSummarySerializer(many=True)

    class Meta:
        model = User
        fields = ("id", "login", "full_name", "role", "departments")

    def get_full_name(self, obj: User) -> str:
        full_name = obj.full_name.strip()
        if full_name:
            return full_name
        return obj.username


class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["departments"] = list(user.departments.values_list("code", flat=True))
        return token

    def validate(self, attrs):
        login = attrs.get("username")
        if login:
            user_by_email = User.objects.filter(email__iexact=login).only("username").first()
            if user_by_email:
                attrs["username"] = user_by_email.username
        data = super().validate(attrs)
        data["user"] = UserSummarySerializer(self.user).data
        return data
