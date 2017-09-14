# THIRD PARTY
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.core.urlresolvers import reverse

# AMAA
from amaa.models import QuestionSession, Question
from dashboard.forms import QuestionForm


def session_list(request):
    return render(request, template_name='dashboard/session_list.html', context={
        'question_session_list': QuestionSession.objects.all()
    })


def question_list(request, pk):
    question_session = get_object_or_404(QuestionSession, id=pk)

    if request.POST:
        form = QuestionForm(request.POST)

        if form.is_valid():
            Question.objects.create(
                session=question_session,
                text=form.cleaned_data['question'],
            )
            return redirect(reverse('dashboard:question_list', kwargs={'pk': question_session.pk}))
    else:
        form = QuestionForm()

    return render(request, template_name='dashboard/question_list.html', context={
        'question_session': question_session,
        'question_list': question_session.question_list.all(),
        'form': form,
    })


def big_screen(request):
    return render(request, template_name='dashboard/big_screen.html', context={})


def all_questions(request):
    return render(request, template_name='dashboard/all_questions.html', context={})


def submit_question(request):
    raise NotImplementedError


def finish(request, session_pk):
    # This will allow you to set the 'is_finished' flag to True and wipe out the voting data.
    # That will have the effect of hiding the session from the home page
    raise NotImplementedError


def wipeout_voting_data(request):
    # This will allow you to call QuestionSession.wipeout() after a session is finished.
    # This might not be needed if we trigger it from the finish view.
    raise NotImplementedError
