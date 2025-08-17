from django.urls import path
from .views import TaskViewSet

urlpatterns = [
    path("tasks/", TaskViewSet.as_view(), name="tasks"),
    path("tasks/<int:pk>/", TaskViewSet.as_view(), name="task_detail"),
]
