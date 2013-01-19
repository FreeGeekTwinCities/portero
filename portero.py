import pkg_resources
pkg_resources.require("Flask")

from datetime import date, datetime, timedelta
from decimal import *

from flask import Flask, render_template, request, url_for, redirect, flash
from flask.ext.bootstrap import Bootstrap
from wtforms import Form, DateField, DateTimeField, DecimalField, HiddenField, TextField, SelectField, RadioField, PasswordField, validators

import json
import portero_config

app = Flask(__name__)
app.config.from_object('portero_config')
app.secret_key = app.config['SECRET_KEY']
	
import openerplib
connection = openerplib.get_connection(hostname=app.config['ERP_HOST'], database=app.config['ERP_DB'], login=app.config['ERP_USER'], password=app.config['ERP_PASSWORD'])

employee_model = connection.get_model("hr.employee")
employees = employee_model.search_read([("active", "=", True)])
employee_choices = [('%s : %s' % (employee['id'], employee['name'])) for employee in employees]

user_model = connection.get_model('res.users')
	
attendance_model = connection.get_model("hr.attendance")
timesheet_model = connection.get_model("hr_timesheet_sheet.sheet")

department_model = connection.get_model('hr.department')
departments = department_model.search_read([])

address_model = connection.get_model('res.partner')

app.debug = app.config['DEBUG']
    
Bootstrap(app)

#Set up new volunteer form
class VolunteerForm(Form):
	name = TextField('Full Name', [validators.Required()], description=u"Please enter your full name, first (given) name first, family (last) name last.")
	email = TextField('Email Address', [validators.Email(message='Please enter a valid email address')])
	phone = TextField('Phone #')
	street = TextField('Street Address')
	city = TextField('City')
	zip = TextField('Zip Code', [validators.Required()])
	username = TextField('Username/Login', [validators.Required(), validators.Length(min=3)])
	password = PasswordField('Password', [validators.Required(), validators.EqualTo('password_confirm', message='Passwords must match')], description=u"The default password is the one from the 'Need a Password' box below; remember this (or write it down), since it will also be your password for Moodle & discussion groups!")
	password_confirm = PasswordField('Repeat Password')
	emergency_contact_name = TextField('Name')
	emergency_contact_phone = TextField('Phone #')
	action = HiddenField()
	
#Display welcome/sign-in page at root of site
@app.route("/", methods=['GET', 'POST'])
def sign_in():
	today = str(date.today().strftime('%Y-%m-%d'))
	employees_signed_in = []
	employees = employee_model.search_read([("active", "=", True)])
	employee_choices = [('%s : %s' % (employee['id'], employee['name'])) for employee in employees]
		
	#Set up attendance form
	class AttendanceForm(Form):
		employee = TextField('Volunteer', [validators.Required(), validators.AnyOf(employee_choices, message='Please select a valid volunteer ID/name; if your name does not appear when you begin typing it, please check with a staffer or click the New Volunteer link above!')], description=u"Begin entering your name (first and/or last, not your username), then select your name & ID from the list; if you can't find it, please ask a staffer for help!")
		work = RadioField('What are you working on?', [validators.Required()], choices=[(department['id'], department['name']) for department in departments], coerce=int)
		action = HiddenField()

	#Generate attendance entry form (defined in TimesheetForm above)
	form = AttendanceForm(request.form)
	event = 0
	sheet = 0
	
	if request.method == 'POST' and form.validate():
		employee_id = int(request.form['employee'][:request.form['employee'].find(':')])
		employee = employee_model.search_read([("id", "=", employee_id)])[0]
		current_timesheets = timesheet_model.search_read([("employee_id", "=", employee_id), ("date_from", "=", today)])
		if len(current_timesheets) > 0:
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
		now = str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
		new_event = {
			'employee_id' : employee_id,
			'name' : now,
			'day' : today,
			'action' : 'sign_in',
			'sheet_id' : int(sheet['id'])
		}
		event = attendance_model.create(new_event)
		print event
		employees_signed_in.append({'id': employee_id, 'photo': employee['image_small'], 'name': employee['name']})
	
	attendances_today = attendance_model.search_read([('day', '=', today)])
	print attendances_today

	#timesheets_today = timesheet_model.search_read([("date_from", "=", today)])
	#print timesheets_today

	employees_signed_out = [('%s : %s' % (employee['id'], employee['name'])) for employee in employees if employee['state'] == 'absent']
	#print employees_signed_out
	
	#Use the following for OpenERP v6.x
	#employees_signed_in = [{'id': employee['id'], 'photo': employee['photo'], 'name': employee['name']} for employee in employees if employee['state'] == 'present']
	#Use the following version for OpenERP v7
	employees_signed_in.extend([{'id': employee['id'], 'photo': employee['image_small'], 'name': employee['name']} for employee in employees if employee['state'] == 'present'])
	#print employees_signed_in
	
	for employee in employees_signed_in:
		#print employee
		current_work = timesheet_model.search_read([("date_from", "=", today), ("employee_id", "=", employee['id'])])
		#print current_work
		if current_work:
			employee['work'] = current_work[0]['department_id'][1]
		else:
			employee['work'] = 'Unknown'
	#print employees_signed_in
		
	return render_template('index.html', form=form, event=attendance_model.read(event), employees=employees, employees_signed_out=json.dumps(employees_signed_out), employees_signed_in=employees_signed_in, erp_db=app.config['ERP_DB'], erp_host=app.config['ERP_HOST'], department_limits=app.config['DEPARTMENT_LIMITS'], department_index={department['name'] : department['id'] for department in departments})

#Display new volunteer form
@app.route("/volunteer/new", methods=['GET', 'POST'])
def sign_up():
	employees = employee_model.search_read([("active", "=", True)])
	users = user_model.search_read([])
	form = VolunteerForm(request.form)
	#print form.validate()
	
	if request.method == 'POST' and form.validate():
		#First, create the 'user', since the 'employee' record will link to this
		new_user = {
			'login' : request.form['username'],
			'password' : request.form['password'],
			'name' : request.form['name'],
			'email' : request.form['email'],
		}
		user = user_model.create(new_user)
		
		#Create an 'address' record to store the volunteer's address info
		new_address = {
			'name' : request.form['name'],
			'street' : request.form['street'],
			'city' : request.form['city'],
			'zip' : request.form['zip']
		}
		address = address_model.create(new_address)
		
		#Then, create the 'employee' record, linking it to the just-created 'user' - this is required for timesheet entry; also link to the home address
		new_employee = {
			'name' : request.form['name'],
			'work_email' : request.form['email'],
			'user_id' : user,
			'address_home_id' : address
		}
		employee = employee_model.create(new_employee)
		employee_choices = [('%s : %s' % (employee['id'], employee['name'])) for employee in employees]
		return render_template('signup.html', form=VolunteerForm(), new_volunteer=request.form['name'])
			
	return render_template('signup.html', form=form, users=[user['login'] for user in users], erp_db=app.config['ERP_DB'], erp_host=app.config['ERP_HOST'])

@app.route("/volunteer/sign_out", methods=['GET', 'POST'])
def sign_out():
	employee_id = request.args.get('volunteer_id')
	today = str(date.today().strftime('%Y-%m-%d'))
	now = str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
	new_event = {
		'employee_id' : employee_id,
		'name' : now,
		'day' : today,
		'action' : 'sign_out'
	}
	event = attendance_model.create(new_event)
	#print event
	return redirect(url_for('sign_in'))
	
@app.route("/volunteer/report", methods=['GET', 'POST'])
def volunteer_report():
	employee_id = request.args.get('id')
	employee_name = request.args.get('name')
	employee_key = [employee_id, employee_name]
	#print employees
	employee_photo = employee_model.search_read([("id", "=", employee_id)])[0]['image_small']
	timesheet_lines = timesheet_model.search_read([("employee_id", "=", employee_key)])
	return render_template('timesheet_report.html', timesheet_lines=timesheet_lines, employee_photo=employee_photo, erp_db=app.config['ERP_DB'], erp_host=app.config['ERP_HOST'])

if __name__ == "__main__":
    app.run()
