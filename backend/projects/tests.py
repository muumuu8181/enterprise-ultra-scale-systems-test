from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Project

class ProjectTests(APITestCase):
    def test_create_project(self):
        """
        Ensure we can create a new project object.
        """
        url = reverse('project-list')
        data = {'name': 'New Project', 'code': 'PRJ-NEW', 'status': 'planning'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.objects.get().name, 'New Project')

    def test_get_projects(self):
        """
        Ensure we can retrieve projects.
        """
        Project.objects.create(name="Existing Project", code="PRJ-EXIST")
        url = reverse('project-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
