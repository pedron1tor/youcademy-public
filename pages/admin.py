from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Metrics)
admin.site.register(CustomUser)
admin.site.register(Course)
admin.site.register(PracticeSessions)
admin.site.register(Notes)
admin.site.register(MCQuestions)
admin.site.register(OpenQuestions)
admin.site.register(Strategy)
admin.site.register(Reading)
admin.site.register(StudentTeacherQuestion)
admin.site.register(RawData)
admin.site.register(WritingPrompts)
admin.site.register(BinarySearchParameters)
admin.site.register(Feedback)