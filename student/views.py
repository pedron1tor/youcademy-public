import json, os, time, uuid, requests, threading
from datetime import datetime, timedelta
from groq import Groq
from pymongo import DESCENDING
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils import timezone
from pages.models import (Course, StudentTeacherQuestion,  WritingPrompts, CustomUser, LearningStreak, Reviews, Feedback)
from utils.helpers import create_flashcards, CreateReading,  Publisher, LexileAlgorithm
from .decorators import student_required
from django.http import HttpResponse
import base64
import pytz 
from pymongo import ReturnDocument

@student_required
def student_home(request):
  """
  Django view for the student dashboard showing review items for the spaced repetition algorithm, courses, and learning stats.

  Displays upcoming reviews, enrolled courses, learning streaks, and handles course 
  enrollment. Redirects to diagnostic tests when requested.

  Args:
    request (HttpRequest): Django request object with optional POST data:
      - diagnostic: Course ID for diagnostic test
      - course_code: Code for course enrollment 
      - course_name: Name for course enrollment

  Returns:
    HttpResponse:
      - Redirects to 'query' view if diagnostic test requested
      - Renders 'student/student_signup.html' with context:
        * courses: List of enrolled Course objects
        * path: Navigation breadcrumb ("Dashboard")
        * title: Page title 
        * today: Current date
        * tomorrow: Next day's date
        * seconds_until_review: Time until next review in seconds
        * last_course_id: Most recently enrolled course (if any)
        * learning_streak: Current learning streak count

  Notes:
    - Requires student authorization (@student_required) Information on decorators
    - Updates learning streak on each visit
    - Orders reviews by date
    - Shows error message if course enrollment fails
    - Handles both diagnostic test requests and course enrollment
  """
  queryset = Reviews.objects.filter(student=CustomUser(id=request.user.id)).order_by('review_date')
  nearest_future_review = queryset.filter(review_date__gt=timezone.now()).order_by('review_date').first()
  if nearest_future_review: 
    time_diff = nearest_future_review.review_date - timezone.now()
    time = round(time_diff.total_seconds(), 0)
  else: 
    time = 0
  courses = list(Course.objects.filter(students=request.user))
  streak, created = LearningStreak.objects.get_or_create(user=request.user)
  streak.update_streak()
  learning_streak = streak.current_streak
  if request.method == "POST":
    if "diagnostic" in request.POST:
      course_id = request.POST.get("diagnostic")
      return redirect("query", course_id=course_id)
    else:
      course = Course.objects.filter(course_code=request.POST.get("course_code"), name=request.POST.get("course_name")).first()
      if course:
        course.students.add(request.user)
      else:
        messages.error(request, "No course found with that name and code")
      return redirect("student_home")
  return render(request, "student/student_signup.html", {"courses": courses,"path": "Dashboard", "title": "Student Dashboard", 'today': timezone.now().date(),'tomorrow': (timezone.now()+timedelta(days=1)).date(), "seconds_until_review": time, "last_course_id": courses[-1] if len(courses) > 0 else None, "learning_streak": learning_streak, })

@student_required
def course(request, course_id):
   """
   Django view for handling course-related actions and navigation for students.
   
   Manages writing prompts, pronunciation practice sessions, and course navigation.
   Stores session data for maintaining state across redirects.

   Args:
       request (HttpRequest): Django request object containing:
           POST data (optional):
               - prompt: Writing prompt text
               - qid: Question ID for writing
               - practice_id: Pronunciation practice session ID
       course_id (int): Course identifier

   Returns:
       HttpResponse: One of:
           - Redirect to:
               * writing view with qid (for writing prompts)
               * running_record view (for paragraph pronunciation)
               * pronunciation view (for sentence pronunciation)
           - Renders "student/learning_path.html" with context:
               * path: Course name
               * title: Course name
               * course_id: Course ID
               * go_back_url: Return URL ("/student/")

   Session Data Set:
       - course_id: Current course ID
       - prompt: Selected writing prompt
       - practice_id: Current practice session
       - review: Boolean flag for review mode
       - text: Full text for running record
       - sentences: Sentence data for pronunciation practice

   Notes:
       - Requires student authorization (@student_required)
       - Updates pronunciation practice timestamp in MongoDB
       - Handles both paragraph and sentence-level pronunciation practice
   """
   request.session['course_id'] = course_id

   if request.method == "POST":
       if "prompt" in request.POST:
           request.session["prompt"] = request.POST["prompt"]
           return redirect("writing", qid=request.POST["qid"])
           
       elif "practice_id" in request.POST:
           practice_id = request.POST["practice_id"]
           print(practice_id)
           
           doc = settings.MDB_1.pronunciation.find_one_and_update(
               {"practice_id": practice_id},
               {"$set": {"last_viewed": timezone.now()}},
               return_document=ReturnDocument.AFTER,
               projection={"_id": 0, "created_at": 0, "last_viewed": 0}
           )
           print(doc)
           
           request.session['practice_id'] = practice_id
           request.session["review"] = True
           
           if doc.get('text'):
               request.session["text"] = doc['text']
               return redirect("running_record", course_id=course_id, practice_id=practice_id)
           else:
               request.session["sentences"] = doc
               return redirect("pronunciation", course_id=course_id, question_id=1)

   return render(
       request,
       "student/learning_path.html",
       {
           "path": Course.objects.get(id=course_id).name,
           "title": Course.objects.get(id=course_id).name,
           "course_id": course_id,
           "go_back_url": "/student/"
       }
   )

@student_required
def reading_menu(request, course_id):
   """
   Django view for managing student reading practice sessions and menu display.
   
   Handles both viewing the reading menu and initiating reading practice sessions.
   Stores reading text and associated metadata in session for practice.

   Args:
       request (HttpRequest): Django request object containing:
           POST data (optional):
               - practice_id: Identifier for specific reading practice
       course_id (int): Course identifier

   Returns:
       HttpResponse: One of:
           - Redirect to:
               * practice view with practice_id when starting a practice session
           - Renders "student/reading_menu.html" with context:
               * path: Navigation breadcrumb ("English / Reading")
               * title: Page title ("Reading")
               * course_id: Course identifier
               * texts: List of user's reading practices (reversed chronological order)

   Session Data Set:
       - questions (bool): True to indicate questions mode
       - review (bool): True to indicate review mode
       - text (tuple): Contains:
           * title: Reading title
           * text: Reading content
           * query: Associated query
           * yellow_highlights: Optional highlighted sections
           * pink_highlights: Optional highlighted sections
           * notes: Optional reading notes

   Notes:
       - Requires student authorization (@student_required)
       - Retrieves reading data from MongoDB (settings.MDB_1.readings)
       - Orders readings in reverse chronological order
       - Preserves highlights and notes from previous sessions
   """
   if request.method == "POST":
       practice_id = request.POST["practice_id"]
       request.session["questions"] = True
       request.session["review"] = True
       
       doc = settings.MDB_1.readings.find_one({"practice_id": practice_id})
       request.session['text'] = (
           doc['title'],
           doc['text'],
           doc['query'],
           doc.get('yellow_highlights', None),
           doc.get('pink_highlights', None),
           doc.get('notes', None)
       )
       return redirect("practice", practice_id=practice_id)

   return render(
       request,
       "student/reading_menu.html",
       {
           "path": "English / Reading",
           "title": "Reading",
           "course_id": course_id,
           "texts": list(settings.MDB_1.readings.find({"user_id": request.user.id}))[::-1]
       }
   )

@student_required
def student_query(request, course_id): 
  """
  Django view for handling student reading query creation and submission.
  Processes student queries and initiates reading practice sessions.

  Args:
      request (HttpRequest): Django request object containing:
          - session data
          - POST data (optional): For submitting queries
      course_id (int): Course identifier

  Returns:
      HttpResponse: One of:
      - Redirect to:
          * practice view with new practice_id when query submitted
      - Renders "student/home.html" with context:
          * path: Navigation breadcrumb
          * title: Page title
          * course_id: Course identifier

  Session Data Set:
      - course_id: Current course identifier
      - text: Generated reading content
      - questions: Question status
      - review: Review mode status

  Notes:
      - Requires student authorization (@student_required)
      - Publishes user activity data when query is written
      - Generates unique practice_id for new sessions
  """ 
  request.session['course_id'] = course_id
  if request.method == "GET": 
    Publisher("The user is writing his query", {"time": datetime.now(), "action": "query", "user_id" :request.user.id, "name": request.user.name, "course_id": course_id}).publish()
  if request.method == "POST":
    practice_id = uuid.uuid4()
    request.session["text"] = CreateReading(request, practice_id, course_id).gpt_query()
    request.session["questions"] = None
    request.session["review"] = False
    return redirect("practice", practice_id=practice_id)
  return render(request, "student/home.html", {"path": "Dashboard / Create Reading", "title": "Create Reading", "course_id": course_id},)

@student_required
def practice(request, practice_id):
  """
  Django view for managing reading practice sessions and interactions.
  Handles reading display, highlighting, note-taking, and question generation.

  Args:
      request (HttpRequest): Django request object containing:
          - session data
          - POST data (optional):
              * feedback: User feedback on reading
              * submit_notes: Notes and highlights submission
              * teacher_question: Questions for teacher
      practice_id (str): Unique identifier for practice session

  Returns:
      HttpResponse: One of:
      - Redirect to:
          * questions view when ready for assessment
          * practice view after feedback submission
      - Renders "student/practice.html" with context:
          * User info (name, occupation)
          * Reading content and metadata
          * Highlighting and notes data
          * Session status information

  Session Data Set:
      - practice_id: Current practice identifier
      - quiz: Generated questions
      - text: Reading content and metadata
      - notes: User notes
      - questions: Question availability status
      - review: Review mode status

  Notes:
      - Requires student authorization (@student_required)
      - Handles highlight processing via external task service
      - Supports question generation through task queue
      - Publishes user activity data for analytics
      - Manages both new practice and review sessions
  """
  if request.method == "GET": 
    if not request.session.get("review"):
      Publisher("The user is reading", {"time": datetime.now(), "action": "reading", "user_id" :request.user.id, "name": request.user.name, "course_id": request.session.get('course_id')}).publish()
  if str(practice_id) == "b1c3b7d8-4648-4969-8604-a6161e13f5aa":
    request.session["questions"] = True
    doc = settings.MDB_1.readings.find_one({"practice_id": str(practice_id)})
    quiz = settings.MDB_1.questions.find_one({"practice_id": str(practice_id)}, {"_id": 0})
    request.session["quiz"] = quiz['quiz']
    request.session["practice_id"] = str(practice_id)
    request.session["text"] = (doc["title"], doc["text"], doc["query"], doc.get('yellow_highlights', None), doc.get('pink_highlights', None), doc.get('notes', None))
    text = request.session.get("text")
    reading_title = text[0]
    story = request.session.get("text")[1]
    story_paragraphs = story.split("\n\n")
    request.session["review"] = False
  else:
    text = request.session.get("text")
    reading_title = text[0]
    story = request.session.get("text")[1]
    story_paragraphs = story.split("\n\n")

  if not request.session.get("questions"):
    question_topics = ["visualize", "summarize", "prior knowledge", "self monitor"]
    question_strategy = ["genre", "location details", "sequence", "main idea", "cause effect"]
    payload = {
      'story' : story,
      'PROD': settings.PROD,
      'question_topics': question_topics, 
      'question_strategy': question_strategy,
      'original_query': request.session.get("text")[2], 
      'practice_id': str(practice_id)
    }
    # Use local API endpoint instead of cloud function
    def async_generate_questions():
      try:
        requests.post(f"{settings.URL}/api/generate-questions/", json=payload, timeout=300)
      except Exception as e:
        print(f"Error generating questions: {e}")
    threading.Thread(target=async_generate_questions).start()
    request.session["questions"] = True
  if request.method == "POST":
    form = request.POST
    if "feedback" in form:
      item = Feedback(user=request.user, user_occupation=request.user.occupation, positive=form.get('feedback')=='positive', document_reference=practice_id, item_num=None, item_type="reading")
      item.save()
      return redirect("practice", practice_id=practice_id)
    if not request.session.get("review"):
      if "submit_notes" in form:
        request.session['practice_id'] = str(practice_id)
        form_hl = form.get("yellowHighlights", None)
        form_hl2 = form.get("pinkHighlights", None)
        yellow_highlights = json.loads(form_hl) if form_hl else []
        pink_highlights = json.loads(form_hl2)if form_hl2 else []
        highlighted_text = [x['text'] for x in yellow_highlights]
        unknown_words = [x['text'] for x in pink_highlights]
        notes = form.get("notes")
        settings.MDB_1.readings.update_one({"practice_id": str(practice_id)}, {"$set": {"yellow_highlights": yellow_highlights, "pink_highlights": pink_highlights, "notes": notes}})
        if len(unknown_words) > 0 or len(highlighted_text) > 0:
          payload = { 
            "highlighted_text": highlighted_text, 
            "unknown_words": unknown_words, 
            "PROD": settings.PROD,
            "user_id": request.user.id
          }
          # Use local API endpoint instead of cloud function
          def async_process_highlights():
            try:
              requests.post(f"{settings.URL}/api/process-highlights/", json=payload, timeout=300)
            except Exception as e:
              print(f"Error processing highlights: {e}")
          threading.Thread(target=async_process_highlights).start()

        request.session["notes"] = notes
      elif "teacher_question" in form:
        question = form.get("question")
        StudentTeacherQuestion(course=Course.objects.get(id=request.session["course_id"]),question=question,student=request.user,).save()
        Publisher(f"The user has this question: {question}", {"time": datetime.now(), "action": "help", "user_id" :request.user.id, "name": request.user.name, "course_id": request.session.get('course_id')}).publish()
        return redirect("practice", practice_id=practice_id)
    else:
      request.session['notes'] = text[5]
    quiz = None
    while not quiz:
      quiz = settings.MDB_1.questions.find_one({"practice_id": str(practice_id)}, {"_id": 0})
      time.sleep(5) 
    request.session["quiz"] = quiz['quiz']
    request.session["practice_id"] = str(practice_id)
    return redirect("questions", question_num=1)
  return render(
    request,
    "student/practice.html",
    {
      "name": request.user.name,
      "occupation": request.user.occupation,
      "title": reading_title,
      "text": story_paragraphs,
      "pink_highlights": base64.b64encode(json.dumps(text[4]).encode('utf-8')).decode('utf-8'), 
      "yellow_highlights": base64.b64encode(json.dumps(text[3]).encode('utf-8')).decode('utf-8'),
      "notes": text[5],
      "questions": request.session.get("questions", False),
      "path": f"English / Reading / {reading_title}",
      "review": request.session.get("review"),
      "course_id": request.session.get("course_id")
    },
  )
#TODO make sure that questions are loaded in tour mode...
#TODO make sure to update database variable tour whenever the user finishes or clicks do tour later...

@student_required
def student_questions(request, question_num):
  """
  Django view for managing student question responses and quiz submissions.
  Handles question display, answer submission, and grading process.

  Args:
      request (HttpRequest): Django request object containing:
          - session data
          - POST data (optional):
              * submit_quiz: Quiz submission
              * feedback: Question feedback
              * change_question: Navigation between questions
      question_num (int): Current question number

  Returns:
      HttpResponse: One of:
      - Redirect to:
          * student_home after quiz completion
          * next question when navigating
      - Renders "student/questions.html" with context:
          * Question content and metadata
          * Reading content
          * User progress and answers
          * Review information if applicable

  Session Data Set:
      - quiz: Question set and answers
      - text: Reading content
      - practice_id: Practice session identifier
      - review: Review mode status

  Notes:
      - Requires student authorization (@student_required)
      - Publishes user activity data during question attempts
      - Handles diagnostic test progression
      - Processes grading through external task service
      - Supports both testing and review modes
  """
  if request.method == "GET": 
    if not request.session.get("review"):
      Publisher("The user is doing questions", {"time": datetime.now(), "action": "questions", "question_number":question_num, "user_id" :request.user.id, "name": request.user.name, "course_id": request.session.get('course_id')}).publish()
  quiz = request.session.get("quiz")
  reading_title = request.session.get("text")[0]
  text = request.session.get("text")[1].split("\n\n")
  speech = False
  if request.method == "POST":
    if "submit_quiz" in request.POST:
      if not request.session.get("review"):
        Publisher("The user has finished", {"time": datetime.now(), "action": "finished", "user_id" :request.user.id, "name": request.user.name, "course_id": request.session.get('course_id')}).publish()
        settings.MDB_1.readings.update_one({"practice_id": request.session['practice_id']}, {"$set": {"notes": request.POST.get("notes")}})
        payload = { 
          "course_id": request.session.get("course_id"), 
          "answers": dict(request.POST),
          "practice_id": request.session['practice_id'], 
          "PROD": settings.PROD,
          "user_id": request.user.id}
        # Use local API endpoint instead of cloud function
        def async_grade_quiz():
          try:
            requests.post(f"{settings.URL}/api/grade-quiz-reading/", json=payload, timeout=300)
          except Exception as e:
            print(f"Error grading quiz: {e}")
        threading.Thread(target=async_grade_quiz).start()
        messages.success(request, "You have successfully submitted your quiz")
      if not request.user.diagnostic and not request.user.admin: 
        quiz = None
        # TODO make sure that this does not crash...
        while True:
          quiz = settings.MDB_1.questions.find_one({"practice_id": str(request.session.get("practice_id"))}, {"_id": 0})
          if quiz and 'graded' in quiz:
            break
          time.sleep(5)
        score = quiz['mpc_grade']
        finish = LexileAlgorithm(request, score).BinarySearch()

        if finish:
          messages.success(request, "You have finished the diagnostic test")
          user_obj = request.user
          user_obj.diagnostic = True
          user_obj.save()
          return redirect("student_home")
        else: 
          messages.info(request, "Please continue with the next reading of your diagnostic!")
          return redirect("query", course_id=request.session.get("course_id"))
      return redirect("student_home")
    elif "feedback" in request.POST:
      item = Feedback(user=request.user, user_occupation=request.user.occupation, positive=request.POST.get('feedback')=='positive', document_reference=request.session.get('practice_id'), item_num=question_num, item_type="question")
      item.save()
      return redirect("questions", question_num=question_num)
    elif "change_question" in request.POST:
      return redirect(request, "questions", question_num=request.POST["change_question"])
  current_question = next((q for q in quiz["questions"] if q["question_num"] == question_num), None)
  story = request.session.get("text")[1]
  story_paragraphs = story.split("\n\n")

  context = {
    "pink_highlights": request.session.get("pink_highlights"),
    "yellow_highlights": request.session.get("yellow_highlights"),
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
    "course_id": request.session.get("course_id")

  }
  if request.session.get("review"): 
    context = {
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
  }
  return render(request, "student/questions.html", context)

@student_required
def writing_menu(request, course_id):
  """
  Django view for managing student writing activities and assignments.
  Handles writing prompt selection and access to previous writings.

  Args:
      request (HttpRequest): Django request object containing:
          - session data
          - POST data (optional):
              * writing_id: Existing writing identifier
              * course_prompts: Selected writing prompt
              * add_prompt: New prompt creation
      course_id (int): Course identifier

  Returns:
      HttpResponse: One of:
      - Redirect to:
          * writing view with selected or new writing ID
      - Renders "student/writingarchive.html" with context:
          * Previous writings list
          * Course information
          * Navigation data

  Session Data Set:
      - prompt: Selected writing prompt
      - write_id: Writing identifier

  Notes:
      - Requires student authorization (@student_required)
      - Retrieves writings from MongoDB database
      - Formats timestamps to user's timezone
      - Manages both new and existing writing sessions
      - Supports course-specific writing prompts
  """
  new_text = str(uuid.uuid4())
  if request.method == "POST":
    if "writing_id" in request.POST:
      request.session["prompt"] = None
      request.session["write_id"] = request.POST["writing_id"]
      return redirect("writing", qid=request.POST["writing_id"])
    elif "course_prompts" in request.POST:       
      request.session["prompt"] = request.POST["course_prompts"]
      return redirect("writing", qid=new_text)
    elif "add_prompt" in request.POST: 
      prompt_name = request.POST['prompt_name']
      prompt = request.POST["prompt"]
      write_prompt = WritingPrompts(name=prompt_name, prompt=prompt)
      write_prompt.save()
      course_obj = Course.objects.get(id=course_id).writing_prompts.add(write_prompt)
      return redirect("writing_menu", course_id=course_id)

  texts = list(
    settings.MDB.writing.find({"user_id": request.user.id}).sort("updated_at", DESCENDING))
  for x in texts:
    x["id"] = x["_id"]
    utc_time = datetime.fromisoformat(x["updated_at"].replace('Z', '+00:00'))
    utc_time = utc_time.replace(tzinfo=timezone.utc)
    user_time = utc_time.astimezone(timezone.get_current_timezone())
    x["updated_at"] = user_time.strftime('%B %d, %Y at %I:%M %p %Z')

  path_str = "English / Writing"
  title_str = "Writing"
  return render(
    request,
    "student/writingarchive.html",
    {
      "texts": texts,
      "path": path_str,
      "title": title_str,
      "courses": Course.objects.filter(students=request.user),
      "course_id": course_id
    },
  )

@student_required
def writing(request, qid):
  """
  Django view for handling individual writing sessions.
  Manages writing interface and content creation.

  Args:
      request (HttpRequest): Django request object containing:
          - session data
      qid (str): Unique identifier for writing session

  Returns:
      HttpResponse: Renders "student/writing.html" with context:
          * User identifier
          * Session identifier
          * API endpoints
          * Writing prompt
          * Navigation data

  Session Data Set:
      - qid: Writing session identifier
      - user_id: Current user identifier
      - prompt: Writing prompt

  Notes:
      - Requires student authorization (@student_required)
      - Integrates with external data and websocket services
      - Handles both new and existing writing sessions
  """
  request.session["qid"] = str(qid)
  request.session["user_id"] = request.user.id
  prompt = request.session.get("prompt")
  if request.session.get("prompt") is None:
    try:
      chat = settings.MDB.chat.find_one({"wid": str(qid)})
      prompt = chat["prompt"]
    except Exception:
      prompt = "default"
  return render(
    request,
    "student/writing.html",
    {
      "user_id": request.user.id,
      "qid": qid,
      "data_url": settings.URL,
      "ws_url": settings.WS_URL,
      "path": "Dashboard / English / New Document",
      "prompt": prompt,
    },
  )


@student_required
def flashcards_dash(request, course_id):
  """
  Django view for managing flashcard sets and their organization.
  Handles creation of new flashcard sets and access to existing ones.

  Args:
      request (HttpRequest): Django request object containing:
          - session data
          - POST data (optional):
              * create_new: Trigger for new flashcard set
              * flash_id: Existing flashcard set identifier
      course_id (int): Course identifier

  Returns:
      HttpResponse: One of:
      - Redirect to:
          * flashcards view with selected flashcard_id
      - Renders "student/flashcards_dash.html" with context:
          * Existing flashcard sets
          * Navigation data
          * Course identifier

  Notes:
      - Requires student authorization (@student_required)
      - Stores flashcard data in MongoDB database
      - Formats timestamps to user's timezone
      - Orders flashcard sets by last viewed date
  """
  if request.method == "POST":
    if "create_new" in request.POST:
      cards = create_flashcards()  
      new_flashcard = str(uuid.uuid4())
      settings.MDB.flashcards.insert_one(
        {
          "qid": new_flashcard,
          "user_id": request.user.id,
          "cards": cards["cards"],
          "title": cards["title"],
          "topic": cards["topic"],
          "created_at": datetime.now().isoformat(),
          "last_viewed": datetime.now().isoformat(),
        }
      )

      return redirect("flashcards", flashcard_id=new_flashcard)
    elif "flash_id" in request.POST:
      return redirect("flashcards", flashcard_id=request.POST["flash_id"])
  flashcards = list(settings.MDB.flashcards.find({"user_id": request.user.id}).sort(
    [("last_viewed", DESCENDING)])
  )
  for x in flashcards:
    x["id"] = x["_id"]
    utc_time = datetime.fromisoformat(x["last_viewed"].replace('Z', '+00:00'))
    utc_time = utc_time.replace(tzinfo=timezone.utc)
    user_time = utc_time.astimezone(timezone.get_current_timezone())
    x["last_viewed"] = user_time.strftime('%B %d, %Y at %I:%M %p %Z')
    utc_time = datetime.fromisoformat(x["created_at"].replace('Z', '+00:00'))
    utc_time = utc_time.replace(tzinfo=timezone.utc)
    user_time = utc_time.astimezone(timezone.get_current_timezone())
    x["created_at"] = user_time.strftime('%B %d, %Y at %I:%M %p %Z')
  return render(
    request,
    "student/flashcards_dash.html",
    {"db_cards": flashcards, "path": "English / Flashcards", "title": "Flashcards", "course_id": course_id},
  )

@student_required
def flashcards(request, flashcard_id):
  """
  Django view for displaying and interacting with specific flashcard sets.
  Manages individual flashcard study sessions.

  Args:
      request (HttpRequest): Django request object containing:
          - session data
      flashcard_id (str): Unique identifier for flashcard set

  Returns:
      HttpResponse: Renders "student/flashcards.html" with context:
          * Flashcard set identifier
          * User identifier
          * API endpoint
          * Course identifier

  Notes:
      - Requires student authorization (@student_required)
      - Retrieves flashcard content from session data
      - Supports interactive flashcard review
  """
  return render(
    request,
    "student/flashcards.html",
    {"qid": flashcard_id, "user_id": request.user.id, "data_url": settings.URL, "course_id": request.session.get("course_id")})

# misc views (not features)
@login_required
def edit_profile(request):
  """
  Django view for handling user profile modifications.
  Manages user preferences and settings updates.

  Args:
      request (HttpRequest): Django request object containing:
          - POST data (optional):
              * color: User interface color preference
              * timezone: User's preferred timezone

  Returns:
      HttpResponse: One of:
      - Redirect to:
          * student_home for students
          * dashboard for other users
      - Renders "student/edit_profile.html" with context:
          * Available timezones
          * Current settings
          * Navigation data

  Notes:
      - Requires login authentication (@login_required)
      - Updates CustomUser model with new preferences
      - Supports different redirects based on user occupation
  """
  if request.method == "POST":
    color = request.POST['color']
    user = CustomUser.objects.get(id=request.user.id)
    user.color = color
    user.timezone = request.POST['timezone']
    user.save()

    if request.user.occupation == "student":
      return redirect("student_home")
    else: 
      return redirect("dashboard")
  return render(request, "student/edit_profile.html", {"path": "Edit Profile", "title": "Edit Profile", 'timezones': pytz.common_timezones, "current_timezone": request.user.timezone})

@csrf_exempt
def get_suggestions(request):
   """
   Get topic suggestions using the Groq API based on a query string.
   
   Sends a query to Groq's LLM API to generate related topics and returns them
   as a JSON response. Uses llama3-8b-8192 model for suggestions.

   Args:
       request (HttpRequest): Django request object containing:
           - query: Search term in GET parameters for topic suggestions

   Returns:
       JsonResponse: JSON response with one of:
           - {'suggestions': list} - List of suggested topics on success
           - {'error': str} - Error message if request fails, with appropriate status code:
               * 400 - Missing query parameter
               * 405 - Invalid request method
               * 500 - API or parsing errors

   Raises:
       Groq.ApiError: When Groq API call fails
       json.JSONDecodeError: When API response cannot be parsed
       Exception: For unexpected errors

   Notes:
       - Requires GROQ_API_KEY environment variable
       - CSRF exempt to allow external requests
       - Returns only topics, no explanations
   """
   if request.method == "GET":
       try:
           query = request.GET.get("query")
           if not query:
               return JsonResponse({'error': 'Query parameter is missing'}, status=400)

           client = Groq(
               api_key=os.environ.get("GROQ_API_KEY"),
           )

           chat_completion = client.chat.completions.create(
               messages=[
                   {
                       "role": "user",
                       "content": f"Return a JSON that includes a concise list of topics related to {query}. Only return the topics, no explanations nor anything else. {{ \"topics\": []}}",
                   }
               ],
               model="llama3-8b-8192",
           )

           suggestions = chat_completion.choices[0].message.content
           try:
               suggestions_dict = json.loads(suggestions)
               suggestions = suggestions_dict.get("topics", [])
           except json.JSONDecodeError:
               return JsonResponse({'error': 'Failed to parse API response'}, status=500)

           if not isinstance(suggestions, list):
               return JsonResponse({'error': 'Unexpected response format from API'}, status=500)

           return JsonResponse({'suggestions': suggestions})
           
       except Groq.ApiError as e:
           return JsonResponse({'error': f'Groq API error: {str(e)}'}, status=500)
       except Exception as e:
           return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)

   return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_protect
def left_page(request):
  if request.method == 'POST':
    try:
      data = json.loads(request.body)
      action = data.get('action')
      timestamp = data.get('timestamp')
      duration = data.get('duration')
      if not request.session.get('review'):
        if action == "tab_left":
          Publisher("The user has left the tab for more than 5 seconds", {"time": datetime.now(), "action": "left_tab", "user_id" :request.user.id, "name": request.user.name, "course_id": request.session.get('course_id')}).publish()

        elif action == "tab_returned": 
          Publisher("The user has returned to the tab", {"time": datetime.now(), "action": "returned_tab", "user_id" :request.user.id, "name": request.user.name, "course_id": request.session.get('course_id')}).publish()
      return HttpResponse("Data received successfully")
    except json.JSONDecodeError:
      return HttpResponse("Invalid JSON data", status=400)
  else:
    return HttpResponse("This endpoint only accepts POST requests", status=405)

@student_required
def pronunciation_dash(request, course_id):
  """
  Django view for managing pronunciation practice sessions.
  Handles creation and access to pronunciation exercises.

  Args:
      request (HttpRequest): Django request object containing:
          - POST data (optional):
              * create_new: Generate new sentence set
              * new_running_record: Generate new text
              * practice_id: Access existing practice
      course_id (int): Course identifier

  Returns:
      HttpResponse: One of:
      - Redirect to:
          * pronunciation view for sentence practice
          * running_record view for text practice
      - Renders "student/pronunciation_home.html" with context:
          * Previous sessions
          * Navigation data
          * Course information

  Session Data Set:
      - sentences: Generated sentence set
      - text: Generated reading text
      - practice_id: Practice identifier
      - review: Review mode status

  Notes:
      - Requires student authorization (@student_required)
      - Uses Groq API for content generation
      - Stores practice data in MongoDB
      - Handles both sentence and text-based practice
  """ 
  if request.method == "POST":
    if "create_new" in request.POST:
      while True:
        try:
          json_string = "Please give me a JSON with sentences for english learners from 8th to 12th grade. Please make sure that the sentences does not contain single nor double quotes. Please return 10 sentences, no more, no less... ONLY RETURN THE JSON, no text before nor after itUse the following format: {\"title\":\"title\", \"questions\": [{\"sentence\": \"I am a student\"}, {\"sentence\": \"The sixth sick sheik's sixth sheep's sick\"}]}"
          client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
          )
          chat_completion = client.chat.completions.create(
            messages=[
              {
                "role": "user",
                "content": json_string,
              }
            ],
            model="llama3-70b-8192",)
          sentences_file = json.loads(chat_completion.choices[0].message.content)
          assert "questions" in sentences_file
          assert "title" in sentences_file
          assert len(sentences_file["questions"]) == 10
          for sentence in sentences_file["questions"]:
            assert "sentence" in sentence
          request.session["sentences"] = sentences_file
          practice_id = str(uuid.uuid4())
          request.session['practice_id'] = practice_id
          request.session["review"] = False
          settings.MDB_1.pronunciation.insert_one({"user_id": request.user.id, "title": sentences_file["title"],"questions": sentences_file["questions"], "practice_id": practice_id, "created_at": timezone.now(), "last_viewed": timezone.now(), "reviewed": True})
          return redirect("pronunciation", course_id=course_id, question_id=1)
        except Exception as e: 
          print(e)
    elif "new_running_record" in request.POST:
      practice_id = str(uuid.uuid4())
      while True:
        try:
          json_string = "Please give me a JSON with a 500 word text for english learners from 8th to 12th grade. A few of few of these sentences are supposed to be hard to pronounce. ONLY RETURN THE JSON, no text before nor after it. Use the following format: {\"text\": \"Here is the short text...\", \"title\": \"The title of the text\"}"
          client = Groq(api_key=os.environ.get("GROQ_API_KEY"),)
          chat_completion = client.chat.completions.create(
            messages=[
              {
                "role": "user",
                "content": json_string,
              }
            ],
            model="llama3-70b-8192",)
          text_file = json.loads(chat_completion.choices[0].message.content)
          assert "text" in text_file
          assert "title" in text_file
          assert type(text_file["text"]) == str
          request.session["text"] = text_file["text"]
          practice_id = str(uuid.uuid4())
          request.session["review"] = False
          request.session['practice_id'] = practice_id
          settings.MDB_1.pronunciation.insert_one({"user_id": request.user.id, "title":text_file['title'],"text": text_file["text"], "practice_id": practice_id, "created_at": timezone.now(), "last_viewed": timezone.now()})
          return redirect("running_record", course_id=course_id, practice_id=practice_id)
        except Exception as e: 
          print(e)
    elif "practice_id" in request.POST: 
      practice_id = request.POST["practice_id"]
      doc = settings.MDB_1.pronunciation.find_one_and_update({"practice_id": practice_id},{"$set": {"last_viewed": timezone.now()}},return_document=ReturnDocument.AFTER, projection={"_id": 0, "created_at": 0, "last_viewed": 0})
      request.session['practice_id'] = practice_id
      request.session["review"] = True
      if doc.get('text'):
        request.session["text"] = doc['text']
        return redirect("running_record", course_id=course_id, practice_id=practice_id)
      else:
        request.session["sentences"]= doc
        return redirect("pronunciation", course_id=course_id, question_id=1)   




  sessions = list(settings.MDB_1.pronunciation.find({"user_id": request.user.id}).sort({"last_viewed": DESCENDING}))     
  return render(request, "student/pronunciation_home.html", {"path": "English / Pronunciation", "title": "Pronunciation", "course_id": course_id, "go_back_url": "/student/", "sessions": sessions})



@student_required 
def pronunciation(request, course_id, question_id):
  """
  Django view for individual pronunciation practice sessions.
  Manages sentence-level pronunciation exercises.

  Args:
      request (HttpRequest): Django request object containing:
          - session data
      course_id (int): Course identifier
      question_id (int): Current question number

  Returns:
      HttpResponse: Renders "student/pronunciation.html" with context:
          * Current sentence
          * Question metadata
          * Session information
          * Navigation data
          * Audio URL if available

  Session Data Set:
      - sentences: Complete set of practice sentences
      - practice_id: Practice identifier
      - review: Review mode status

  Notes:
      - Requires student authorization (@student_required)
      - Retrieves sentences from session data
      - Supports both practice and review modes
  """
  sentences = request.session["sentences"]["questions"]
  doc = sentences[question_id -1 ]
  sentence = doc["sentence"]
  return render(request, "student/pronunciation.html", {"path": "English / Pronunciation", "title": "Pronunciation", "course_id": course_id, "sentence": sentence, "question_id": question_id, "go_back_url": "/student/", 
                                                        "practice_id": request.session["practice_id"], "review": request.session.get("review"), "doc": doc, "audio_url": doc.get("audio_url")})

@student_required
def running_record(request, course_id, practice_id):
  """
  Django view for managing running record reading sessions.
  Handles continuous text reading practice and recording.

  Args:
      request (HttpRequest): Django request object containing:
          - session data
      course_id (int): Course identifier
      practice_id (str): Unique identifier for practice session

  Returns:
      HttpResponse: Renders "student/running_record.html" with context:
          * Reading text (full and paragraphs)
          * Session information
          * Results data in review mode
          * Navigation elements
          * Audio URL if available

  Session Data Set:
      - text: Reading content
      - review: Review mode status

  Notes:
      - Requires student authorization (@student_required)
      - Splits text into paragraphs for display
      - Handles both practice and review modes
      - Includes audio playback in review mode
  """
  text = request.session.get("text") 
  doc = settings.MDB_1.pronunciation.find_one({"practice_id": str(practice_id)})
  paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
  review = request.session.get("review")
  if review: 
    context = {"path": "English / Pronunciation / Running Record", "title": "Running Record", "course_id": course_id, "practice_id": practice_id, "go_back_url": "/student/", "text": paragraphs, "full_text": text, "review" : request.session.get("review"), "doc": doc['result'],"sentences": json.dumps(doc["result"]["result"]["sentences"]), "audio_url": doc["audio_url"],}
  else: 
    context = {"path": "English / Pronunciation / Running Record", "title": "Running Record", "course_id": course_id, "practice_id": practice_id, "go_back_url": "/student/", "text": paragraphs, "full_text": text, "review" : request.session.get("review")}
  return render(request, "student/running_record.html", context)


def test_reading(request): 
  return render(request, "student/new_reading.html")

def learning_path(request): 
  return render(request, "student/learning_path.html")

def courses(request): 
  """
  Django view for displaying user's course information and learning streak.
  Manages course listing and streak tracking.

  Args:
      request (HttpRequest): Django request object containing:
          - user information

  Returns:
      HttpResponse: Renders "student/courses.html" with context:
          * List of enrolled courses
          * Current learning streak
          * Streak statistics

  Notes:
      - Updates and tracks learning streaks
      - Retrieves course enrollment data
      - Supports streak maintenance and tracking
  """
  streak, created = LearningStreak.objects.get_or_create(user=request.user)
  streak.update_streak()
  learning_streak = streak.current_streak
  courses = list(Course.objects.filter(students=request.user))
  return render(request, "student/courses.html", {"streak": learning_streak,"courses": courses, "learning_streak": learning_streak})

@student_required
def bigger_picture(request, course_id):
  """
  Django view for displaying course overview and progress visualization.
  Provides broader context of student's learning journey.

  Args:
      request (HttpRequest): Django request object
      course_id (int): Course identifier

  Returns:
      HttpResponse: Renders "student/bigger_picture.html" with context:
          * Course identifier

  Notes:
      - Requires student authorization (@student_required)
      - Displays course progress overview
  """
  return render(request, "student/bigger_picture.html", {"course_id": course_id})

@student_required
def grades(request):
  """
  Django view for displaying student grade information.
  Manages grade reporting and academic progress tracking.

  Args:
      request (HttpRequest): Django request object

  Returns:
      HttpResponse: Renders "student/grades.html" with empty context

  Notes:
      - Requires student authorization (@student_required)
      - Displays academic performance data
  """
  return render(request, 'student/grades.html', {})