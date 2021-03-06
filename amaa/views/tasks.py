# STANDARD LIB
import logging

# THIRD PARTY
from djangae.db import transaction
from django.conf import settings
from django.db import IntegrityError
from django.http import HttpResponse

# AMAA
from amaa.constants import USER_CHOICES


logger = logging.getLogger(__name__)


def sum_votes_for_question(question_pk):
    """ Given a single Question ID, check to see if the number of votes in the sharded counter
        field has changed, and if it has then update the non-sharded votes field.
    """
    from amaa.models import Question
    # Note that this transaction relies on there only being 10 shards in the `votes_sharded` field
    with transaction.atomic(xg=True):
        question = Question.objects.get(pk=question_pk)
        if question.is_asked:
            return
        sharded_votes = question.votes_sharded.value()
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
        Vote.objects.create(question=question, user=user)
    logger.info("Created votes for question %s", question_pk)


def create_users(request):
    """ Make sure that there is a User object for each user in USER_CHOICES.
    """
    from amaa.models import User
    users_by_username = {username: name for name, username in USER_CHOICES}
    # Go through the existing users and remove them all from our dictionary.
    # That will then leave us with the users that we need to create
    for user in User.objects.all():
        username = user.email.split("@")[0]
        try:
            del users_by_username[username]
        except KeyError:
            logger.warning("User %s exists but is not in USER_CHOICES", username)

    # Now create any users which don't exist
    for username, name in users_by_username.items():
        email = "%s@%s" % (username, settings.GOOGLE_APPS_EMAIL_DOMAIN)
        first_name, last_name = name.split(None, 1)  # Yeah yeah, crude
        try:
            User.objects.pre_create_google_user(email, first_name=first_name, last_name=last_name)
            logger.info("Created new user %s", email)
        except IntegrityError as e:
            pass

    return HttpResponse("Users created")


def delete_votes_from_session(session_pk):
    """ Wipe out Vote data from old QuestionSessions so that we (further) protect anonymity.
        This avoids things like seeing who voted for something when only one person used their
        vote (because the unused Vote objets would tell you who the one used vote belonged to).
        We should leave only the questions and the vote counts.
    """
    from amaa.models import QuestionSession
    session = QuestionSession.objects.get(pk=session_pk)
    if not session.votes_can_be_wiped():
        logger.info(
            "Not wiping votes from session %s because either it's not (far enough) in the past "
            "or it's still on air.",
            session_pk
        )
        return
    for question in session.question_list.all():
        question.vote_set.all().delete()
    logger.info("Finishing deleting Vote objects from session %s", session_pk)
