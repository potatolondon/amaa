from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^big-screen/(?P<pk>\d+)/$', views.big_screen, name='big_screen'),
    url(r'^all-questions/$', views.all_questions, name='all_questions'),
    url(r'^session/(?P<pk>\d+)/$', views.question_list, name='question_list'),
    url(r'^finish-session/(?P<pk>\d+)/$', views.finish_session, name='finish_session'),
    url(r'^vote-question/(?P<pk>\d+)/$', views.vote_question, name='vote_question'),
    url(r'^$', views.session_list, name='session_list'),
]
