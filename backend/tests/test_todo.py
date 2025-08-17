from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from apps.todo.models import Task
from django.contrib.auth.models import User


class TodoTests(APITestCase):
    def setUp(self):
        self.tasks_url = reverse("tasks")
        self.admin = User.objects.create_user(username="admin", password="testpass")
        self.user = User.objects.create_user(username="user", password="testpass")
        self.task = Task.objects.create(
            title="Test task",
            description="Test description",
            status="pending",
            priority="high",
            due_date="2025-12-31",
            owner=self.admin,
        )
        self.valid_data = {
            "title": "New title",
            "description": "New description",
            "status": "completed",
            "priority": "high",
            "due_date": "2025-12-30",
        }
        self.invalid_data = {
            "title": "",
            "description": "",
            "status": "invalid",
            "priority": "invalid",
            "due_date": "invalid",
        }

    def test_unauthorized_create_task(self):
        response = self.client.post(self.tasks_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_get_task(self):
        response = self.client.get(self.tasks_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], Task.objects.count())

    def test_create_valid_data(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(self.tasks_url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)
        self.assertIn("title", response.data)
        self.assertIn("description", response.data)
        self.assertIn("status", response.data)
        self.assertIn("priority", response.data)
        self.assertIn("due_date", response.data)

    def test_create_invalid_data(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(self.tasks_url, self.invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)
        self.assertIn("description", response.data)
        self.assertIn("status", response.data)
        self.assertIn("priority", response.data)
        self.assertIn("due_date", response.data)

    def test_get_nonexistent_task(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(
            reverse("task_detail", kwargs={"pk": 4}), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Task not found.")

    def test_get_existing_task(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(
            reverse("task_detail", kwargs={"pk": 1}), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test task")
        self.assertIn("title", response.data)
        self.assertIn("description", response.data)
        self.assertIn("status", response.data)
        self.assertIn("priority", response.data)
        self.assertIn("due_date", response.data)

    def test_get_users_tasks(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.tasks_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_get_filtered_tasks(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(
            self.tasks_url,
            data={
                "ordering": "created_at",
                "search": "high",
                "status": "completed",
                "page_size": "10",
                "page": "1",
                "priority": "high",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_fails_not_owner(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse("task_detail", kwargs={"pk": 1}),
            data={"title": "Users title"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_fails_task_not_found(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse("task_detail", kwargs={"pk": 5}), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_valid_data(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            reverse("task_detail", kwargs={"pk": 1}),
            data=self.valid_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("title", response.data)
        self.assertIn("description", response.data)
        self.assertIn("status", response.data)
        self.assertIn("priority", response.data)
        self.assertIn("due_date", response.data)

    def test_update_invalid_data(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            reverse("task_detail", kwargs={"pk": 1}),
            data=self.invalid_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)
        self.assertIn("description", response.data)
        self.assertIn("status", response.data)
        self.assertIn("priority", response.data)
        self.assertIn("due_date", response.data)

    def test_delete_nonexistent_task(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(
            reverse("task_detail", kwargs={"pk": 4}), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Task not found.")

    def test_delete_existing_task(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(
            reverse("task_detail", kwargs={"pk": 1}), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
