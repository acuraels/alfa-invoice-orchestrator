from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User


class AuthAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ivanov_aa",
            email="ivanov@example.com",
            password="SuperSecretPassword123",
            role=User.Roles.USER,
        )
        self.login_url = reverse("auth-login")
        self.refresh_url = reverse("auth-refresh")

    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "ivanov_aa",
                "password": "SuperSecretPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", response.data)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["login"], self.user.username)
        self.assertEqual(response.data["user"]["role"], User.Roles.USER)

    def test_login_with_invalid_password(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "ivanov_aa",
                "password": "WrongPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_success(self):
        refresh = str(RefreshToken.for_user(self.user))

        response = self.client.post(
            self.refresh_url,
            {"refresh": refresh},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertEqual(sorted(response.data.keys()), ["access"])

    def test_refresh_with_invalid_token(self):
        response = self.client.post(
            self.refresh_url,
            {"refresh": "invalid-token"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_response_contains_role(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "ivanov_aa",
                "password": "SuperSecretPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["role"], User.Roles.USER)
