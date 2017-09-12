# THIRD PARTY
from djangae import fields as djangae_fields
from django.db import models


class QuestionSession(models.Model):
    """ A Q & A session in which someone is asked questions. """

    name = djangae_fields.CharField()
    time = models.DateTimeField()

    def wipeout(self):
        """ Wipe out all the data from the question session, leaving only the questions
            and the number of votes for each.  This is to aid anonymity.
        """

        # TODO: check that this can only be called AFTER the Q & A session has happened.
        raise NotImplementedError


class Question(models.Model):
    """ A question which an audience member would like to be asked in the question session. """

    session = models.ForeignKey(QuestionSession)
    text = djangae_fields.CharField(max_length=140)  # Twitter-style length limit!
    votes = djangae_fields.ShardedCounterField(shard_count=10)


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

