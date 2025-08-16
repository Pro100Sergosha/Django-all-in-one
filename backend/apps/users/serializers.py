from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
import re


class RegisterSerializer(serializers.Serializer):
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
        username = validated_data.get("username")
        email = validated_data.get("email")
        password = validated_data.get("password1")

        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")
        data["user"] = user
        return data

    def create(self, validated_data):
        user = validated_data["user"]
        token = RefreshToken.for_user(user)
        return {"access": str(token.access_token), "refresh": str(token)}
