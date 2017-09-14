from amaa.models import QuestionSession, Question
from django.shortcuts import render


def session_list(request):
    return render(request, template_name='dashboard/session_list.html', context={
        'question_session_list': QuestionSession.objects.all()
    })


def question_list(request, pk):
    question_session = QuestionSession.objects.get(id=pk)
    return render(request, template_name='dashboard/question_list.html', context={
        'question_session': question_session,
        'question_list': question_session.question_list.all()
    })


def big_screen(request):
    return render(request, template_name='dashboard/big_screen.html', context={})


def all_questions(request):
    return render(request, template_name='dashboard/all_questions.html', context={})
