from django.test import TestCase, Client
from django.urls import reverse

from .models import CustomUser
class SignUpTests(TestCase):
  def setUp(self):
    self.client = Client()
    self.signup_url = reverse('signup')  
    
  def test_signup_page_loads(self):
    """Test that signup page loads correctly"""
    response = self.client.get(self.signup_url)
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "Create new account")
    
  def test_successful_signup(self):
    """Test signup with valid data"""
    data = {
      'occupation': 'student',
      'name': 'Test User',
      'email': 'test@example.com',
      'username': 'testuser',
      'pwd': 'TestPass123!',
      'terms': 'on'  
    }
    
    response = self.client.post(self.signup_url, data)
    self.assertEqual(response.status_code, 302)  
    
    self.assertTrue(CustomUser.objects.filter(username='testuser').exists())
  
    
  def test_occupation_not_selected(self):
    """Test submission without selecting occupation"""
    data = {
      'username': 'testuser',
      'name': 'Test User',
      'email': 'test@example.com',
      'pwd': 'TestPass123!',
      'terms': 'on'
    }
    
    response = self.client.post(self.signup_url, data)
    self.assertEqual(response.status_code, 200)  
    
    """Test signup with already existing username"""
  def test_duplicate_username(self):
    # Create a user first
    CustomUser.objects.create_user(username='testuser', password='TestPass123!')
    
    data = {
      'occupation': 'student',
      'name': 'Test User',
      'email': 'test@example.com',
      'username': 'testuser', 
      'pwd': 'TestPass123!',
      'terms': 'on'
    }
    
    response = self.client.post(self.signup_url, data)
    self.assertEqual(response.status_code, 200)  
    
  def test_missing_required_fields(self):
    """Test submission with missing required fields"""
    
    required_fields = ['name', 'username', 'email', 'pwd', 'occupation']
    base_data = {
      'occupation': 'student',
      'name': 'Test User',
      'email': 'test@example.com',
      'username': 'testuser',
      'pwd': 'TestPass123!',
      'terms': 'on'
    }
    
    for field in required_fields:
      data = base_data.copy()
      del data[field]
      response = self.client.post(self.signup_url, data)
      self.assertEqual(response.status_code, 200)  