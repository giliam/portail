from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('bda.views',
	url(r'^$', 'archives', name='revue'),
    url(r'^archives/$', 'archives', name='revue_archives'),
    url(r'^archives/json/$', 'archives_json', name='revue_archives_json'),
    url(r'^$', 'musiciens', name='musiciens'),
    url(r'^musiciens/$', 'musiciens', name='musiciens'),
    url(r'^credit_debit_eleve/$','credit_debit_eleve', name='soldes_bda'),
    )