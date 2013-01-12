#!/usr/bin/python
import sys
from flask import Flask
from couchdb.client import Server

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

for timesheet in results:
	if timesheet.value['volunteer'] == sys.argv[1]:
		print timesheet.value['date'], timesheet.value['volunteer'], timesheet.value['hours'], timesheet.value['work_type']

