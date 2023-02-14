"""
Tests for the DJango admin mods
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client

class AdminSiteTests(TestCase):
    """Tests for Django admin"""

    # user camel case for helper function in test class
    def setUp(self):
        """Create user and client."""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='testpass123'
        )
        # every req we make is authed with this user
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='testpass123',
            name='Test User'
        )

    def test_uses_list(self):
        """Test that users are listed on page"""
        url = reverse('admin:core_user_changelist')
        # http request
        res = self.client.get(url)
        
        self.assertContains(res,self.user.name)
        self.assertContains(res,self.user.email)


    def test_edit_user_page(self):
        """test the edit user page works"""
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code,200)
        