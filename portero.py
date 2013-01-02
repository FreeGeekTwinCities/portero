import pkg_resources
pkg_resources.require("Flask")

from datetime import date, datetime, timedelta
from decimal import *

from flask import Flask, render_template, request, url_for, redirect
from flask.ext.bootstrap import Bootstrap
from wtforms import Form, DateField, DateTimeField, DecimalField, HiddenField, TextField, SelectField, RadioField, PasswordField, validators

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

department_model = connection.get_model('hr.department')
departments = department_model.search_read([])

user_model = connection.get_model('res.users')

app.debug = app.config['DEBUG']
    
Bootstrap(app)

#Set up attendance form
class AttendanceForm(Form):
	employee = TextField('Volunteer')
	work = RadioField(choices=[(department['id'], department['name']) for department in departments], coerce=int)
	action = HiddenField()

#Set up new volunteer form
class VolunteerForm(Form):
	name = TextField('Full Name')
	email = TextField('Email Address')
	phone = TextField('Phone #')
	street = TextField('Street Address')
	city = TextField('City')
	zip = TextField('Zip Code')
	username = TextField('Username/Login')
	password = PasswordField('Password')
	action = HiddenField()
	
#Display welcome/sign-in page at root of site
@app.route("/", methods=['GET', 'POST'])
def sign_in():
	today = str(date.today().strftime('%Y-%m-%d'))
	employees = employee_model.search_read([("active", "=", True)])
	print employees
	employees_signed_out = [('%s : %s' % (employee['id'], employee['name'])) for employee in employees if employee['state'] == 'absent']
	print employees_signed_out
	#Use the following for OpenERP v6.x
	#employees_signed_in = [{'id': employee['id'], 'photo': employee['photo'], 'name': employee['name']} for employee in employees if employee['state'] == 'present']
	#Use the following version for OpenERP v7
	employees_signed_in = [{'id': employee['id'], 'photo': employee['image_small'], 'name': employee['name']} for employee in employees if employee['state'] == 'present']
	for employee in employees_signed_in:
		current_work = timesheet_model.search_read([("date_from", "=", today), ("employee_id", "=", employee['id'])])
		if current_work:
			employee['work'] = current_work[0]['department_id'][1]
		
	#Generate attendance entry form (defined in TimesheetForm above)
	form = AttendanceForm(request.form)
	event = 0
	sheet = 0
		
	if request.method == 'POST':
		employee_id = int(request.form['employee'][:request.form['employee'].find(':')])
		current_timesheets = timesheet_model.search([("employee_id", "=", employee_id), ("date_from", "=", today)])
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
	
	return render_template('index.html', form=form, event=attendance_model.read(event), employees=employees, employees_signed_out=json.dumps(employees_signed_out), employees_signed_in=employees_signed_in, erp_db=app.config['ERP_DB'], erp_host=app.config['ERP_HOST'])

#Display new volunteer form
@app.route("/volunteer/new", methods=['GET', 'POST'])
def sign_up():
	employees = employee_model.search_read([("active", "=", True)])
	users = user_model.search_read([])
	form = VolunteerForm(request.form)
	
	if request.method == 'POST':
		#First, create the 'user', since the 'employee' record will link to this
		new_user = {
			'login' : request.form['username'],
			'password' : request.form['password'],
			'name' : request.form['name'],
			'email' : request.form['email'],
			'timezone' : 'America/Chicago'
		}
		user = user_model.create(new_user)
		
		#Then, create the 'employee' record, linking it to the just-created 'user' - this is required for timesheet entry
		new_employee = {
			'name' : request.form['name'],
			'work_email' : request.form['email'],
			'user_id' : user
		}
		employee = employee_model.create(new_employee)
			
	return render_template('signup.html', form=form, employees=employees)

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
	return redirect(url_for('sign_in'))

if __name__ == "__main__":
    app.run()
