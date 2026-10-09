import json
import time
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from pages.models import Course, Reviews, CustomUser
from api.utils import save_editor_content
from api.tasks import CACHE_TIMEOUT
from rest_framework import status
from django.core.files.base import ContentFile
import time
from datetime import timedelta
import hashlib
import os
from urllib.parse import urlparse
import logging
import requests
import io
import json
import uuid
from django.utils.text import get_valid_filename
from google.cloud import texttospeech
from google.cloud import storage
import fsrs
from django.db import transaction
import math
from django.utils import timezone
logger = logging.getLogger(__name__)

@api_view(["GET"])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def hello_world(request):
  """
  Retrieves editor content for a specific user and question from cache or MongoDB.

  First checks the Redis cache for recently edited content. If not found,
  falls back to checking MongoDB for saved content. Used to initialize 
  the editor when a user opens a writing assignment.

  Args:
    request (HttpRequest): Django request object containing:
      - qid (str): Question/assignment identifier
      - userId (str): User's ID
      - HTTP_ORIGIN (str): Request origin header

  Returns:
    Response: JSON containing:
      - initialContent (list): Editor content blocks
      - Empty list if no content is found

  Notes:
    - Uses cache key format: editor_content_{user_id}_{qid}
    - Prioritizes cached content for real-time collaboration
    - Falls back to MongoDB for persistent storage
    - Returns empty list for new assignments
  """
  origin = request.META.get("HTTP_ORIGIN")
  qid = request.GET.get("qid")
  user_id = request.GET.get("userId")
  cache_key = f"editor_content_{user_id}_{qid}"

  # Check cache first (EC: In the scenario of different browser windows)
  content = cache.get(cache_key)
  if content:
    print(f"Cache hit for key: {cache_key}")
    return Response({"initialContent": content["blocks"]})

  # Fallback to MongoDB
  print(f"Cache miss for key: {cache_key}. Fetching from MongoDB.")
  initial_content = settings.MDB.writing.find_one(
    {"_id": qid, "user_id": int(user_id)}
  )
  print(initial_content)
  if initial_content is None:
    return Response({"intialContent": []})
  else:
    return Response({"initialContent": initial_content["content"]["blocks"]})

@api_view(["POST"])
def update_editor(request):
  """
  Updates cached editor content for real-time collaboration.

  Stores the current editor state in cache with a timestamp for syncing 
  between multiple users/windows. Used to maintain real-time updates 
  for collaborative editing.

  Args:
    request (HttpRequest): Django request object containing:
      - data (dict):
        - user_id (str): User's identifier 
        - qid (str): Question/assignment ID
        - content (dict): Current editor content blocks

  Returns:
    Response: JSON response containing:
      - status (str): "success" if update completed

  Notes:
    - Cache key format: editor_content_{user_id}_{qid}
    - Adds UTC timestamp to track last update
    - Cache timeout controlled by CACHE_TIMEOUT constant
    - Used by background task to check for updates
  """
  content = request.data
  user_id = content.get("user_id")
  qid = content.get("qid")
  cache_key = f"editor_content_{user_id}_{qid}"

  # Update the cache with the editor content and last update time for background task to check
  content['last_update'] = datetime.utcnow().isoformat() + "Z"
  cache.set(cache_key, content, timeout=CACHE_TIMEOUT)

  return Response({"status": "success"})

def parse_blocks(blocks):
  text_str = ""
  for block in blocks:
    if block['type'] == 'table':
      text_str += parse_table(block['content']['rows'])
    else:
      text_str += parse_regular_block(block['content'])
    text_str += "\n"  # Add a newline after each block
  return text_str.strip()

def parse_regular_block(content):
  return "".join(item['text'] for item in content if 'text' in item)

def parse_table(rows):
  table_str = ""
  for row in rows:
    cells = row['cells']
    row_content = []
    for cell in cells:
      cell_content = "".join(item['text'] for item in cell if 'text' in item)
      row_content.append(cell_content)
    table_str += " | ".join(row_content) + "\n"
  return table_str

@api_view(["GET"])
def send_chat_editor_content(request):
 """
 Retrieves and parses cached editor content for chat integration.

 Fetches the editor content from cache and converts it into plain text format,
 handling both regular text blocks and table structures. Used to share editor
 content with chat/AI features.

 Args:
   request (HttpRequest): Django request object containing:
     - user_id (str): User's identifier 
     - qid (str): Question/assignment ID

 Returns:
   Response: JSON containing one of:
     - success case:
       - content (str): Parsed text content from editor
     - error cases:
       - error (str): "Content not found" with 404 status
       - content (str): "An error occurred" for parsing failures

 Notes:
   - Cache key format: editor_content_{user_id}_{qid}
   - Uses parse_blocks() helper function for content conversion
   - Handles tables and regular text blocks differently
   - Returns 404 if content has expired from cache
 """
 user_id = int(request.GET.get("user_id"))
 qid = request.GET.get("qid")
 cache_key = f"editor_content_{user_id}_{qid}"
 
 content = cache.get(cache_key)
 if content is None:
   return Response({"error": "Content not found"}, status=404)
 
 try:
   text_str = ""
   blocks = content['blocks']
   text_str = parse_blocks(blocks)
 except Exception as e:
   return Response({"content": "An error occurred."})
 
 return Response({"content": text_str })


@csrf_exempt
def user_left(request):
 """
 Handles cleanup when a user leaves the editor.

 Saves the current editor state to persistent storage when a user exits
 the editor. Retrieves latest content from cache and saves it to MongoDB
 to prevent data loss.

 Args:
   request (HttpRequest): Django request object containing POST data:
     - user_id (str): User's identifier
     - qid (str): Question/assignment ID

 Returns:
   JsonResponse: One of:
     - For POST requests:
       - status: "success"
       - user_id: ID of user who left
     - For non-POST requests:
       - status: "success"

 Notes:
   - CSRF exempt to allow external requests
   - Cache key format: editor_content_{user_id}_{qid}
   - Uses save_editor_content() helper for MongoDB persistence
   - Preserves latest edits even if user leaves abruptly
 """
 if request.method == "POST":
   user_id = int(request.POST.get("user_id"))
   qid = request.POST.get("qid")
   cache_key = f"editor_content_{user_id}_{qid}"
   editor_content = cache.get(cache_key)

   save_editor_content(user_id, qid, editor_content)

   # Here you can add logic to handle when user leaves
   return JsonResponse({"status": "success", "user_id": user_id})
 return JsonResponse({"status": "success"})


@csrf_exempt 
def log_chat_session(request):
 """
 Logs chat session data to MongoDB and handles updates to existing sessions.

 Creates or updates chat session records with messages, prompts, and timestamps.
 Handles JSON validation and required fields checking. Used to persist chat
 interactions for later reference.

 Args:
   request (HttpRequest): POST request with JSON body containing:
     - qid (str): Unique ID for the chat session/writing ID
     - messages (list): List of chat messages 
     - prompt (str): Initial chat prompt (for new sessions)
     - user_id (str): User's identifier (for new sessions)

 Returns:
   JsonResponse: One of:
     - Success case: 
       - status: "success"
     - Error cases (with appropriate status codes):
       - 400: Invalid JSON or missing required fields
       - 405: Non-POST request method
       - 500: Unexpected server errors
     All error responses include:
       - status: "error"
       - message: Error description

 Notes:
   - CSRF exempt to allow external requests
   - Stores data in MongoDB chat collection
   - Updates timestamps on all modifications
   - Logs errors for debugging
   - Validates JSON structure and required fields
 """
 if request.method == "POST":
   try:
     data = json.loads(
       request.body.decode("utf-8")
     ) # Properly load JSON data from request body
     print("THE DATA IS", data) # Log data to see what's received
     
     existing_chat = settings.MDB.chat.find_one({"wid": data["qid"]})
     messages = data["messages"]
     print(type(messages))
     
     if existing_chat is not None:
       settings.MDB.chat.update_one(
         {"wid": data["qid"]},
         {
           "$set": {
             "messages": messages,
             "updated_at": datetime.now().isoformat(),
           }
         },
       )
       return JsonResponse({"status": "success"})
     else:
       settings.MDB.chat.insert_one(
         {
           "messages": messages,
           "prompt": data["prompt"],
           "wid": data["qid"],
           "user_id": data["user_id"],
           "created_at": datetime.now().isoformat(),
           "updated_at": datetime.now().isoformat(),
         }
       )
       print(data["prompt"])
       return JsonResponse({"status": "success"})
       
   except json.JSONDecodeError as e:
     print(f"JSON error: {e}") # Log JSON errors
     return JsonResponse(
       {"status": "error", "message": "Invalid JSON data"}, status=400
     )
   except KeyError as e:
     print(f"Missing key: {e}") # Log missing key errors
     return JsonResponse(
       {"status": "error", "message": f"Missing key: {e}"}, status=400
     )
   except Exception as e:
     print(f"Error: {e}") # Log any other errors
     return JsonResponse({" status": "error", "message": str(e)}, status=500)
 
 return JsonResponse(
   {"status": "error", "message": "Only POST method allowed"}, status=405
 )


@api_view(["GET"])
def get_chat_session(request):
 """
 Retrieves chat session messages for a specific writing/question ID.

 Fetches stored chat messages from MongoDB and handles different message
 formats (string or native). Returns empty list if no session exists.

 Args:
   request (HttpRequest): Django request object containing:
     - qid (str): Writing/question ID to retrieve chat for
     - HTTP_ORIGIN (str): Request origin header

 Returns:
   Response: JSON containing:
     - messages (list): Chat messages for the session
     - Empty list if no session found
     
 Notes:
   - Handles both string and native message formats
   - Parses string messages as JSON when needed
   - Logs origin for debugging purposes
 """
 origin = request.META.get("HTTP_ORIGIN")
 print(f"Request received from origin: This is the get_chat_session view{origin}")
 
 qid = request.GET.get("qid")
 chat_session = settings.MDB.chat.find_one({"wid": qid})

 if chat_session is None:
   return Response({"messages": []})

 if isinstance(chat_session["messages"], str):
   messages = json.loads(chat_session["messages"])
 else:
   messages = chat_session["messages"]

 return Response({"messages": messages})


@api_view(["GET"])
def flashcards(request):
 """
 Retrieves flashcards for a specific user and question ID.

 Gets stored flashcard data from MongoDB for a particular study session
 identified by qid and user_id.

 Args:
   request (HttpRequest): Django request object containing:
     - qid (str): Question/study session identifier
     - userId (str): User's identifier

 Returns:
   Response: JSON containing:
     - cards (list): List of flashcard objects for the session
 """
 qid = request.GET.get("qid")
 user_id = request.GET.get("userId")
 cards = settings.MDB.flashcards.find_one({"user_id": int(user_id), "qid": qid})
 return Response({"cards": cards["cards"]},)


@api_view(["POST"]) 
def save_flashcards(request):
 """
 Saves or updates flashcards for a study session.

 Stores flashcard data in MongoDB and updates metadata like last viewed time
 and number of cards. Used to persist changes to flashcard sets.

 Args:
   request (HttpRequest): Django request object containing:
     Query parameters:
       - qid (str): Question/study session identifier
       - userId (str): User's identifier
     Body data:
       - cards (list): List of flashcard objects to save

 Returns:
   Response: JSON containing:
     - status: "success" if save completed
 """
 qid = request.query_params.get("qid")
 user_id = request.query_params.get("userId")
 data = request.data
 cards = data.get("cards")
 
 settings.MDB.flashcards.update_one(
   {"qid": qid, "user_id": int(user_id)},
   {
     "$set": {
       "cards": cards,
       "last_viewed": datetime.now().isoformat(),
       "length": len(cards)
     }
   },
 )
 return Response({"status": "success"})


@api_view(["GET"])
def get_prompts(request):
 """
 Retrieves writing prompts for a specific course.

 Gets all writing prompts associated with a course identified by name
 and code. Course name is expected in format "name_code".

 Args:
   request (HttpRequest): Django request object containing:
     - course_name (str): Combined course name and code ("name_code")

 Returns:
   Response: One of:
     Success case:
       - prompts (list): List of prompt objects containing:
         - name (str): Prompt name
         - prompt (str): Prompt content
     Error cases:
       - 404: Course not found
       - 400: Course name not provided
 """
 course_name = request.GET.get("course_name").split("_")[0]
 course_code = request.GET.get("course_name").split("_")[1]
 
 if course_name:
   try:
     course = Course.objects.get(name=course_name, course_code=course_code)
     prompts = [
       {"name": x.name, "prompt": x.prompt}
       for x in course.writing_prompts.all()
     ]
     print(prompts)
     return Response({"prompts": prompts})
   except Course.DoesNotExist:
     return Response({"error": "Course not found"}, status=404)
 else:
   return Response({"error": "Course name not provided"}, status=400)

@csrf_exempt
@api_view(["POST"])
def upload_image(request):
  """
  Uploads an image file and saves it to the server.

  Parameters:
  - request: The HTTP request object containing the image file and other data.

  Returns:
  - A JSON response containing the URL of the uploaded file.

  """
  if request.method == 'POST':
    file = request.FILES['file']
    doc_id = request.POST.get('doc_id')
    user_id = request.POST.get('user_id')
    qid = request.POST.get('qid')
    if not doc_id:
      return Response({'error': 'Document ID not provided'}, status=400)
    file_path = f'uploads/{user_id}/{qid}/{doc_id}'
    default_storage.save(file_path, file)
    return Response({'file_url': default_storage.url(file_path)})
  return Response({'error': 'Invalid request'}, status=400)
  
def save_unique_file(file, folder='audio_recordings'):
  # Generate a unique filename
  original_name = get_valid_filename(file.name)
  name, ext = os.path.splitext(original_name)
  unique_filename = f"{name}_{uuid.uuid4().hex}{ext}"
  
  # Save the file with the unique name
  file_path = os.path.join(folder, unique_filename)
  file_name = default_storage.save(file_path, file)
  
  return file_name

@api_view(["POST"])
def record_audio(request):
 """
 Records and evaluates audio for pronunciation practice using SpeechSuper API.

 Handles audio file upload, validates WAV format, sends to SpeechSuper for 
 evaluation, and stores results. Supports both local and cloud storage paths.

 Args:
   request (HttpRequest): Django request object containing:
     Files:
       - audio_file (File): WAV audio file for evaluation
     Data:
       - sentence (str): Reference text to evaluate against
       - practice_id (str): Practice session identifier
       - question_num (int): Question number in session

 Returns:
   Response: One of:
     Success case (201):
       - status: "success"
       - message: Evaluation results from SpeechSuper
       - file_url: URL of stored audio file
     Error cases:
       - 400: Missing file, invalid format, or invalid WAV header
       - 500: Unexpected server errors

 Notes:
   - Requires WAV files with valid RIFF headers
   - Uses SpeechSuper sent.eval.promax API
   - Stores files differently in prod vs dev:
     * Prod: Google Cloud Storage
     * Dev: Local storage
   - Requires environment variables:
     * SPEECHSUPER_APP_KEY
     * SPEECHSUPER_SECRET_KEY
   - Updates MongoDB with evaluation results
 """
 if 'audio_file' not in request.FILES:
   return Response({"error": "No audio file provided"}, status=status.HTTP_400_BAD_REQUEST)
 
 audio_file = request.FILES['audio_file']
 if not audio_file.name.lower().endswith('.wav'):
   return Response({"error": "Invalid file type. Only WAV files are supported."}, status=status.HTTP_400_BAD_REQUEST)
 
 try:
   # Read the first 44 bytes (WAV header)
   header = audio_file.read(44)
   
   # Check RIFF header
   if header[:4] != b'RIFF':
     return Response({"error": "Invalid WAV file: RIFF header not found"}, status=status.HTTP_400_BAD_REQUEST)
   
   # Check WAVE format
   if header[8:12] != b'WAVE':
     return Response({"error": "Invalid WAV file: WAVE format not found"}, status=status.HTTP_400_BAD_REQUEST)

   audio_file.seek(0)
   file_name = save_unique_file(audio_file)
   file_url = default_storage.url(file_name)
   refText = request.data.get("sentence")
   practice_id = request.data.get("practice_id")
   question_num = int(request.data.get("question_num"))-1
   appKey = os.environ.get("SPEECHSUPER_APP_KEY")
   secretKey = os.environ.get("SPEECHSUPER_SECRET_KEY")

   baseURL = "https://api.speechsuper.com/"

   timestamp = str(int(time.time()))

   coreType = "sent.eval.promax"  # Change the coreType according to your needs.
   audioPath = os.path.join(settings.BASE_DIR, file_url.lstrip('/')) if not settings.PROD else file_url
   audioType = "wav" 
   audioSampleRate = 16000
   userId = "guest"

   url = baseURL + coreType
   connectStr = (appKey + timestamp + secretKey).encode("utf-8")
   connectSig = hashlib.sha1(connectStr).hexdigest()
   startStr = (appKey + timestamp + userId + secretKey).encode("utf-8")
   startSig = hashlib.sha1(startStr).hexdigest()

   params = {
     "connect": {
       "cmd": "connect",
       "param": {
         "sdk": {
           "version": 16777472,
           "source": 9,
           "protocol": 2
         },
         "app": {
           "applicationId": appKey,
           "sig": connectSig,
           "timestamp": timestamp
         }
       }
     },
     "start": {
       "cmd": "start",
       "param": {
         "app": {
           "userId": userId,
           "applicationId": appKey,
           "timestamp": timestamp,
           "sig": startSig
         },
         "audio": {
           "audioType": audioType,
           "channel": 1,
           "sampleBytes": 2,
           "sampleRate": audioSampleRate
         },
         "request": {
           "coreType": coreType,
           "refText": refText,
           "tokenId": "tokenId"
         }
       }
     }
   }

   datas = json.dumps(params)
   data = {'text': datas}
   headers = {"Request-Index": "0"}

   if settings.PROD:
     storage_client = storage.Client()
     bucket_name = "your-gcp-project-id-media"
     blob_name = file_url.split(f"{bucket_name}/")[1]
     
     bucket = storage_client.bucket(bucket_name)
     blob = bucket.blob(blob_name)
     file_obj = io.BytesIO()
     blob.download_to_file(file_obj)
     file_obj.seek(0)
     files = {"audio": (blob_name, file_obj)}
     res = requests.post(url, data=data, headers=headers, files=files)
     file_obj.close()
         
   else:
     files = {"audio": open(audioPath, "rb")}
     res = requests.post(url, data=data, headers=headers, files=files)

   message = res.text.encode('utf-8', 'ignore').decode('utf-8')
   message_json = json.loads(message)
   settings.MDB_1.pronunciation.update_one(
     {"practice_id": practice_id},
     {"$set": {
       f"questions.{question_num}.result": message_json,
       f"questions.{question_num}.audio_url": file_url
     }}
   )

   return Response({
     "status": "success",
     "message": message_json,
     "file_url": file_url
   }, status=status.HTTP_201_CREATED)
   
 except Exception as e:
   logger.error(f"Unexpected error: {str(e)}")
   return Response({
     "error": f"Unexpected error: {str(e)}"
   }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  
@api_view(["POST"])
def running_record(request):
 """
 Records and evaluates paragraph-level audio for pronunciation assessment.

 Similar to record_audio but uses SpeechSuper's para.eval endpoint for
 paragraph-level pronunciation evaluation. Handles file upload, validation,
 and API interaction.

 Args:
   request (HttpRequest): Django request object containing:
     Files:
       - audio_file (File): WAV audio file for evaluation
     Data:
       - full_text (str): Complete paragraph text to evaluate against
       - practice_id (str): Practice session identifier

 Returns:
   Response: One of:
     Success case (201):
       - status: "success" 
       - message: Full evaluation results from SpeechSuper
       - file_url: URL of stored audio file
     Error cases:
       - 400: Missing file, invalid format, or invalid WAV header
       - 500: Unexpected server errors

 Notes:
   - Requires WAV files with valid RIFF headers
   - Uses SpeechSuper para.eval API for paragraph analysis
   - Storage handling:
     * Prod: Google Cloud Storage
     * Dev: Local storage
   - Required environment variables:
     * SPEECHSUPER_APP_KEY
     * SPEECHSUPER_SECRET_KEY
   - Marks practice as reviewed on successful evaluation
 """
 if 'audio_file' not in request.FILES:
   return Response({"error": "No audio file provided"}, status=status.HTTP_400_BAD_REQUEST)

 audio_file = request.FILES['audio_file']
 if not audio_file.name.lower().endswith('.wav'):
   return Response({"error": "Invalid file type. Only WAV files are supported."}, status=status.HTTP_400_BAD_REQUEST)

 try:
   header = audio_file.read(44)
   if header[:4] != b'RIFF':
     return Response({"error": "Invalid WAV file: RIFF header not found"}, status=status.HTTP_400_BAD_REQUEST)
   if header[8:12] != b'WAVE':
     return Response({"error": "Invalid WAV file: WAVE format not found"}, status=status.HTTP_400_BAD_REQUEST)

   audio_file.seek(0)
   file_name = save_unique_file(audio_file)
   file_url = default_storage.url(file_name)
   refText = request.data.get("full_text")
   practice_id = request.data.get("practice_id")
   appKey = os.environ.get("SPEECHSUPER_APP_KEY")
   secretKey = os.environ.get("SPEECHSUPER_SECRET_KEY")

   baseURL = "https://api.speechsuper.com/"
   timestamp = str(int(time.time()))
   coreType = "para.eval"  # Change the coreType according to your needs.
   audioPath = os.path.join(settings.BASE_DIR, file_url.lstrip('/')) if not settings.PROD else file_url
   audioType = "wav"
   audioSampleRate = 16000
   userId = "guest"

   url = baseURL + coreType
   connectStr = (appKey + timestamp + secretKey).encode("utf-8")
   connectSig = hashlib.sha1(connectStr).hexdigest()
   startStr = (appKey + timestamp + userId + secretKey).encode("utf-8")
   startSig = hashlib.sha1(startStr).hexdigest()

   params = {
     "connect": {
       "cmd": "connect",
       "param": {
         "sdk": {
           "version": 16777472,
           "source": 9,
           "protocol": 2
         },
         "app": {
           "applicationId": appKey,
           "sig": connectSig,
           "timestamp": timestamp
         }
       }
     },
     "start": {
       "cmd": "start",
       "param": {
         "app": {
           "userId": userId,
           "applicationId": appKey,
           "timestamp": timestamp,
           "sig": startSig
         },
         "audio": {
           "audioType": audioType,
           "channel": 1,
           "sampleBytes": 2,
           "sampleRate": audioSampleRate
         },
         "request": {
           "coreType": coreType,
           "refText": refText,
           "tokenId": "tokenId",
         }
       }
     }
   }

   datas = json.dumps(params)
   data = {'text': datas}
   headers = {"Request-Index":"0"}

   if settings.PROD:
     storage_client = storage.Client()
     bucket_name = "your-gcp-project-id-media"
     blob_name = file_url.split(f"{bucket_name}/")[1]
     
     bucket = storage_client.bucket(bucket_name)
     blob = bucket.blob(blob_name)
     file_obj = io.BytesIO()
     blob.download_to_file(file_obj)
     file_obj.seek(0)
     files = {"audio": (blob_name, file_obj)}
     res = requests.post(url, data=data, headers=headers, files=files)
     file_obj.close()
   else:
     files = {"audio": open(audioPath, "rb")}
     res = requests.post(url, data=data, headers=headers, files=files)

   message = res.text.encode('utf-8', 'ignore').decode('utf-8')
   message_json = json.loads(message)
   print(message)
   
   settings.MDB_1.pronunciation.update_one(
     {"practice_id": practice_id},
     {"$set": {
       "result": message_json,
       "audio_url": file_url,
       "reviewed": True
     }}
   )

   return Response({
     "status": "success",
     "message": message_json,
     "file_url": file_url
   }, status=status.HTTP_201_CREATED)
   
 except Exception as e:
   logger.error(f"Unexpected error: {str(e)}")
   return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  
@api_view(["POST"])
def get_tts(request):
  """
Generates text-to-speech audio for flashcard content using Google Cloud TTS.

Converts flashcard front text to audio files, manages existing audio files,
and handles file storage. Uses Google Cloud Text-to-Speech for generation
with consistent voice settings.

Args:
  request (HttpRequest): Django request object containing:
    Data:
      - cards (list): List of flashcard objects with 'frontHTML' content
      - params (dict): Parameters including:
        - qid (str): Question/flashcard set identifier

Returns:
  Response: JSON containing:
    - status: "success"
    - file_paths (list): List of dictionaries mapping text to audio URLs
      Each item format: {text: url} or {text: None} if generation failed

Notes:
  - Uses Google Cloud Text-to-Speech with standard voice settings:
    * Language: en-US
    * Voice: en-US-Standard-C
    * Gender: Neutral
    * Format: MP3
  - File management:
    * Checks for existing audio files before generating new ones
    * Generates unique filenames with random components
    * Stores in 'tts_audio' directory
  - Database:
    * Updates MongoDB with file path mappings
    * Uses upsert to handle new flashcard sets
  - Error handling:
    * Returns None URL for failed generations
    * Preserves existing files when possible
"""
  cards = request.data.get("cards")
  params = request.data.get("params")
  qid = params.get("qid")
  client = texttospeech.TextToSpeechClient()
  file_paths = []

  # Fetch existing file paths from the database
  existing_flashcard = settings.MDB.flashcards.find_one({"qid": qid})
  existing_file_paths = {list(x.keys())[0]: list(x.values())[0] for x in existing_flashcard.get("file_paths", [])} if existing_flashcard else {}

  for index, card in enumerate(cards):
    text = card.get("frontHTML")
    
    if text in existing_file_paths:
      # File exists, generate a new URL
      existing_url = existing_file_paths[text]
      existing_path = urlparse(existing_url).path
      if default_storage.exists(existing_path[14:]):
        new_url = default_storage.url(existing_path[14:])
        file_paths.append({text: new_url})
      else:
        # If file doesn't exist, treat as a new file
        existing_file_paths.pop(text)
    
    if text not in existing_file_paths:
      # Generate new audio file
      synthesis_input = texttospeech.SynthesisInput(text=text)
      voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Standard-C",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
      )
      audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
      )
      
      try:
        response = client.synthesize_speech(
          input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        filename = f"tts_audio_{qid}_{index}_{os.urandom(8).hex()}.mp3"
        file_path = default_storage.save(
          os.path.join('tts_audio', filename),
          ContentFile(response.audio_content)
        )
        file_url = default_storage.url(file_path)
        file_paths.append({text: file_url})
        
        print(f'Audio content written to file "{file_path}"')
      except Exception as e:
        print(f"Error generating audio for text: {text}. Error: {str(e)}")
        file_paths.append({text: None})  # Add None for failed generations

  # Update database with new file paths
  settings.MDB.flashcards.update_one(
    {"qid": qid},
    {"$set": {"file_paths": file_paths}},
    upsert=True  # Create a new document if it doesn't exist
  )

  return Response({"status": "success", "file_paths": file_paths})

def get_rating(difficulty): 
  if difficulty == "easy":
    rating = fsrs.Rating.Easy
  elif difficulty == "good": 
    rating = fsrs.Rating.Good
  elif difficulty == "hard": 
    rating = fsrs.Rating.Hard
  elif difficulty == "again": 
    rating = fsrs.Rating.Again
  return rating

@api_view(["POST"])
@csrf_exempt
def card_response(request): 
  """
  Processes flashcard review responses using the FSRS (Free Spaced Repetition System) algorithm.

  Handles both new and existing flashcard reviews, calculates next review dates,
  and maintains review history. Uses the FSRS algorithm to optimize review scheduling
  based on user-reported difficulty.

  Args:
  request (HttpRequest): Django request object containing:
    - qid (str): Question/flashcard set identifier
    - currentCard (dict):
      - id (str): Identifier for the card being reviewed
    - difficulty (str): User-reported difficulty level, one of:
      * "easy"
      * "good"
      * "hard"
      * "again"

  Returns:
  Response: JSON containing:
    - status: "Success"
    - show_again (bool): Whether card should be shown again today
      * True if next review is within 24 hours
      * False if next review is later

  Notes:
  - FSRS Implementation:
    * Maintains review history and scheduling data
    * Adapts schedule based on performance
    * Handles both new and reviewed cards
  - Data Storage:
    * Stores in MongoDB fsrs_data field
    * Maintains complete review history
    * Updates due dates and review logs
  - Review Scheduling:
    * Cards may be shown multiple times per day
    * Due dates calculated based on difficulty and history
  - TODO: Remove redundancy of deleted cards

  See Also:
  get_rating(): Converts difficulty string to FSRS rating enum
  """
  # TODO remove redundancy of deleted cards
  qid = request.data.get("qid")
  mdb_fsrs_data = settings.MDB.flashcards.find_one({"qid": qid})
  fsrs_data = mdb_fsrs_data.get("fsrs_data", {}) if mdb_fsrs_data else {}
  current_card_id = str(request.data.get("currentCard").get("id"))
  difficulty = request.data.get("difficulty")
  f = fsrs.FSRS()
  if current_card_id in fsrs_data:
    card_data = fsrs_data[current_card_id]
    prev_card = fsrs.Card.from_dict(card_data['card'][-1])
    rating = get_rating(difficulty)
    card,review_log = f.review_card(prev_card, rating)
    due = card.due
    last_review = card.last_review
    card_dict = card.to_dict()
    review_log_dict = review_log.to_dict()
    fsrs_data[current_card_id] = {"due": due, "card": fsrs_data[current_card_id]["card"]+[card_dict], "review_log": fsrs_data[current_card_id]["review_log"]+[review_log_dict]}
    if due - last_review < timedelta(days=1): 
      show = True
    else: 
      show = False
  else: 
    card = fsrs.Card()
    rating = get_rating(difficulty)
    card, review_log = f.review_card(card, rating)
    due = card.due
    last_review = card.last_review
    card_dict = card.to_dict()
    review_log_dict = review_log.to_dict()
    fsrs_data[current_card_id] = {"due": due, "card": [card_dict], "review_log": [review_log_dict]}
    if due - last_review <= timedelta(days=1):
      show = True
    else: 
      show = False
    print(card_dict, review_log_dict)
  settings.MDB.flashcards.update_one({"qid": qid}, {"$set":{"fsrs_data": fsrs_data}})
          
  return Response({"status": "Success", "show_again": show})

def make_aware(date):
  return timezone.make_aware(date, timezone.get_current_timezone()) if timezone.is_naive(date) else date

@api_view(["POST"])
@csrf_exempt
def due_dates_mdb_sql(request): 
  """
  Synchronizes FSRS due dates from MongoDB to SQL database.

  Fetches flashcard review schedules from MongoDB and creates corresponding
  Review objects in Django's SQL database for efficient querying.

  Args:
    request (HttpRequest): Django request object containing:
      - qid (str): Question/flashcard set identifier

  Returns:
    Response: JSON containing:
      - status: "Success"

  Notes:
    - Uses atomic transaction for data consistency
    - Ignores conflicts for duplicate reviews
    - Bulk creates reviews for efficiency
  """
  qid = request.data.get("qid")
  doc = settings.MDB.flashcards.find_one({"qid":qid})
  print(doc)
  fsrs_data = doc['fsrs_data']
  fsrs_data_keys = fsrs_data.keys()
  user = CustomUser.objects.get(id=doc['user_id'])
  review_items = []
  for key in fsrs_data_keys:
    due_date = fsrs_data[key]['due']
    print(due_date)
    review_items.append(
      Reviews(
        review_date=due_date,
        document=qid,
        student=user,
        card_id=key
      )
    )

  # Use bulk_create with ignore_conflicts to efficiently create multiple objects
  with transaction.atomic():
    Reviews.objects.bulk_create(review_items, ignore_conflicts=True)
  return Response({"status": "Success", })

@api_view(["POST"])
def grade_quiz_old_placeholder(request):
  """
  OLD PLACEHOLDER - Replaced by grade_quiz_reading below
  """
  return Response()

@api_view(["POST"])
def finish_tour(request):
  """
  Marks the user tour as completed.

  Updates user profile to indicate onboarding tour has been completed.

  Args:
    request (HttpRequest): Django request object with authenticated user

  Returns:
    Response: JSON containing:
      - message: "success"
  """ 
  user = request.user
  user.tour = True
  user.save()
  return Response({'message': "success"})

def get_readings_for_date(course_id, date_str):
  """
  Retrieves reading assignments for a specific date and course.

  Queries MongoDB for reading documents within a 24-hour period.

  Args:
    course_id (str): Course identifier
    date_str (str): Date in format "YYYY-MM-DD"

  Returns:
    cursor: MongoDB cursor containing matching reading documents

  Notes:
    - Includes full day (00:00:00 to 23:59:59)
    - Filters by course_id and time range
  """
  # Parse the date string
  target_date = datetime.strptime(date_str, "%Y-%m-%d")
  
  # Create start and end of the day
  start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
  end_of_day = start_of_day + timedelta(days=1)

  # Construct the query
  query = {
    "course_id": course_id,
    "time": {
      "$gte": start_of_day,
      "$lt": end_of_day
    }
  }

  # Execute the query
  documents = settings.MDB_1.readings.find(query)

  return documents

@api_view(["POST"])
def get_data(request, course_id):
  """
  Retrieves and processes reading data for a specific date.

  Calculates percentile scores for readings on given date.

  Args:
    request (HttpRequest): Django request object containing:
      - currentDate (str): Target date
      - course_id (str): Course identifier
    course_id (str): URL parameter course identifier

  Returns:
    Response: JSON containing:
      - data (dict): Percentile scores (10th through 90th)
      - rating: None
      - time: None

  Notes:
    - Calculates percentiles only if scores exist
    - Returns empty data if no scores found
  """
  date = request.data.get("currentDate")
  course_id = request.data.get("course_id")
  print(course_id)
  print(date)
  documents = get_readings_for_date(course_id, date)
  mpc_scores = [doc['mpc_score'] for doc in documents if 'mpc_score' in doc]
  mpc_scores.sort()
  if len(mpc_scores) > 0:
    percentiles = [f"{i}0th" for i in range(1, 11)]
    data = {}
    
    for i, percentile in enumerate(percentiles):
      index = math.ceil((i + 1) * 0.1 * len(mpc_scores)) - 1
      data[percentile] = mpc_scores[index]
  else:
    data = {}
  ratings = ["C2/1100", "C3/1500"]
  return Response({"data": data, "rating": None , "time":None})

@api_view(["POST"])
def get_fsrs_performance(request):
  """
  Generates performance data for FSRS visualization.

  Creates sequential number mapping for graph display.

  Args:
    request (HttpRequest): Django request object

  Returns:
    Response: JSON containing:
      - graph_data (dict): Mapping of integers 0-9 to sequential values
  """
  num_dictionary = {}
  data = iter([x for x in range(0, 10)])

  for integer in range(0,10):
    num_dictionary[f"{integer}"] = next(data)
  return Response({"graph_data": num_dictionary})

@api_view(["POST"])
def upload_flashcard_image(request):
  """
  Handles image upload for flashcard content.

  Saves uploaded images and associates them with specific flashcard sides.

  Args:
    request (HttpRequest): Django request object containing:
      - qid (str): Question/flashcard set identifier
      - cardId (str): Specific card identifier
      - userId (str): User's identifier
      - image (File): Image file to upload
      - side (str): Card side to associate image with ("front" or "back")

  Returns:
    Response: JSON containing:
      - message: "success"
      - imageUrl (str): URL of uploaded image

  Notes:
    - Creates user/qid-specific upload paths
    - Updates MongoDB with image URL
    - Uses unique filenames to prevent collisions
  """
  print(request.data)
  qid = request.data.get("qid")
  card_id = request.data.get("cardId")
  user_id = request.data.get("userId")
  file = request.data.get("image")
  side = request.data.get("side")
  flashcards = settings.MDB.flashcards.find_one({"qid": qid})["cards"]
  for index, card in enumerate(flashcards):
    if card_id in card:
      file_path = f'uploads/{user_id}/{qid}'
      file_name = save_unique_file(file, folder=file_path)
      file_url = default_storage.url(file_name)
      settings.MDB.flashcards.update_one({"qid": qid}, {"$set": {f"cards.{index}.{side}-image": file_url}})
  return Response({"message": "success", "imageUrl": file_url})


# Cloud Function Replacements - Local implementations

@api_view(["POST"])
@csrf_exempt
def generate_questions(request):
  """
  Generates quiz questions from a reading text using OpenAI.
  Replaces: https://us-central1-your-gcp-project-id.cloudfunctions.net/testfunction
  """
  import textwrap
  import openai
  
  data = request.data
  question_topics = data.get('question_topics')
  question_strategy = data.get('question_strategy')
  story = data.get('story')
  original_query = data.get('original_query')
  practice_id = data.get('practice_id')
  PROD = data.get('PROD')
  
  openai.api_key = settings.OPENAI_KEY
  
  query = textwrap.dedent(
    f"""You are a teacher and are going to assess your students on text comprehension. For the questions, you should carefully follow the instructions provided below.

{question_topics}

The student should be nudged for the following reading strategy:

{question_strategy} Return a json object with the key 'questions' and a list of 15 questions no more, no less. Each question should be a string.  Additionally, include another nested key called "answers" for each of the questions that has 4 possible answers with one that is correct and another key that is 'correct_index' with the precise zero-index of the answer that is correct.
                        Add one open question in the end, and for this one do not attach any answers under the 'answers' key, but only for this question.  
                        You can create multiple-choice questions, open questions, and highlighting questions. Highlighting questions are questions where students need to highlight the answer in the text.
Thes string for "type" key should be all lowercase. "multiple" for multiple choice, "highlight" for a highlighting question, "open" for open-ended questions. If the question is a highlighting question, the exact sentence that the student should highlight should be placed in the "correct_highlight" key and the answers key and correct_index should be left empty. 
Make at least ten multiple choice questions. Also for each question add a key called "question_num" with the number of the question. Please only have ONE highlighting question
ONLY OUTPUT THE QUESTIONS! NOTHING ELSE. DO NOT return the letter of the questions (a,b,c,d), just return the possible answers for multiple choice
Please return a JSON file with the questions.
 {{
"questions": [
    {{
        "question_num": int,
        "question": "",
        "type": "",
        "answers": [],
        "correct_index": [], 
        "correct_highlight": "",
    }},]}}
                       Please ensure that you strictly adhere to this format and that the you always fill out the answers when they are multiple choice questions"""
    + story)
  
  while True:
    try:
      custom_message = [
        {"role": "user", "content": original_query},
        {"role": "assistant", "content": story},
        {"role": "user", "content": query},
      ]
      
      if PROD:
        print('using gpt-4')
        response = openai.chat.completions.create(
          model="ft:gpt-3.5-turbo-0125:youcademy:questions:9VbNoDqo",
          response_format={"type": "json_object"},
          messages=custom_message,
        )
      else:
        print('using gpt-4o-mini')
        response = openai.chat.completions.create(
          model="gpt-4o-mini",
          response_format={"type": "json_object"},
          messages=custom_message,
        )
      
      response_content = response.choices[0].message.content
      quiz = json.loads(response_content)
      
      assert type(quiz["questions"]) == list, "not a list"
      highlight_num = 0
      for q in quiz["questions"]:
        assert "question" in q, "no 'question'"
        if q["type"] == "multiple":
          assert "answers" in q, "no 'option'"
          assert "correct_index" in q, "no 'answer'"
        if q["type"] == "highlight":
          highlight_num += 1
      assert highlight_num == 1, "no highlighting question, more than 1"
      
      # Store in MongoDB
      settings.MDB_1.questions.insert_one({
        "practice_id": practice_id,
        "quiz": quiz
      })
      
      return Response(quiz)
    except Exception as e:
      print("Failed to parse response for quiz: ", e)


@api_view(["POST"])
@csrf_exempt
def process_highlights(request):
  """
  Creates flashcards from highlighted text and unknown words using OpenAI.
  Replaces: https://us-central1-your-gcp-project-id.cloudfunctions.net/highlight_processing
  """
  import textwrap
  import openai
  
  data = request.data
  highlighted_text = data.get('highlighted_text')
  user_id = data.get('user_id')
  unknown_words = data.get('unknown_words')
  PROD = data.get('PROD')
  
  openai.api_key = settings.OPENAI_KEY
  
  print(unknown_words)
  
  # Generate flashcards
  flashcard_list = {
    "title": "text", 
    "topic": "text", 
    "cards": [
      {"id": 1, "frontHTML": "What is the capital of Alaska?", "backHTML": "Juneau"}, 
      {"id": 2, "frontHTML": "What is the capital of California?", "backHTML": "Sacramento"},
      {"id": 3, "frontHTML": "What is the capital of New York?", "backHTML": "Albany"},
      {"id": 4, "frontHTML": "What is the capital of Florida?", "backHTML": "Tallahassee"},
      {"id": 5, "frontHTML": "What is the capital of Texas?", "backHTML": "Austin"},
      {"id": 6, "frontHTML": "What is the capital of New Mexico", "backHTML": "Santa Fe"},
      {"id": 7, "frontHTML": "What is the capital of Arizona?", "backHTML": "Phoenix"}
    ]
  }
  
  query = textwrap.dedent(
    f"""Please create flashcards for the following words: {unknown_words}. The flashcards should be in a JSON and in the following format DO NOT include any html tags with the cards: 
    {{
"cards": [
    {{
        "id": int,
        "frontHTML": This is important text,
        "backHTML": "This is the back of the card"
    }},] "title": "text", "topic": "text"}}
    Example with text: 
    \n{json.dumps(flashcard_list, indent=4)}
    """)
  
  custom_message = [
    {
      "role": "system",
      "content": "You are in charge of teaching students that are learning english as their second language, such that you are in charge of listening to the and returning a JSON file with flashcards. Create one card for each word"
    },
    {
      "role": "assistant",
      "content": query
    },
  ]
  
  MAX_ATTEMPTS = 5
  
  for attempt in range(MAX_ATTEMPTS):
    try:
      response = openai.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=custom_message,
      )
      response_content = response.choices[0].message.content
      flashcards = json.loads(response_content)
      
      assert type(flashcards["cards"]) == list, "not a list"
      for q in flashcards["cards"]:
        assert "id" in q, "no 'id'"
        assert "frontHTML" in q, "no 'frontHTML'"
        assert "backHTML" in q, "no 'backHTML'"
      
      # Store in MongoDB
      new_flashcard = str(uuid.uuid4())
      settings.MDB.flashcards.insert_one({
        "qid": new_flashcard,
        "user_id": user_id,
        "cards": flashcards["cards"],
        "title": flashcards["title"],
        "topic": flashcards["topic"],
        "created_at": datetime.now().isoformat(),
        "last_viewed": datetime.now().isoformat(),
      })
      print("the cards were uploaded to the mongoDB database")
      
      return Response(flashcards)
    except Exception as e:
      print(f"Attempt {attempt + 1} failed: {e}")
      if attempt == MAX_ATTEMPTS - 1:
        print("Max attempts reached. Exiting.")
        return Response({
          'cards': [{"id": 1, "frontHTML": "", "backHTML": ""}], 
          "title": "New Flashcard Set", 
          "topic": "New Flashcard Set"
        })


@api_view(["POST"])
@csrf_exempt
def grade_quiz_reading(request):
  """
  Grades quiz answers including multiple choice, highlight, and open questions.
  Replaces: https://us-central1-your-gcp-project-id.cloudfunctions.net/grade_quiz
  """
  from copy import deepcopy
  import openai
  
  data = request.data
  course_id = data.get('course_id')
  answers = data.get('answers')
  practice_id = data.get('practice_id')
  PROD = data.get('PROD')
  user_id = data.get('user_id')
  
  openai.api_key = settings.OPENAI_KEY
  
  quiz = settings.MDB_1.questions.find_one({"practice_id": practice_id})
  story = settings.MDB_1.readings.find_one({"practice_id": practice_id})['text']
  
  # Grade the quiz
  graded_questions = deepcopy(quiz)
  
  # Parse user answers
  user_answers = json.loads(answers['responses'][0])
  mpc_count = 0
  mpc_grade = 0
  
  for question in graded_questions['quiz']['questions']:
    q_num = question['question_num']
    q_type = question['type']
    user_answer = user_answers.get(f'question_{q_num}', {}).get('forminput')
    
    if q_type == 'multiple':
      correct_index = question['correct_index']
      correct_answer = question['answers'][int(correct_index)]
      is_correct = user_answer == correct_answer
      user_answer_index = question['answers'].index(user_answer) if user_answer in question['answers'] else None
      
      question['user_answer'] = user_answer
      question['user_answer_index'] = user_answer_index
      question['is_correct'] = is_correct
      mpc_count += 1
      mpc_grade += is_correct
      
    elif q_type == 'highlight':
      correct_highlight = question['correct_highlight'].strip()
      user_highlights = user_answers.get(f'question_{q_num}', {}).get('highlights', {}).get('yellow', [])
      highlighted_text = ' '.join([highlight['text'] for highlight in user_highlights]).strip()
      correct_chars = set(correct_highlight)
      highlighted_chars = set(highlighted_text)
      correct_chars_highlighted = len(correct_chars.intersection(highlighted_chars))
      total_correct_chars = len(correct_chars)
      grade = (correct_chars_highlighted / total_correct_chars) * 100 if total_correct_chars > 0 else 0
      
      question['user_answer'] = highlighted_text
      question['grade'] = round(grade, 2)
      
      custom_message = [
        {"role": "system", "content": f"Given this story. {story}. And this question {question['question']} Grade the user's answer."}, 
        {"role": "user", "content": f"This is my answer: {highlighted_text}"}
      ]
      response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=custom_message,
      )
      question['feedback'] = [{"type": "AI", "message": response.choices[0].message.content}]
      question['yellow_highlights'] = user_highlights
      
    elif q_type == 'open':
      question['user_answer'] = user_answer
      custom_message = [
        {"role": "system", "content": f"Given this story. {story}. And this question {question['question']} Grade the user's answer. Return positive feedback. Return only text."}, 
        {"role": "user", "content": f"This is my answer: {user_answer}"}
      ]
      response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=custom_message,
      )
      question['feedback'] = [{"type": "AI", "message": response.choices[0].message.content}]
      question['grade'] = 100
  
  graded_questions['graded'] = True
  graded_questions['course_id'] = course_id
  graded_questions['user_id'] = user_id
  graded_questions['mpc_grade'] = (mpc_grade / mpc_count) * 100 if mpc_count > 0 else 0
  
  # Update MongoDB
  settings.MDB_1.questions.update_one({"practice_id": practice_id}, {"$set": graded_questions})
  settings.MDB_1.readings.update_one({"practice_id": practice_id}, {"$set": {"graded": True}})
  
  return Response({"message": "Success"})