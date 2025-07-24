from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class AccountEmailAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(unique=True)
    verified = models.BooleanField(default=False)
    confirmation_code = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self) -> str:
        status = "Verified" if self.verified else "Unverified"
        return f"{self.email} ({status})"


class VerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user} {self.code}"

    def is_valid(self):
        return (timezone.now() - self.created_at).seconds < 300
