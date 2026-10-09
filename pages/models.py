from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.utils import timezone

# Create your models here.
class CustomUser(AbstractUser):
    name = models.CharField(max_length=100, default="Anonymous")
    occupation = models.CharField(max_length=100)
    diagnostic = models.BooleanField(default=False)
    color = models.CharField(max_length=100, default="#132143")
    timezone = models.CharField(max_length=100, default="UTC")
    admin = models.BooleanField(default=False)
    tour = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name
    
class Feedback(models.Model): 
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    user_occupation = models.CharField(max_length=36, null=True)
    positive = models.BooleanField()
    document_reference = models.CharField(max_length=100)
    item_num = models.IntegerField(null=True)
    item_type = models.CharField(max_length=36, null=True)

class BinarySearchParameters(models.Model): 
    high = models.IntegerField(null=True)
    low = models.IntegerField(null=True)  
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
class LearningStreak(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    def update_streak(self):
        today = timezone.now().date()
        if self.last_activity_date == today:
            # Already updated today, do nothing
            return
        elif self.last_activity_date == today - timezone.timedelta(days=1):
            # Consecutive day, increase streak
            self.current_streak += 1
            self.longest_streak = max(self.current_streak, self.longest_streak)
        else:
            # Streak broken, reset to 1
            self.current_streak = 1
        
        self.last_activity_date = today
        self.save()
    
class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="course+")
    course_code = models.CharField(max_length=100)
    students = models.ManyToManyField(CustomUser, related_name="courses", blank=True, )
    writing_prompts = models.ManyToManyField('WritingPrompts', related_name="courses", blank=True, )
    def __str__(self):
        return self.name

class WritingPrompts(models.Model): 
    name = models.CharField(max_length=100)
    prompt = models.TextField()
    def __str__(self):
        return self.name


class Metrics(models.Model):
    date = models.DateTimeField(auto_now=True)
    # one student can have many metrics
    student = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name="metrics", null=True)
    # one course can have many metrics
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name="metrics", null=True)
    raw_data = models.OneToOneField('RawData', on_delete=models.CASCADE, related_name="metrics", null=True)
    test_readiness_score = models.FloatField(null=True)
    areas_of_struggle = models.JSONField(default=dict, null=True)
    estimated_lexile_level = models.IntegerField(null=True)
    confidence_score = models.FloatField(null=True)
    # words per minute
    reading_speed = models.FloatField(null=True)
    quiz_score_average = models.FloatField(null=True)
    average_reading_time = models.FloatField(null=True)
    average_questions_time = models.FloatField(null=True)
    average_length_of_highlight = models.FloatField(null=True)
    average_removed_highlights = models.FloatField(null=True)
    average_uknown_words = models.FloatField(null=True)
    average_questions_asked = models.FloatField(null=True)
    story_elements_score = models.FloatField(null=True)
    problem_solution_score = models.FloatField(null=True)
    poetry_score = models.FloatField(null=True)
    sequences = models.FloatField(null=True)
    explicit_details = models.FloatField(null=True)
    cause_effect = models.FloatField(null=True)
    descriptive = models.FloatField(null=True)
    implicit = models.FloatField(null=True)
    location_details = models.FloatField(null=True)
    estimated_cefr_rating = models.CharField(max_length=100, null=True)
    estimated_level = models.CharField(max_length=100, null=True)
# this corresponds to one quiz or one reading
class RawData(models.Model):
    date = models.DateTimeField(auto_now=True)
    student = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name="raw_data", )
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name="course")
    removed_highlights = models.IntegerField(null=True)
    number_of_highlights = models.IntegerField(null=True)
    number_of_unknown_words = models.IntegerField(null=True)
    avg_length_of_highlight = models.FloatField(null=True)
    # this could be readings or questions
    estimated_lexile_level_text = models.IntegerField(null=True)
    time_seconds = models.FloatField(null=True)
    left_page = models.IntegerField(null=True)
    # for questions
    order_answers = models.CharField(max_length=200, null=True)
    missing_answers = models.IntegerField(null=True)
    right_answers = models.IntegerField(null=True)
    total_questions = models.IntegerField(null=True)
    score = models.FloatField(null=True)
    practice_session = models.ForeignKey('PracticeSessions', on_delete=models.CASCADE, null=True, related_name="raw_data", blank=True)

class PracticeSessions(models.Model):
    date = models.DateTimeField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    
# TODO figure out if we want on_delete to be CASCADE or SET_NULL...    
class Notes(models.Model):
    # change this field to datetime...
    date = models.DateTimeField(auto_now=True)
    pink_highlights = models.JSONField(default=list)
    yellow_highlights = models.JSONField(default=list)
    raw_data = models.ForeignKey(RawData, on_delete=models.CASCADE, related_name="notes", null=True)
    notes = models.TextField()
    # TODO set this as null = False
    reading = models.TextField(null=True)
class MCQuestions(models.Model):
    date = models.DateTimeField(auto_now=True)
    raw_data = models.ForeignKey(RawData, on_delete=models.CASCADE, related_name="mc_questions", null=True)
    question = models.TextField()
    response = models.TextField()
    answer = models.TextField()
    correct = models.BooleanField()


class OpenQuestions(models.Model):
    date = models.DateTimeField(auto_now=True)
    raw_data = models.ForeignKey(RawData, on_delete=models.CASCADE, related_name="open_questions", null=True)
    question = models.TextField(null=True)
    response = models.TextField(null=True)
    grade = models.TextField(null=True)
    feedback = models.TextField(null=True, blank=True)

class Reading(models.Model):
    title = models.CharField(max_length=100)
    text = models.TextField()
    lexile_level = models.IntegerField()
    word_count = models.IntegerField()
    raw_data = models.OneToOneField(RawData, on_delete=models.CASCADE, related_name="reading", null=True, blank=True)
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="readings", null=True, blank=True)
class Strategy(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    practice_session = models.ManyToManyField('PracticeSessions',  related_name="strategies", blank=True) 
    def __str__(self):
        return self.name

class StudentTeacherQuestion(models.Model): 
    date = models.DateTimeField(auto_now=True) 
    student = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name="student_teacher_questions") 
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name="student_teacher_questions")
    question = models.TextField() 
    response = models.TextField() 
    answered = models.BooleanField(default=False) 
    def __str__(self): 
        return self.question    

class Reviews(models.Model):
    review_date = models.DateTimeField()
    document = models.CharField(max_length=36, blank=False, null=False)
    student = models.ForeignKey("CustomUser", on_delete=models.CASCADE, related_name="review")
    card_id = models.CharField(max_length=50, blank=False, null=False) 

class QuizScore(models.Model):
    date = models.DateTimeField()
    mdb_ref = models.CharField(max_length=36, blank=False, null=False)
    grade = models.FloatField(null=True)
    student = models.ForeignKey("CustomUser", on_delete=models.CASCADE, related_name="quizscore")
    
