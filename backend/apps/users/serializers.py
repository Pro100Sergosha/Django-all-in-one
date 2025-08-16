from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User
from django.core.cache import cache
from .models import AccountEmailAddress
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
        password2 = data.pop("password2")

        if password1 != password2:
            raise serializers.ValidationError("Passwords must match.")

        pattern = r"^(?=.*\d)(?=.*[^a-zA-Z\d]).{6,}$"
        if not re.match(pattern, password1):
            raise serializers.ValidationError(
                "Password must be at least 6 characters long, contain at least one number, and one special character."
            )
        return data

    def create(self, validated_data):
        password = validated_data.pop("password1")

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
