from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User
from django.core.cache import cache
from .models import AccountEmailAddress
from .mixins import VerificationCodeMixin
import re


class RegisterSerializer(VerificationCodeMixin, serializers.Serializer):
    username = serializers.CharField(
        max_length=255,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), message="Username already exists"
            )
        ],
    )
    email = serializers.EmailField(
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="Email already exists")
        ],
    )
    password1 = serializers.CharField(write_only=True, max_length=255)
    password2 = serializers.CharField(write_only=True, max_length=255)

    def validate(self, data):
        password1 = data.get("password1")
        password2 = data.get("password2")
        if password1 != password2:
            raise serializers.ValidationError("Passwords must match.")

        pattern = r"^(?=.*\d)(?=.*[^a-zA-Z\d]).{6,}$"
        if not re.match(pattern, password1):
            raise serializers.ValidationError(
                "Password must be at least 6 characters long, contain at least one number, and one special character."
            )
        return data

    def create(self, validated_data):
        email = validated_data.get("email")
        subject = "Verification Code"
        template = "register_template.html"
        cache.set(f"register_{email}", validated_data, timeout=600)
        code = self.send_code(email=email, subject=subject, template=template)
        account_email, _ = AccountEmailAddress.objects.get_or_create(email=email)
        account_email.confirmation_code = code
        account_email.save()
        return {"message": "Verification code sent."}


class RegisterConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data["email"].lower()
        code = data["code"]
        cached_data = cache.get(f"registration_{email}")

        try:
            account_email = AccountEmailAddress.objects.get(email=email)
        except AccountEmailAddress.DoesNotExist:
            raise serializers.ValidationError("Email not found.")

        if not cached_data:
            raise serializers.ValidationError("Session expired. Please register again.")

        if account_email.verified:
            raise serializers.ValidationError("This email is already verified.")

        if account_email.confirmation_code != code:
            raise serializers.ValidationError("Invalid confirmation code.")
        data["cached_data"] = cached_data
        return data

    def create(self, validated_data):
        email = validated_data["email"]
        account_email = AccountEmailAddress.objects.get(email=email)
        cached_data = validated_data.get("cached_data")

        user = User.objects.create_user(
            username=cached_data["username"],
            email=email,
        )
        user.set_password(cached_data["password1"])
        user.is_active = True
        user.save()

        account_email.user = user
        account_email.verified = True
        account_email.confirmation_code = None
        account_email.save()

        cache.delete(f"registration_{email}")
        return {"message": "Email verified successfully."}
