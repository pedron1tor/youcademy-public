from django.urls import path
from . import views

urlpatterns = [
    path('get-editor-content/', views.hello_world, name='hello_world'),
    path('update-editor-content/', views.update_editor, name='update_editor'),
    path('send-chat-editor-content/',
         views.send_chat_editor_content, name='send_chat_editor_content'),
    path('user-left/', views.user_left, name='user_left'),
    path('log-chat-session/', views.log_chat_session, name='log_chat_session'),
    path('get-chat-session/', views.get_chat_session, name='get_chat_session'),
    path('get-flashcards/', views.flashcards, name='get_flashcards'),
    path('save-flashcards/', views.save_flashcards, name='save_flashcards'),
    path('get_prompts/', views.get_prompts, name='get_prompts'),
    path('upload_image/', views.upload_image, name='upload_image'),
    path('record-audio/', views.record_audio, name='record_audio'),
    path('running-record/', views.running_record, name='running_record'),   
    path('get-tts/', views.get_tts, name='get_tts'),
    path('card-response/', views.card_response, name='card_response'),
    path('due-dates-mdb-sql/', views.due_dates_mdb_sql, name='due_dates_mdb_sql'), 
    path('review-quiz/', views.grade_quiz_old_placeholder, name="review_quiz"),
    path('finish-tour/', views.finish_tour, name="finish_tour"), 
    path('get-graph-info/<int:course_id>/', views.get_data, name="get_data"),
    path('get-fsrs-performance/', views.get_fsrs_performance, name="get_fsrs_performance"), 
    path('upload-flashcard-image/', views.upload_flashcard_image, name="upload_flashcard_image"),
    # Local cloud function replacements
    path('generate-questions/', views.generate_questions, name="generate_questions"),
    path('process-highlights/', views.process_highlights, name="process_highlights"),
    path('grade-quiz-reading/', views.grade_quiz_reading, name="grade_quiz_reading"),
]