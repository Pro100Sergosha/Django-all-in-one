from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, subject, template, email, code, username=None):
    try:
        html_message = render_to_string(
            f"{template}",
            context={"code": code, "username": username},
        )
        plain_message = strip_tags(html_message)

        message = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            to=[email],
        )
        message.attach_alternative(html_message, "text/html")
        message.send(fail_silently=False)

    except Exception as exc:
        raise self.retry(exc=exc)
