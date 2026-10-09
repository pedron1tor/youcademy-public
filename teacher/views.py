from django.shortcuts import render, redirect
from pages.forms import CourseForm, PracticeSessionForm, ReadingStrategyForm
from google.cloud import pubsub_v1
from pages.models import *
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.files.storage import FileSystemStorage
import os
from django.http import JsonResponse
# from mainframe.storages import PrivateMediaStorage
import numpy as np
from django.conf import settings
from pymongo import DESCENDING
import datetime
from django.contrib.auth import get_user_model
import json
import base64
import time
from .decorators import teacher_required
from utils.helpers import teacher_feedback
User = get_user_model()
@teacher_required
def dashboard(request):           
  """
  Django view for teacher dashboard management.
  Handles course creation, reading strategy setup, and file uploads.

  Args:
      request (HttpRequest): Django request object containing:
          - POST data (optional):
              * course_creation: Course form data
              * reading_strategy: Strategy form data
              * assignment_upload: File upload data

  Returns:
      HttpResponse: One of:
      - Redirect to dashboard after successful form submission
      - Renders "teacher/dashboard.html" with context:
          * User information
          * Course form
          * Reading strategy form
          * Existing courses
          * Available strategies
          * Navigation data

  Notes:
      - Requires teacher authorization (@teacher_required)
      - Handles file storage for uploaded assignments
      - Manages course and strategy creation
  """                                                                                                                                           
  if request.method == "POST":
    if "course_creation" in request.POST:
      course_form = CourseForm(request.POST)
      print(request.POST)
      if course_form.is_valid():
        print('The form was valid')
        course = course_form.save(commit=False)
        course.teacher = request.user
        course.save()
        return redirect("dashboard")
      else:
        print(course_form.errors)
    if "reading_strategy" in request.POST:
      reading_strategy_form = ReadingStrategyForm(request.POST)
      if reading_strategy_form.is_valid():
        reading_strategy = reading_strategy_form.save()
        reading_strategy.save()
        return redirect("dashboard")
      else:
        print(reading_strategy_form.errors)
    if "assignemnt_upload" in request.POST:
      print("The file was uploaded...")

      myfile = request.FILES['file']
      fs = FileSystemStorage(location=os.path.join('uploads', 'pdfs'))  # Customize the location
      filename = fs.save(myfile.name, myfile)
      # The file is now saved in the specified location, and `filename` contains the actual name of the saved file.
      return redirect("dashboard")
  else:
    course_form = CourseForm(initial={'teacher': request.user})
    reading_strategy_form = ReadingStrategyForm()
    courses = Course.objects.filter(teacher=request.user)
    strategies = Strategy.objects.all()

  return render(request, "teacher/dashboard.html", {"name": request.user.name.split()[0], "occupation": request.user.occupation, "course_form":course_form, "reading_strategy_form": reading_strategy_form,"courses": courses, "strategies": strategies, 
  "path": "Dashboard", "title": "Dashboard", "class_len":len(courses)})



@teacher_required
def teacher_course(request, course_id):
  """
  Django view for managing individual course details and settings.
  Handles practice sessions, CEFR ratings, and course prompts.

  Args:
      request (HttpRequest): Django request object containing:
          - POST data (optional):
              * practice_session: Practice form data
              * cefr: Student CEFR ratings
              * add_prompt: Writing prompt creation
              * add_vocab: Vocabulary additions
      course_id (int): Course identifier

  Returns:
      HttpResponse: One of:
      - Redirect to course view after form submission
      - Renders "teacher/course.html" with context:
          * Course information
          * Practice session form
          * Student data
          * Questions
          * Lesson plans
          * Navigation data

  Notes:
      - Requires teacher authorization (@teacher_required)
      - Manages student metrics and progress
      - Handles MongoDB interactions for lesson plans
      - Supports writing prompt management
  """
  if request.method == "POST":
    if "practice_session" in request.POST:
      practice_form = PracticeSessionForm(request.POST)
      if practice_form.is_valid():
        practice = practice_form.save(commit=False)
        practice.save()
        return redirect("teacher_class", course_id=course_id)
      else:
        print(practice_form.errors)
      return redirect("teacher_class", course_id=course_id)

    elif "cefr" in request.POST:
      for student in Course.objects.get(id=course_id).students.all():
        cefr_rating = request.POST.get(f"cefr_rating_{student.id}")
        estimated_level = request.POST.get(f"level_{student.id}")
        # Only proceed if cefr_rating and estimated_level are provided
        if cefr_rating and estimated_level and not student.diagnostic:
          # Create a new Metrics instance and save it
          metrics = Metrics(
              student=student,
              estimated_cefr_rating=cefr_rating,
              estimated_level=estimated_level
          )
          metrics.save()
      return redirect("teacher_class", course_id=course_id)
    elif "add_prompt" in request.POST: 
      prompt_name = request.POST['prompt_name']
      prompt = request.POST["prompt"]
      write_prompt = WritingPrompts(name=prompt_name, prompt=prompt)
      write_prompt.save()
      course_obj = Course.objects.get(id=course_id)
      course_obj.writing_prompts.add(write_prompt)
      return redirect("teacher_class", course_id=course_id)
    elif "add_vocab" in request.POST:
      return redirect("teacher_class", course_id=course_id)

      
  practice_form = PracticeSessionForm(teacher=request.user)
  sessions = PracticeSessions.objects.filter(course=course_id)
  questions = StudentTeacherQuestion.objects.filter(course=course_id)
  students = list(Course.objects.get(id=course_id).students.all())
  
  for student in students: 
    student.progress = 80
    student.readiness = 90
  lesson_plans = list(settings.MDB.writing.find({'user_id': request.user.id}).sort('updated_at', DESCENDING))
  for x in lesson_plans:
    x['id'] = x['_id']
  return render(request, "teacher/course.html", {"course_id": course_id, "practice_form": practice_form, "sessions": sessions,
                                                 "students": students, "total_students": Course.objects.get(id=course_id).students.count(),  "questions":questions, 
                                                 "path": f"Dashboard / Course / {Course.objects.get(id=course_id).name}", "go_back_url": "/teacher/dashboard", "title": Course.objects.get(id=course_id).name,
                                                 "lesson_plans": lesson_plans})
@teacher_required
def teacher_assessment(request, course_id):
  """
  Django view for course assessment management.
  Displays assessment interface for specific course.

  Args:
      request (HttpRequest): Django request object
      course_id (int): Course identifier

  Returns:
      HttpResponse: Renders "teacher/assessment.html" with context:
          * Course identifier
          * Navigation data
          * Page title

  Notes:
      - Requires teacher authorization (@teacher_required)
  """
  return render(request, "teacher/assessment.html", {"course_id": course_id, "path": "Dashboard / Course / Assessment", "title": "Assessment", "go_back_url": f"/teacher/class/{course_id}"})

@teacher_required
def teacher_student(request, course_id, student_id):
  """
  Django view for individual student management and metrics.
  Handles student-specific data and progress tracking.

  Args:
      request (HttpRequest): Django request object
      course_id (int): Course identifier
      student_id (int): Student identifier

  Returns:
      HttpResponse: Renders "teacher/student.html" with context:
          * Course identifier
          * Student information
          * Student metrics

  Notes:
      - Requires teacher authorization (@teacher_required)
      - Tracks various student performance metrics
  """
  if request.method == "POST":
    form = request.POST
  metrics_list = [
      'quiz_score_average', 'estimated_lexile_level', 'confidence_score'
  ]

  return render(
      request, "teacher/student.html", {
          "course_id": course_id,
          "student_id": student_id,
          "student": CustomUser.objects.get(id=student_id)
      })

@teacher_required
def lesson_plans(request):
  """
  Django view for managing teacher lesson plans.
  Handles creation and access to existing lesson plans.

  Args:
      request (HttpRequest): Django request object containing:
          - POST data (optional):
              * writing_id: Existing lesson plan identifier

  Returns:
      HttpResponse: One of:
      - Redirect to lesson editor for new/existing plan
      - Renders "teacher/lesson_plans.html" with context:
          * Existing lesson plans
          * Plan count
          * Navigation data

  Notes:
      - Requires teacher authorization (@teacher_required)
      - Integrates with MongoDB for plan storage
      - Orders plans by last update time
  """
  texts = list(settings.MDB.writing.find({'user_id': request.user.id}).sort('updated_at', DESCENDING))
  for x in texts:
    x['id'] = x['_id']
  if request.method == "POST":
    new_text = str(uuid.uuid4())
    if "writing_id" in request.POST:
      request.session['write_id'] = request.POST["writing_id"]
      return redirect('lesson_editor', qid=request.POST["writing_id"])
    return redirect('lesson_editor', qid=new_text)
    
  return render(request, "teacher/lesson_plans.html", {"path": "Lesson Plans", "mongo_counter": len(texts), "texts": texts, "title": "Custom Lesson Plans"})

@teacher_required 
def lesson_editor(request, qid):
  """
  Django view for lesson plan editing interface.
  Provides editing environment for lesson plans.

  Args:
      request (HttpRequest): Django request object
      qid (str): Unique identifier for lesson plan

  Returns:
      HttpResponse: Renders "teacher/lesson_editor.html" with context:
          * User information
          * Editor configuration
          * API endpoints
          * Navigation data

  Notes:
      - Requires teacher authorization (@teacher_required)
      - Sets up WebSocket connection for real-time editing
  """
  request.session['qid'] = str(qid)
  request.session['user_id'] = request.user.id
  return render(request, "teacher/lesson_editor.html", {
      "user_id": request.user.id,
      "qid": qid, 
      "data_url": settings.URL, 
      "ws_url": settings.WS_URL,
      "path": " Lesson Plans / New Document",
      "title": "New Lesson Plan", 

  })

def get_signed_url(request, file_name):
    """
    Django view for generating signed URLs for file access.
    Creates secure access URLs for private media files.

    Args:
        request (HttpRequest): Django request object
        file_name (str): Name of file to access

    Returns:
        JsonResponse: Contains:
            * signed_url: Secure URL for file access

    Notes:
        - Uses PrivateMediaStorage for secure file access
        - Generates time-limited access URLs
    """
    storage = PrivateMediaStorage()
    signed_url = storage.url(file_name)
    return JsonResponse({'signed_url': signed_url})

@teacher_required
def dataview(request, course_id):
  """
  Django view for course data visualization and analysis.
  Manages reading session data and analytics.

  Args:
      request (HttpRequest): Django request object containing:
          - POST data (optional):
              * practice_id: Reading practice identifier
      course_id (int): Course identifier

  Returns:
      HttpResponse: One of:
      - Redirect to practice view for specific session
      - Renders "teacher/dataview.html" with context:
          * Reading session data
          * Navigation information
          * Course identifier

  Notes:
      - Requires teacher authorization (@teacher_required)
      - Integrates with MongoDB for session data
      - Handles timezone conversions for timestamps
  """
  readings = list(settings.MDB_1.readings.find({'course_id': course_id}).sort('time', DESCENDING))
  for x in readings:
    x['name'] = User.objects.get(id=x['user_id']).name
    utc_time = x.get('time')
    if x.get('time'):
      if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=timezone.utc)
      # Convert to the user's timezone
      user_time = timezone.localtime(utc_time)
      # Format the datetime in the user's local time
      x["time"] = user_time.strftime('%B %d, %Y at %I:%M %p %Z')
  if request.method == "POST": 
    practice_id = request.POST["practice_id"]
    request.session["questions"] = True
    request.session["review"] = True
    doc = settings.MDB_1.readings.find_one({'practice_id': practice_id})
    request.session["text"] = (doc['title'], doc['text'], doc['query'], doc.get("yellow_highlights", None), doc.get("pink_highlights", None), doc.get('notes', None))
    return redirect("teacher_practice_view", course_id=course_id, practice_id=request.POST["practice_id"])
  return render(request, "teacher/dataview.html", {"path": "Dashboard / Data View", "title": "Data View", "readings": readings, "go_back_url": f"/teacher/class/{course_id}", "course_id":course_id})

@teacher_required
def teacher_practice_view(request, course_id, practice_id):
  """
  Django view for reviewing student practice sessions.
  Displays reading content and student interactions.

  Args:
      request (HttpRequest): Django request object
      course_id (int): Course identifier
      practice_id (str): Practice session identifier

  Returns:
      HttpResponse: One of:
      - Redirect to questions view after form submission
      - Renders "student/practice.html" with context:
          * Reading content
          * Student highlights and notes
          * Session status
          * Navigation data

  Notes:
      - Requires teacher authorization (@teacher_required)
      - Manages session state and quiz data
      - Handles text formatting and display
  """
  text = request.session.get("text")
  request.session['practice_id'] = str(practice_id)
  reading_title = text[0]
  story = request.session.get("text")[1]
  story_paragraphs = story.split("\n\n")
  request.session['course_id'] = course_id
  if request.method == "POST":
    form = request.POST
    request.session['notes'] = text[5]
    quiz = None
    while not quiz:
      quiz = settings.MDB_1.questions.find_one({"practice_id": str(practice_id)}, {"_id": 0})
      time.sleep(5) 
    request.session["quiz"] = quiz['quiz']
    
    return redirect("teacher_questions_view", question_num=1,)
  return render(request, "student/practice.html", {"path": "Dashboard / Course / Practice View", "title": "Practice View", 
                                                   "name": request.user.name,
      "occupation": request.user.occupation,
      "title": reading_title,
      "text": story_paragraphs,
      "pink_highlights": base64.b64encode(json.dumps(text[4]).encode('utf-8')).decode('utf-8'), 
      "yellow_highlights": base64.b64encode(json.dumps(text[3]).encode('utf-8')).decode('utf-8'),
      "notes": text[5],
      "questions": request.session.get("questions", False),
      "path": f"English / Reading / {reading_title}",
      "review": request.session.get("review"),})

@teacher_required
def teacher_questions_view(request, question_num): 
  """
  Django view for reviewing student question responses.
  Manages question review and feedback submission.

  Args:
      request (HttpRequest): Django request object containing:
          - POST data (optional): Teacher feedback
      question_num (int): Current question number

  Returns:
      HttpResponse: One of:
      - Redirect to dashboard after feedback submission
      - Renders "student/questions.html" with context:
          * Question data
          * Student responses
          * Reading content
          * Navigation elements
          * Teacher feedback interface

  Notes:
      - Requires teacher authorization (@teacher_required)
      - Handles feedback submission and storage
      - Supports multiple question types
  """
  quiz = request.session.get("quiz")
  reading_title = request.session.get("text")[0]
  text = request.session.get("text")[1].split("\n\n")
  current_question = next(
        (q for q in quiz["questions"] if q["question_num"] == question_num), None
    )
  story = request.session.get("text")[1]
  story_paragraphs = story.split("\n\n")
  if request.method == "POST": 
    #TODO add logic to save feedback for students on open ended questions...
    #TODO ensure that the text area does not lose info when you reload...
    user_answers = dict(request.POST)
    practice_id = request.session['practice_id']
    questions = settings.MDB_1.questions.find_one({"practice_id": practice_id})
    teacher_feedback(practice_id, questions,user_answers)
    return redirect("data_dashboard", course_id=request.session.get("course_id"))
  context = {
        "path": "Dashboard / Course / Practice View / Questions", "title": "Questions", 
        "pink_highlights": request.session.get("pink_highlights"),
        "yellow_highlights": base64.b64encode(json.dumps(quiz['questions'][question_num-1].get("yellow_highlights")).encode('utf-8')).decode('utf-8') if quiz['questions'][question_num-1].get("yellow_highlights") else None,
        "notes": request.session.get("notes"),
        "path": f"Dashboard / English / Reading / {reading_title} ",
        "question": current_question,
        "title": reading_title,
        "text": text,
        "last_question": question_num == len(quiz["questions"]),
        "first_question": question_num == 1,
        "text": story_paragraphs,
        "quiz_len": len(quiz["questions"]),
        "question_num": question_num,
        "questions": quiz["questions"],
        "prefill_notes": request.session.get("notes"),
        "go_back_url": "/student/",
        "review": request.session.get("review"), 
        "user_answer":(quiz['questions'][question_num-1].get("user_answer") if quiz['questions'][question_num-1].get('user_answer_index') is None else (quiz['questions'][question_num-1].get('user_answer_index') + 1 if quiz['questions'][question_num-1].get('type') not in ['highlight', 'open'] else quiz['questions'][question_num-1].get('user_answer'))),
        "correct_answer":quiz['questions'][question_num-1].get('correct_index')+1 if quiz['questions'][question_num-1].get('type') not in ['highlight', 'open'] else None,
        "feedback_list" : quiz['questions'][question_num-1].get('feedback') if quiz['questions'][question_num-1].get('type') in ['highlight', 'open'] else None,
        "teacher": True}
  return render(request, "student/questions.html", context)

@teacher_required
def email_us(request):
  """
  Django view for email contact interface.
  Provides email communication functionality.

  Args:
      request (HttpRequest): Django request object

  Returns:
      HttpResponse: Renders "teacher/email_us.html" with context:
          * Page title
          * Navigation path

  Notes:
      - Requires teacher authorization (@teacher_required)
  """
  return render(request, "teacher/email_us.html", {"title": "Email Us", "Path": "Dashboard / Email Us"})

@teacher_required
def classes(request):
  """
  Django view for displaying teacher's course list.
  Shows overview of all courses taught by teacher.

  Args:
      request (HttpRequest): Django request object

  Returns:
      HttpResponse: Renders "teacher/classes.html" with context:
          * List of teacher's courses

  Notes:
      - Requires teacher authorization (@teacher_required)
      - Filters courses by current teacher
  """
  courses = Course.objects.filter(teacher=request.user)
  return render(request, "teacher/classes.html", {"courses": courses})

@teacher_required
def writing_prompts(request, course_id):
  """
  Django view for managing course writing prompts.
  Displays and manages writing assignments.

  Args:
      request (HttpRequest): Django request object
      course_id (int): Course identifier

  Returns:
      HttpResponse: Renders "teacher/writing-prompts.html" with context:
          * Course prompts
          * Navigation data

  Notes:
      - Requires teacher authorization (@teacher_required)
      - Retrieves course-specific writing prompts
  """
  prompts = Course(id=course_id).writing_prompts.all()
  return render(request, "teacher/writing-prompts.html", {"prompts": prompts, "go_back_url": f"/teacher/class/{course_id}"})