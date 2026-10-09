from django.test import TestCase, Client
from django.urls import reverse

class LanguageDetectionTest(TestCase):
  def setUp(self):
    """Set up test client for all test methods"""
    self.client = Client()
    self.url = ''
      
  def test_dutch_language_detection(self):
    """Test Dutch language detection for Netherlands IP"""
    response = self.client.get(self.url,HTTP_X_FORWARDED_FOR='82.169.97.88',HTTP_ACCEPT_LANGUAGE='nl')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, 'Gepersonaliseerd')
      
  def test_english_language_detection(self):
    """Test English language detection for US IP"""
    response = self.client.get(self.url,HTTP_X_FORWARDED_FOR='172.56.39.0',HTTP_ACCEPT_LANGUAGE='en')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, 'Personalized')

  def test_language_fallback(self):
    """Test fallback to default language for unknown IP"""
    response = self.client.get(self.url,HTTP_X_FORWARDED_FOR='0.0.0.0')
    self.assertEqual(response.status_code, 200)