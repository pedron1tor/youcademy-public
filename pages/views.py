from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as log, logout as logo
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
from django.conf import settings
from django.urls import reverse
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth import get_user_model
import ipaddress
import requests
from .models import CustomUser as User

def is_ip_from_netherlands(ip: str):
  """
  Asserts whether the country code of the IP is from the netherlands,  

  Args:
      ip (str): ip from user

  Returns:
      bool: True if the IP countryCode is NL, False otherwise

  Raises:
      ValueError: If the IP address is not a valid IP
      RequestException: If there is an error when making request to ip-api.com
  """
  try:
    ipaddress.ip_address(ip)
  except ValueError:
    return "Invalid IP address"

  url = f"http://ip-api.com/json/{ip}"
  
  try:
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'success':
      country = data['countryCode']
      return country == "NL"
    else:
      return "Unable to determine location"
  except requests.RequestException:
    return "Error occurred while fetching data"
    
def home(request):
  if 'HTTP_X_FORWARDED_FOR' in request.META:
      ip = request.META['HTTP_X_FORWARDED_FOR'].split(',')[0]
  else:
      ip = request.META['REMOTE_ADDR']
  country_code = is_ip_from_netherlands(ip)
  if country_code:
    settings.LANGUAGE_CODE = "nl"
  else: 
    settings.LANGUAGE_CODE = "en"
  return render(request, "pages/home.html")

def login(request):
  """
  Django view function to authenticate users via email and password.

  Args:
    request (HttpRequest): Django request object containing POST data with 'email' and 'pwd' fields

  Returns:
    HttpResponse: 
      - Redirects to 'student_home' if user is a student
      - Redirects to 'dashboard' if user is a teacher
      - Renders 'registration/login.html' with error message if authentication fails
      - Renders 'registration/login.html' for GET requests
    

  Notes:
    - Uses Django's ModelBackend for authentication
    - Displays flash messages for invalid credentials
    - TODO: Fix redirect issue of object not subscriptable
  """
  if request.method == "POST":
    form = request.POST
    email = form["email"]
    password = form["pwd"]
    if User.objects.filter(email=email).exists():
      user = User.objects.get(email=email)
      if check_password(password, user.password):
        log(request, user,backend='django.contrib.auth.backends.ModelBackend')
        if user.occupation == "student":
          return redirect("student_home")
        elif user.occupation == "teacher":
          return redirect("dashboard")
      else:
        print("Invalid Password")
        messages.error(request, "Invalid password")
        return render(request, "registration/login.html", {"error": "Invalid password"})
    else:
      return render(request, "registration/login.html", {"error": "Invalid email"})
  return render(request, "registration/login.html")


def signup(request):
  """
  Django view function to register new users.

  Handles user registration with email, password, occupation, name, and username.
  Performs validation checks and creates a new user if all validations pass.

  Args:
    request (HttpRequest): Django request object containing POST data with fields:
      - email: User's email address
      - pwd: Password
      - occupation: User's role/occupation (teacher or student)
      - name: Full name
      - username: Desired username

  Returns:
    HttpResponse:
      - Redirects to 'login' page on successful registration
      - Renders 'pages/sign-up.html' with error messages if:
        * Required fields are missing
        * Email already exists
        * Username already exists
        * Password validation fails
        * Any other error occurs
      - Renders 'pages/sign-up.html' for GET requests

  Raises:
    KeyError: When required fields are missing from the form
    ValidationError: When password doesn't meet Django's validation requirements
    Exception: For any other unexpected errors

  Notes:
    - Uses Django's password validation system
    - Displays flash messages for success/errors using Django messages framework
    - Error messages include the 'danger' extra tag for styling
  """
  if request.method == "POST":
    form = request.POST
    try:
      email = form["email"]
      password = form["pwd"]
      prof = form["occupation"]
      name = form["name"]
      username = form["username"]
      # Check if email or username already exists
      if User.objects.filter(email=email).exists():
        messages.error(request, 'Email already exists', extra_tags="danger")
        return render(request, 'pages/sign-up.html', {"error": "Email already exists"})
      if User.objects.filter(username=username).exists():
        messages.error(request, 'Username already exists', extra_tags="danger")
        return render(request, 'pages/sign-up.html', {"error": "Username already exists"})
      # Validate the password
      try:
        password_validation.validate_password(password, User(username=username, email=email))
      except ValidationError as e:
        messages.error(request, ' '.join(e.messages), extra_tags="danger")
        return render(request, 'pages/sign-up.html', {"error": e.messages})
      # Create and save the user
      user = User(email=email, occupation=prof, name=name, username=username)
      user.set_password(password)
      user.save()
      messages.success(request, 'Account created successfully. Please log in.')
      return redirect("login")
    except KeyError as e:
      messages.error(request, f'Please fill in all the fields. Missing field: {str(e)}', extra_tags="danger")
      return render(request, 'pages/sign-up.html', {"error": f"Missing field: {str(e)}"})
    except Exception as e:
      messages.error(request, f'An error occurred: {str(e)}', extra_tags="danger")
      return render(request, 'pages/sign-up.html', {"error": str(e)})
  return render(request, 'pages/sign-up.html')

def logout(request):
  logo(request)
  return redirect('home')




def purchase(request): 
  if 'HTTP_X_FORWARDED_FOR' in request.META:
      ip = request.META['HTTP_X_FORWARDED_FOR'].split(',')[0]
  else:
      ip = request.META['REMOTE_ADDR']
  country_code = is_ip_from_netherlands(ip)
  if country_code:
    settings.LANGUAGE_CODE = "nl"
  else: 
    settings.LANGUAGE_CODE = "en"
  return render(request, "pages/purchase.html")

def aipolicy(request): 
  if 'HTTP_X_FORWARDED_FOR' in request.META:
      ip = request.META['HTTP_X_FORWARDED_FOR'].split(',')[0]
  else:
      ip = request.META['REMOTE_ADDR']
  # Get the country code
  country_code = is_ip_from_netherlands(ip)
  if country_code:
    settings.LANGUAGE_CODE = "nl"
  else: 
    settings.LANGUAGE_CODE = "en"
  return render(request, "pages/aipolicy.html")

def custom_500_view(request): 
   return render(request, "500.html")

@login_required
def onboard(request):
  """
  Handle user onboarding after social authentication.
  
  Add occupation, timezone, and color preferences for users who sign in with
  Google or Microsoft authentication. Use atomic transaction to ensure data consistency.
  
  :param request: Django request object containing POST data
  :type request: HttpRequest
  
  :requires: POST data fields:
    * occupation - User's role (student/teacher)
    * timezone - User's preferred timezone
    * color - User's preferred UI color
  
  :returns: Different responses based on request type:
    * For AJAX requests: JsonResponse with redirect URL
    * For regular requests:
      - Redirects to 'dashboard' if user is a teacher
      - Redirects to 'student_home' if user is a student
      - Renders 'pages/onboard.html' if:
        + GET request
        + Invalid occupation
        + Update fails
  :rtype: HttpResponse or JsonResponse
  
  :decorators: login_required
  
  :raises: No specific exceptions (will return to onboarding page on failure)
  
  :notes:
    * Uses atomic transaction for data consistency
    * Supports both AJAX and regular form submissions
    * Verifies successful update before redirect
  """
  if request.method == "POST":
    User = get_user_model()
    user = User.objects.get(pk=request.user.pk)
    occupation = request.POST['occupation']
    timezone = request.POST['timezone']
    color = request.POST['color']
    
    with transaction.atomic():
      user.occupation = occupation
      user.timezone = timezone
      user.color = color
      user.save()
      
      # Fetch the user again to confirm changes
      updated_user = User.objects.get(pk=user.pk)
      if (updated_user.occupation == occupation and
          updated_user.timezone == timezone and
          updated_user.color == color):
        
        if occupation == 'teacher':
          redirect_url = reverse('dashboard')
        elif occupation == 'student':
          redirect_url = reverse('student_home')
        else:
          redirect_url = None
          
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
          return JsonResponse({'redirect_url': redirect_url})
        else:
          return redirect(redirect_url) if redirect_url else render(request, "pages/onboard.html", {})
                  
  return render(request, "pages/onboard.html", {})