# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from icalendar import Calendar, Event, FixedOffset
from datetime import datetime
from dateutil.tz import tzoffset
import os, urllib2, json
import re

months = {
	u'January' : 1,
	u'February' : 2,
	u'March' : 3,
	u'April' : 4,
	u'May' : 5,
	u'June' : 6,
	u'July' : 7,
	u'August' : 8,
	u'September' : 9,
	u'October' : 10,
	u'November' : 11,
	u'December' : 12
}

cours = json.load(open(os.path.dirname(__file__) + '/codes.json'))

titlere = re.compile(r'<h1>([^<]*)', re.U)
eventre = re.compile(r'<tr><td align=["\']right["\']>(?:\w+) (?P<day>\d+) (?P<month>[é\w]+) (?P<year>\d+)</td><td>(?P<starth>\d+):(?P<startm>\d+) - (?P<endh>\d+):(?P<endm>\d+)</td><td><b>(?P<descr>[^<]*)</b></td></tr>', re.U)

def getEvents(code):
	url = 'http://sgs.ensmp.fr/prod/sgs/ensmp/catalog/course/detail.php?type=PROGRAM&lang=FR&code=' + code
	page = unicode(urllib2.urlopen(url).read(), 'latin-1')
	title = titlere.search(page).groups()[0]
	for m in eventre.finditer(page):
		evt = Event()
		descr = m.group('descr')
		evt.add('summary', title + (' - ' + descr if descr else ''))
		evt.add('dtstart', datetime(int(m.group('year')), months[m.group('month')], int(m.group('day')), int(m.group('starth')),int(m.group('startm')), tzinfo=tzoffset("GMT+1",3600)))
		evt.add('dtend', datetime(int(m.group('year')), months[m.group('month')], int(m.group('day')), int(m.group('endh')),int(m.group('endm')), tzinfo=tzoffset("GMT+1",3600)))
		yield evt

def getics(request):
	cal = Calendar()
	codes = request.GET.getlist('codes')
	for code in codes:
		for evt in getEvents(code):
			cal.add_component(evt)
	response = HttpResponse(content_type="text/calendar; charset=utf-8")
	response['charset'] = "utf-8"
	response.write(str(cal))
	return response

@login_required
def index(request):
	return render_to_response('timetable/timetable.html', {'cours': cours}, context_instance=RequestContext(request))
