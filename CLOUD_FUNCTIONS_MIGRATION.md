# Cloud Functions to Local API Migration

## Summary
Converted three Google Cloud Functions from the defunct `your-gcp-project-id` project to local Django API endpoints.

## Changes Made

### 1. New API Endpoints (`api/views.py`)
Added three new endpoints to handle cloud function logic locally:

- **`generate_questions()`** - Generates quiz questions from reading text using OpenAI
  - Route: `/api/generate-questions/`
  - Replaces: `https://us-central1-your-gcp-project-id.cloudfunctions.net/testfunction`

- **`process_highlights()`** - Creates flashcards from highlighted text and unknown words
  - Route: `/api/process-highlights/`
  - Replaces: `https://us-central1-your-gcp-project-id.cloudfunctions.net/highlight_processing`

- **`grade_quiz_reading()`** - Grades quiz answers (multiple choice, highlight, and open questions)
  - Route: `/api/grade-quiz-reading/`
  - Replaces: `https://us-central1-your-gcp-project-id.cloudfunctions.net/grade_quiz`

### 2. URL Routes (`api/urls.py`)
Added routes for the three new endpoints.

### 3. Updated Call Sites (`student/views.py`)
Replaced all Google Cloud Functions calls with local API calls:

- **Line ~345**: Question generation - now calls local API with threading for async behavior
- **Line ~377**: Highlight processing - now calls local API with threading for async behavior  
- **Line ~477**: Quiz grading - now calls local API with threading for async behavior

All calls use `threading.Thread` to maintain asynchronous behavior similar to the original Cloud Tasks implementation.

### 4. Import Updates
- Added `requests` and `threading` to imports in `student/views.py`
- Removed unused `TaskHandler` import

## Technical Notes

- **Async Processing**: Uses Python's `threading` module to execute API calls asynchronously, preventing blocking of the main request
- **Error Handling**: Each async function includes try-catch blocks with logging
- **Timeout**: Set to 300 seconds for OpenAI API calls
- **OpenAI API Key**: Uses `settings.OPENAI_KEY` from environment variables
- **MongoDB**: Uses existing `settings.MDB` and `settings.MDB_1` connections

## Testing

To test the migration:

1. Start Redis: `redis-server`
2. Start Django: `python manage.py runserver`
3. Navigate to a practice reading at `/student/practice/<uuid>`
4. Submit notes/highlights and verify flashcards are created
5. Complete quiz and verify it gets graded

## Dependencies

All dependencies already exist in `requirements.txt`:
- `openai` - for GPT API calls
- `pymongo` - for MongoDB operations
- `requests` - for HTTP requests
- `django-rest-framework` - for API views

## Environment Variables Required

- `OPENAI_KEY` - OpenAI API key
- `MONGO_URI` - MongoDB connection string
- `DEBUG` - Debug mode flag
- `SECRET_KEY` - Django secret key

## Files Modified

1. `/api/views.py` - Added 3 new endpoint functions (~300 lines)
2. `/api/urls.py` - Added 3 new URL routes
3. `/student/views.py` - Updated 3 cloud function call sites
4. `/mainframe/settings/local.py` - Disabled Google Cloud Storage for local development
5. `/manage.py` - Fixed infinite loop bug (removed `os.environ.clear()`)

