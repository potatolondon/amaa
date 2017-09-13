# STANDARD LIB
import logging

# THIRD PARTY
from djangae.db import transaction
from django.conf import settings
from django.http import HttpResponse
from google.appengine.ext import deferred


logger = logging.getLogger(__name__)


def sum_votes(request):
    """ For any QuestionSessions which are live, find all the Questions and sum up their
        votes from the sharded counter field into a single model field.
        This is because the sharded counter field can't be ordered on, but we need the sharded
        counter field in order to allow many people to vote at once without hitting the Datastore
        write rate limit.
    """
    # Our cron runs once per minute, but we want to update the votes much quicker than that, so we
    # fire off another task for each question so that we get an update every few seconds.
    # But (to avoid running crons all the time), we only fire off those tasks for questions that
    # have not yet been asked, in sessions that are active.
    from amaa.models import QuestionSession
    for session in QuestionSession.objects.filter(is_on_air=True):
        for question_pk in session.question_set.filter(is_asked=False).values_list('pk', flat=True):
            for countdown in xrange(0, 60, 10):
                deferred.defer(
                    _sum_votes_for_question, question_pk,
                    _queue=settings.QUEUES.VOTE_SUMMING,
                    _countdown=countdown
                )
    return HttpResponse("Vote summing tasks deferred.")


# Note that this transaction relies on there only being 10 shards in the `votes_sharded` field
@transaction.atomic()
def _sum_votes_for_question(question_pk):
    """ Given a single Question ID, check to see if the number of votes in the sharded counter
        field has changed, and if it has then update the non-sharded votes field.
    """
    from amaa.models import Question
    question = Question.objects.get(pk=question_pk)
    if question.is_asked:
        return
    sharded_votes = question.votes_sharded.count()
    if question.votes_summed != sharded_votes:
        if question.votes_summed > sharded_votes:
            logger.error("Question %s has more votes_sharded than votes_sharded.", question_pk)
            return

        question.votes_summed = sharded_votes
        question.save()


def create_votes_for_users(question_pk):
    """ Create all of the Vote objects (one for each user) for the given Question. """
    from amaa.models import Question, User, Vote
    question = Question.objects.get(pk=question_pk)
    assert not Vote.objects.filter(question=question).exists()
    votes = []
    for user in User.objects.all():
        votes.append(Vote(question=question, user=user))
    Vote.objects.bulk_create(votes)
    logger.info("Created votes for question %s", question_pk)



def _pre_create_users():
    """ Make sure that there is a User object for each user in USER_CHOICES. """
    raise NotImplementedError
