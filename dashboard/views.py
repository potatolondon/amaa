# THIRD PARTY
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.core.urlresolvers import reverse

# AMAA
from amaa.models import QuestionSession, Question, Vote
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

    question_list = list(question_session.question_list.all())
    # Fetch all the corresponding Vote objects for the current user, if they haven't already been used
    question_pks = [q.pk for q in question_list]
    votes = list(request.user.vote_set.filter(question__pk__in=question_pks))
    can_vote_by_question = {vote.question_id: True for vote in votes}
    # Now assign a 'can vote' attribute to each question
    for question in question_list:
        question.can_vote = can_vote_by_question.get(question.pk, False)

    return render(request, template_name='dashboard/question_list.html', context={
        'question_session': question_session,
        'question_list': question_list,
        'form': form,
    })


def big_screen(request, pk):
    question_session = get_object_or_404(QuestionSession, id=pk)
    question_list = question_session.question_list.order_by("-votes_summed")
    context = {
        "question_session": question_session,
        "question_list": question_list,
    }
    return render(request, 'dashboard/big_screen.html', context)


def all_questions(request):
    return render(request, template_name='dashboard/all_questions.html', context={})


def vote_question(request, pk):
    question = get_object_or_404(Question, id=pk)
    if request.POST:
        vote = question.get_vote_for_user(request.user)
        if vote is not None:
            vote.vote()
    return redirect(reverse('dashboard:question_list', kwargs={'pk': question.session.id}))


def finish_session(request, pk):
    """ Allows the user to mark the session as finished, which removes it from the home page
        listing and deletes all of the Vote objects (leaving only the counts).
    """
    session = get_object_or_404(QuestionSession, pk=pk)
    context = {
        "question_session": session,
    }
    if request.method == "POST":
        session.is_finished = True
        session.save()
        session.wipeout()
        context["wipeout_started"] = True

    return render(request, "dashboard/finish_session.html", context)


def wipeout_voting_data(request):
    # This will allow you to call QuestionSession.wipeout() after a session is finished.
    # This might not be needed if we trigger it from the finish view.
    raise NotImplementedError
