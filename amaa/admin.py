from django.contrib.admin import site

# AMAA
from amaa.models import (
    QuestionSession,
    Question,
    Vote,
)


site.register(QuestionSession)
site.register(Question)
site.register(Vote)
