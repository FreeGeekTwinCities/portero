import pkg_resources
pkg_resources.require("Flask")

from datetime import date, datetime, timedelta
from decimal import *

from flask import Flask, render_template, request, url_for, redirect
from flask.ext.bootstrap import Bootstrap
from wtforms import Form, DateField, DateTimeField, DecimalField, HiddenField, TextField, SelectField, RadioField, validators

import json
import portero_config

app = Flask(__name__)
app.config.from_object('portero_config')
print app.config
	
import openerplib
connection = openerplib.get_connection(hostname=app.config['ERP_HOST'], database=app.config['ERP_DB'], login=app.config['ERP_USER'], password=app.config['ERP_PASSWORD'])

employee_model = connection.get_model("hr.employee")

attendance_model = connection.get_model("hr.attendance")
#print attendance_model
attendances_today = attendance_model.search_read([('day', '=', str(date.today().strftime('%Y-%m-%d')))])
#attendances = attendance_model.search_read([])
print attendances_today

timesheet_model = connection.get_model("hr_timesheet_sheet.sheet")
print timesheet_model
timesheets = timesheet_model.search_read([])
print timesheets

analytic_model = connection.get_model('account.analytic.account')
#print analytic_model
analytic_accounts = analytic_model.search_read([])
#for account in analytic_accounts:
#	print account['name']
	
department_model = connection.get_model('hr.department')
#print department_model
departments = department_model.search_read([])
#print departments

app.debug = app.config['DEBUG']
    
Bootstrap(app)

#Set up attendance form
class AttendanceForm(Form):
	employee = TextField('Volunteer')
	work = RadioField(choices=[(department['id'], department['name']) for department in departments], coerce=int)
	action = HiddenField()
	
#Display welcome page at root of site
@app.route("/", methods=['GET', 'POST'])
def hello():
	today = str(date.today().strftime('%Y-%m-%d'))
	employees = employee_model.search_read([("active", "=", True)])
	employees_signed_out = [('%s : %s' % (employee['id'], employee['name'])) for employee in employees if employee['state'] == 'absent']
	print employees_signed_out
	employees_signed_in = [{'id': employee['id'], 'photo': employee['photo'], 'name': employee['name']} for employee in employees if employee['state'] == 'present']
	print employees_signed_in
	for employee in employees_signed_in:
		current_work = timesheet_model.search_read([("date_current", "=", today), ("employee_id", "=", employee['id'])])
		employee['work'] = current_work[0]['department_id'][1]
	print employees_signed_in
		
	#Generate attendance entry form (defined in TimesheetForm above)
	form = AttendanceForm(request.form)
	event = 0
	sheet = 0
		
	if request.method == 'POST':
		employee_id = int(request.form['employee'][:request.form['employee'].find(':')])
		current_timesheets = timesheet_model.search([("employee_id", "=", employee_id), ("date_current", "=", today)])
		if len(current_timesheets):
			sheet = current_timesheets[0]
		else:
			new_sheet = {
				'employee_id' : employee_id,
				'company_id' : 1,
				'date_from' : today,
				'date_current' : today,
				'date_to' : today,
				'department_id' : request.form['work'],
			}
			sheet = timesheet_model.create(new_sheet)
			print sheet
		now = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		new_event = {
			'employee_id' : employee_id,
			'name' : now,
			'day' : today,
			'action' : 'sign_in',
			'sheet_id' : int(sheet)
		}
		event = attendance_model.create(new_event)
		print event
	
	return render_template('hello.html', form=form, event=attendance_model.read(event), employees=employees, employees_signed_out=json.dumps(employees_signed_out), employees_signed_in=employees_signed_in)

@app.route("/volunteer/sign_out", methods=['GET', 'POST'])
def sign_out():
	employee_id = request.args.get('volunteer_id')
	today = str(date.today().strftime('%Y-%m-%d'))
	now = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
	new_event = {
		'employee_id' : employee_id,
		'name' : now,
		'day' : today,
		'action' : 'sign_out'
	}
	event = attendance_model.create(new_event)
	print event
	return redirect(url_for('hello'))

if __name__ == "__main__":
    app.run()
