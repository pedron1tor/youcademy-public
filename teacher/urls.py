from django.urls import path

from . import views

urlpatterns = [
    path("dashboard", views.dashboard, name="dashboard"),
    path("class/<int:course_id>", views.teacher_course, name="teacher_class"),
    path("class/<int:course_id>/assessment", views.teacher_assessment, name="teacher_assessment"),
    path("class/<int:course_id>/students/<int:student_id>", views.teacher_student, name="course_student"),
    path("lesson_plans", views.lesson_plans, name="lesson_plans"),
    path('lesson-editor/<uuid:qid>', views.lesson_editor, name='lesson_editor'),
    path('class/<int:course_id>/data-dashboard', views.dataview, name='data_dashboard'),
    path('class/<int:course_id>/practice-view/<uuid:practice_id>', views.teacher_practice_view, name='teacher_practice_view'),
    path('class/questions-view/<int:question_num>', views.teacher_questions_view, name='teacher_questions_view'),
    path('email-us', views.email_us, name="email_us"), 
    path('classes', views.classes, name="classes"), 
    path('writing-prompts/<int:course_id>', views.writing_prompts, name="writing_prompts"), 
]