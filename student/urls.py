from django.urls import path

from . import views

urlpatterns = [
 path('', views.student_home, name='student_home'),
 path('courses', views.courses, name="student_courses"),
 path('practice/<uuid:practice_id>', views.practice, name='practice'),
 path('questions/<int:question_num>', views.student_questions, name='questions'),
 path('query/<int:course_id>', views.student_query, name='query'),
 path('writing/<uuid:qid>/', views.writing, name='writing'),
 path('writing_menu/<int:course_id>', views.writing_menu, name='writing_menu'),
 path("flashcards-dash/<int:course_id>", views.flashcards_dash, name="flashcards_dash"),
 path('flashcards/<uuid:flashcard_id>', views.flashcards, name='flashcards'),
 path('reading_menu/<int:course_id>', views.reading_menu, name='reading_menu'),
 path('course/<int:course_id>', views.course, name='course'),
 path('edit-profile', views.edit_profile, name='edit_profile'),
 path('get-suggestions/', views.get_suggestions, name='get_suggestions'),
 path('left-page', views.left_page, name='left_page'),
 path('pronunciation/<int:course_id>/<int:question_id>', views.pronunciation, name='pronunciation'),
 path('pronunciation-dash/<int:course_id>', views.pronunciation_dash, name='pronunciation_dash'),
 path('pronunciation/<int:course_id>/running-record/<uuid:practice_id>', views.running_record, name='running_record'),
 path('new_reading/', views.test_reading, name="test_reading"), 
 path('learning-path/', views.learning_path, name="learning_path"), 
 path('bigger-picture/<int:course_id>/', views.bigger_picture, name="bigger_picture"), 
 path('grades/', views.grades, name='grades'),
]