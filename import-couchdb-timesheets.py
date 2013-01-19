#!/usr/bin/python
import sys
import math
from flask import Flask
from couchdb.client import Server
from datetime import datetime

import_username = sys.argv[1]

# Connect to CouchDB 
server = Server(url='http://ledger:5984')
db = server['frontdesk']
results = db.view('frontdesk/timesheets_by_volunteer')

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
	print my_user
	print my_user['id']
	employee = employee_model.search_read([('user_id', '=', my_user['id'])])[0]
	print employee
	for timesheet in results:
		#print timesheet.value
		if timesheet.value['volunteer'] == import_username:
			timesheet_date = "%s-%s-%s" % (timesheet.value['date'][0], timesheet.value['date'][1], timesheet.value['date'][2])
			#timesheet.value['volunteer'], timesheet.value['hours'], timesheet.value['work_type']
			print timesheet.value
			timesheet_exists = timesheet_model.search_read([("employee_id", "=", employee['id']), ("date_from", "=", timesheet_date)])
			if len(timesheet_exists) == 1:
				openerp_timesheet = timesheet_exists[0]
			else:			
				imported_timesheet = {
					'employee_id' : employee['id'],
					'company_id' : 1,
					'date_from' : timesheet_date,
					'date_to' : timesheet_date,
					'department_id' : 1
				}
				openerp_timesheet = timesheet_model.create(imported_timesheet)
				print openerp_timesheet
			print openerp_timesheet
			
			in_time = str(datetime(int(timesheet.value['date'][0]), int(timesheet.value['date'][1]), int(timesheet.value['date'][2]), 12, 0, 0).strftime('%Y-%m-%d %H:%M:%S'))
			print in_time
			in_event = {
				'employee_id' : employee['id'],
				'name': in_time,
				'day' : timesheet_date,
				'action' : 'sign_in',
				'sheet_id' : openerp_timesheet
			}
			print in_event
			event = attendance_model.create(in_event)
			print event
			
			timesheet_hours = int(math.modf(timesheet.value['hours'])[1])
			print timesheet_hours
			timesheet_minutes = int(math.modf(timesheet.value['hours'])[0]*60)
			print timesheet_minutes
			out_time = str(datetime(int(timesheet.value['date'][0]), int(timesheet.value['date'][1]), int(timesheet.value['date'][2]), 12 + timesheet_hours, 0 + timesheet_minutes, 0).strftime('%Y-%m-%d %H:%M:%S'))
			print out_time
			out_event = {
				'employee_id' : employee['id'],
				'name': out_time,
				'day' : timesheet_date,
				'action' : 'sign_out',
				'sheet_id' : openerp_timesheet
			}
			print out_event
			event = attendance_model.create(out_event)
			print event
