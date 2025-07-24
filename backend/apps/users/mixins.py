import secrets
from rest_framework import serializers
from .models import VerificationCode, User
from .tasks import send_email_task


class VerificationCodeMixin:
    def send_code(self, *, email, subject, template, username=None, code=None):
        code = code or "".join([str(secrets.choice(range(10))) for _ in range(6)])

        send_email_task.delay(
            subject=subject,
            template=template,
            email=email,
            code=code,
            username=username,
        )

        return code
