from rest_framework.views import APIView
from rest_framework import status
from rest_framework import permissions
from rest_framework import filters
from rest_framework.response import Response
from django.db.models import Q
from .pagination import TaskPagination
from .models import Task
from .serializers import TaskSerializer


class TaskViewSet(APIView):
    pagination_class = TaskPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "status", "priority"]
    ordering_fields = ["created_at", "updated_at", "due_date", "priority", "status"]
    filterset_fields = ["status", "priority", "owner"]
    ordering = ["created_at"]

    def get_permissions(self):
        if self.request.method == "POST" or self.request.method == "PATCH":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save(owner=request.user)
            return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk=None):
        if pk:
            try:
                task = Task.objects.get(pk=pk)
            except Task.DoesNotExist:
                return Response(
                    {"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND
                )
            serializer = TaskSerializer(task)
            return Response(serializer.data)

        if request.user.is_authenticated:
            tasks = Task.objects.filter(owner=request.user)
        else:
            tasks = Task.objects.all()

        search_query = request.GET.get("search")
        if search_query:
            tasks = tasks.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(status__icontains=search_query)
            )

        status_filter = request.GET.get("status")
        if status_filter:
            tasks = tasks.filter(status=status_filter)

        priority_filter = request.GET.get("priority")
        if priority_filter:
            tasks = tasks.filter(priority=priority_filter)

        ordering = request.GET.get("ordering")
        allowed_ordering_fields = ["created_at", "due_date", "priority"]
        if ordering:
            order_field = ordering.lstrip("-")
            if order_field in allowed_ordering_fields:
                tasks = tasks.order_by(ordering)
        else:
            tasks = tasks.order_by("-created_at")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(tasks, request, view=self)

        serializer = TaskSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def patch(self, request, pk=None):
        try:
            task = Task.objects.get(pk=pk)
            if task.owner != request.user:
                return Response(
                    {"detail": "You do not have permission to edit this task."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except Task.DoesNotExist:
            return Response(
                {"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        try:
            task = Task.objects.get(pk=pk, owner=request.user)
        except Task.DoesNotExist:
            return Response(
                {"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND
            )

        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
