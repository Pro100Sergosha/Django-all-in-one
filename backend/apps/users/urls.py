from django.urls import path
from .views import RegisterView, RegisterConfirmView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
]
