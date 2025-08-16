from rest_framework.test import APITestCase
from rest_framework import status
from django.core.cache import cache
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch
from apps.users.models import AccountEmailAddress


class RegisterTests(APITestCase):
    def setUp(self):
        self.url = reverse("register")
        self.user = User.objects.create_user(
            username="admin", email="admin@gmail.com", password="Qwerty1234@"
        )
        self.valid_data = {
            "username": "sergo",
            "email": "sergo@example.com",
            "password1": "Strong#123",
            "password2": "Strong#123",
        }
        self.exist_data = {
            "username": "admin",
            "email": "admin@gmail.com",
            "password1": "Qwerty1234@",
            "password2": "Qwerty1234@",
        }

    @patch(
        "apps.users.serializers.VerificationCodeMixin.send_code", return_value="123456"
    )
    def test_register_valid_data(self, mock_send_code):
        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Verification code sent.")
        mock_send_code.assert_called_once_with(
            email="sergo@example.com",
            subject="Verification Code",
            template="register_template.html",
        )

        cached = cache.get("register_sergo@example.com")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["email"], self.valid_data["email"])

        account = AccountEmailAddress.objects.get(email="sergo@example.com")
        self.assertEqual(account.confirmation_code, "123456")

    def test_passwords_do_not_match(self):
        data = self.valid_data.copy()
        data["password2"] = "Wrong#123"
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_weak_password(self):
        data = self.valid_data.copy()
        data["password1"] = data["password2"] = "abc"
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_invalid_email(self):
        data = self.valid_data.copy()
        data["email"] = "not-an-email"
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_missing_username(self):
        data = self.valid_data.copy()
        del data["username"]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    @patch(
        "apps.users.serializers.VerificationCodeMixin.send_code", return_value="123456"
    )
    def test_register_duplicate_username(self, mock_send_code):
        response = self.client.post(self.url, self.exist_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertFalse(mock_send_code.called)

    @patch(
        "apps.users.serializers.VerificationCodeMixin.send_code", return_value="123456"
    )
    def test_register_duplicate_email(self, mock_send_code):
        response = self.client.post(self.url, self.exist_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertFalse(mock_send_code.called)


class RegisterConfirmTests(APITestCase):
    def setUp(self):
        self.email = "test@example.com"
        self.username = "testuser"
        self.password = "Test#12345"
        self.code = "123456"

        self.url = reverse("register-confirm")

        self.account_email = AccountEmailAddress.objects.create(
            email=self.email,
            confirmation_code=self.code,
            verified=False,
        )

        cache.set(
            f"registration_{self.email}",
            {
                "username": self.username,
                "password1": self.password,
            },
        )

    def test_register_confirm_success(self):
        response = self.client.post(
            self.url,
            {
                "email": self.email,
                "code": self.code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["message"], "Email verified successfully.")

        user = User.objects.get(email=self.email)
        self.assertEqual(user.username, self.username)
        self.assertTrue(user.check_password(self.password))
        self.assertTrue(user.is_active)

        account = AccountEmailAddress.objects.get(email=self.email)
        self.assertTrue(account.verified)
        self.assertEqual(account.user, user)

    def test_register_confirm_wrong_code(self):
        response = self.client.post(
            self.url,
            {
                "email": self.email,
                "code": "654321",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.data)
        self.assertIn("Invalid confirmation code.", response.data["non_field_errors"])

    def test_register_confirm_email_not_found(self):
        response = self.client.post(
            self.url,
            {
                "email": "unknown@example.com",
                "code": self.code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.data)
        self.assertIn("Email not found.", response.data["non_field_errors"])

    def test_register_confirm_expired_cache(self):
        cache.delete(f"registration_{self.email}")

        response = self.client.post(
            self.url,
            {
                "email": self.email,
                "code": self.code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.data)
        self.assertIn(
            "Session expired. Please register again.", response.data["non_field_errors"]
        )

    def test_register_confirm_email_already_verified(self):
        self.account_email.verified = True
        self.account_email.save()

        response = self.client.post(
            self.url,
            {
                "email": self.email,
                "code": self.code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.data)
        self.assertIn(
            "This email is already verified.", response.data["non_field_errors"]
        )
