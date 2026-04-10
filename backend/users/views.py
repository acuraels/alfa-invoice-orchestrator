from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.serializers import LoginSerializer


class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer


class RefreshView(TokenRefreshView):
    permission_classes = (AllowAny,)
