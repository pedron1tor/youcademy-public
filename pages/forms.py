from django import forms 
from .models import Course, PracticeSessions, Strategy, CustomUser
import random
import string

def generate_unique_course_code():
    length = 8  # Define the length of the course code
    characters = string.ascii_uppercase + string.digits  # Use uppercase letters and digits
    course_code = ''.join(random.choices(characters, k=length))
    
    while Course.objects.filter(course_code=course_code).exists():
        course_code = ''.join(random.choices(characters, k=length))
    
    return course_code

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'small-description'}),
        }
        fields = '__all__'
        exclude = ['teacher', 'course_code']  # Exclude the teacher and course_code fields

    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        self.fields['students'].queryset = CustomUser.objects.filter(occupation='student')
        self.fields['students'].required = False  # Make students field optional

    def save(self, commit=True):
        course = super(CourseForm, self).save(commit=False)
        course.name = course.name.strip()  # Strip trailing spaces from the name
        if not course.course_code:  # Only generate if there's no existing course code
            course.course_code = generate_unique_course_code()
        if commit:
            course.save()
            self.save_m2m()  # Save the many-to-many relationships
        return course


class PracticeSessionForm(forms.ModelForm):
    class Meta:
        model = PracticeSessions
        fields = '__all__'
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),}
    def __init__(self, *args, **kwargs):
        # Extract teacher from kwargs with a default of None
        teacher = kwargs.pop('teacher', None)
        super(PracticeSessionForm, self).__init__(*args, **kwargs)

        if teacher is not None:
            # Filter the course queryset to only include courses taught by this teacher
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher)

        

class ReadingStrategyForm(forms.ModelForm):
    class Meta:
        model = Strategy
        widgets = {
            'description': forms.Textarea(attrs={'rows':2, 'class': 'small-description'}),
        }
        fields = '__all__' 