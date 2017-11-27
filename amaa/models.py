# STANDARD LIB
from datetime import timedelta

# THIRD PARTY
from djangae import fields as djangae_fields
from djangae.contrib.gauth_datastore.models import GaeAbstractDatastoreUser
from django.conf import settings
from django.db import models, IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from google.appengine.api import taskqueue
from google.appengine.ext import deferred

# AMAA
from .views import tasks


class User(GaeAbstractDatastoreUser):
    """ Our own custom user model.  Nothing really custom about it yet, but creating our own model
        so that we don't have to change the DB table if we want to add custom fields later.
    """
    pass


class QuestionSession(models.Model):
    """ A Q & A session in which someone is asked questions. """

    name = djangae_fields.CharField()
    time = models.DateTimeField()
    owners = djangae_fields.RelatedSetField(settings.AUTH_USER_MODEL)
    is_finished = models.BooleanField(default=False)

    def wipeout(self):
        """ Wipe out all the data from the question session, leaving only the questions
            and the number of votes for each.  This is to aid anonymity.
        """
        assert self.votes_can_be_wiped()
        deferred.defer(
            tasks.delete_votes_from_session, self.pk,
            _queue=settings.QUEUES.WIPEOUT
        )

    def votes_can_be_wiped(self):
        """ Is it ok to delete the vote data from this session? """
        # TODO: Possibly we should check that the session is in the past as well, but that then
        # means that you can't wipe out the voting data for a session which you decide to cancel
        return self.is_finished

    def __str__(self):
        return self.name


class Question(models.Model):
    """ A question which an audience member would like to be asked in the question session. """

    session = models.ForeignKey(QuestionSession, related_name='question_list')
    text = djangae_fields.CharField(max_length=140)  # Twitter-style length limit!
    votes_sharded = djangae_fields.ShardedCounterField(shard_count=10)
    votes_summed = models.PositiveIntegerField(default=0)
    is_asked = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """ Save the model, and if we are CREATING this Question, then defer a task to create the
            vote objects for all the users.
        """
        is_adding = self._state.adding  # Store a reference which we check after save
        return_value = super(Question, self).save(*args, **kwargs)
        if is_adding:
            deferred.defer(
                tasks.create_votes_for_users,
                self.pk,
                _queue=settings.QUEUES.VOTE_CREATION,
            )
        return return_value

    def get_vote_for_user(self, user):
        return Vote.objects.filter(question=self, user=user).first()

    def __str__(self):
        return self.text


class Vote(models.Model):
    """ A vote from an audience member to ANONYMOUSLY register their preference about whether or
        note a question should be asked.  Is linked to the user only UNTIL it is used.
    """

    question = models.ForeignKey(Question)
    answer = models.IntegerField(null=True)
    user = models.ForeignKey(User, null=True)

    def save(self, *args, **kwargs):
        self._run_integrity_checks()
        super(Vote, self).save()

    def _run_integrity_checks(self):
        """ Run integrity checks which can't be defined in the DB fields (e.g. unique constraints)
            but which also would NOT be user-fixable problems, i.e. are not validation errors.
        """
        if self.answer is not None and self.user:
            raise IntegrityError("Cannot have an answer and a user. This would break anonymity.")

    def vote(self, answer=True):
        """ Cast the vote as the given answer. """
        self.question.votes_sharded.increment()
        # Defer a task to run in 10 seconds' time.  But give it a consistent task name so that if
        # another person votes on this question in the meantime, the duplicate task is
        # ignored/cancelled
        try:
            deferred.defer(
                tasks.sum_votes_for_question,
                self.question_id,
                _queue=settings.QUEUES.VOTE_SUMMING,
                _countdown=10,
                _name="sum-votes-for-question-%s" % self.question_id,
            )
        except (taskqueue.TaskAlreadyExistsError, taskqueue.TombstonedTaskError):
            pass
        self.delete()
