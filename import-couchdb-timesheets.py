#!/usr/bin/python
import sys
import math
from flask import Flask
from couchdb.client import Server
from datetime import datetime
from operator import itemgetter, attrgetter

import_username = sys.argv[1]

# Connect to CouchDB 
server = Server(url='http://192.168.0.3:5984')
db = server['frontdesk']
results = db.view('frontdesk/timesheets_by_volunteer', key=import_username)
print results

# Connect to OpenERP
import openerplib
app = Flask(__name__)
app.config.from_object('portero_config')
connection = openerplib.get_connection(hostname=app.config['ERP_HOST'], database=app.config['ERP_DB'], login=app.config['ERP_USER'], password=app.config['ERP_PASSWORD'])
print connection

employee_model = connection.get_model("hr.employee")
user_model = connection.get_model('res.users')	
attendance_model = connection.get_model("hr.attendance")
timesheet_model = connection.get_model("hr_timesheet_sheet.sheet")
department_model = connection.get_model('hr.department')
departments = department_model.search_read([])
print departments

timesheets = timesheet_model.search_read([])
#print timesheets

user_found = user_model.search_read([('login', '=', import_username)])

if len(user_found) != 1:
	print "Username %s not found in OpenERP!" % import_username
else:
	my_user = user_found[0]
	#print my_user
	#print my_user['id']
	employee = employee_model.search_read([('user_id', '=', my_user['id'])])[0]
	#print employee
	
	timesheets_to_import = {}
	#print timesheets_to_import
	
	for timesheet in results:
		if timesheet.key == import_username:
			#print timesheet.value
			if 'year' in timesheet.value['date']:
				timesheet.value['date'] = [timesheet.value['date']['year'], timesheet.value['date']['month'], timesheet.value['date']['day']]
			timesheets_to_import["%s%s%s" % (timesheet.value['date'][0], str(timesheet.value['date'][1]).zfill(2), str(timesheet.value['date'][2]).zfill(2))] = timesheet.value
				
	for timesheet_id in reversed(sorted(timesheets_to_import)):
		timesheet = timesheets_to_import[timesheet_id]
		timesheet_date = "%s-%s-%s" % (timesheet['date'][0], timesheet['date'][1], timesheet['date'][2])
		print "Importing timesheet for %s" % timesheet_date
		imported_timesheet = {
			'employee_id' : employee['id'],
			'company_id' : 1,
			'date_from' : timesheet_date,
			'date_to' : timesheet_date,
			'department_id' : 1
		}
		openerp_timesheet = timesheet_model.create(imported_timesheet)
		print openerp_timesheet
		
		if isinstance( openerp_timesheet, ( int, long ) ):
			timesheet_id = openerp_timesheet
		else:
			timesheet_id = openerp_timesheet['id']
		
		timesheet_hours = int(math.modf(timesheet['hours'])[1])
		timesheet_minutes = int(math.modf(timesheet['hours'])[0]*60)
		#print timesheet_minutes
		out_time = str(datetime(int(timesheet['date'][0]), int(timesheet['date'][1]), int(timesheet['date'][2]), 12 + timesheet_hours, 0 + timesheet_minutes, 0).strftime('%Y-%m-%d %H:%M:%S'))
		print "Creating sign-out event at %s" % out_time
		out_event = {
			'employee_id' : employee['id'],
			'name': out_time,
			'day' : timesheet_date,
			'action' : 'sign_out',
			'sheet_id' : timesheet_id
		}
		print out_event
		event = attendance_model.create(out_event)
		#print event
		
		in_time = str(datetime(int(timesheet['date'][0]), int(timesheet['date'][1]), int(timesheet['date'][2]), 12, 0, 0).strftime('%Y-%m-%d %H:%M:%S'))
		print "Creating sign-in event at %s" % in_time
		in_event = {
			'employee_id' : employee['id'],
			'name': in_time,
			'day' : timesheet_date,
			'action' : 'sign_in',
			'sheet_id' : timesheet_id
		}
		print in_event
		event = attendance_model.create(in_event)
		#print event
		
		
