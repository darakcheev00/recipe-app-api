"""
Test for the health check api
"""

from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient


class HealthCheckTests(TestCase):
    """Test the health check API"""

    def test_health_check(self):
        """test health check api"""
        client = APIClient()
        url = reverse('health-check')
        res = self.client.get(url)
        print(f"------------------ URL: {url}")

        self.assertEqual(res.status_code, status.HTTP_200_OK)