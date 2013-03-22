"""
Portero is Free Geek Twin Cities volunteer time management system that
uses Open ERP as its back end.
"""
import pkg_resources
pkg_resources.require("Flask")

# Libraries
import sys
import os
from datetime import date, datetime, timedelta
from decimal import *
from flask import Flask, render_template, request, url_for, redirect, flash, Response
from flask.ext.bootstrap import Bootstrap
from wtforms import Form, DateField, DateTimeField, DecimalField, HiddenField, TextField, SelectField, RadioField, PasswordField, validators
import json
import portero_config
import logging
import csv
import openerplib


# Create and configure Flask
app = Flask(__name__)
app.config.from_object('portero_config')
app.secret_key = app.config['SECRET_KEY']
Bootstrap(app)


# Logging
app.debug = app.config['DEBUG']
if app.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
    #from logging.handlers import SMTPHandler
    #mail_handler = SMTPHandler(app.config['SMTP_HOST'], app.config['SMTP_USER'], app.config['ADMINS'], 'Portero Error')
    #mail_handler.setLevel(logging.ERROR)
    #app.logger.addHandler(mail_handler)
    from logging.handlers import TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler(app.config['LOG_FILE'], when='midnight', interval=1, backupCount=7)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    #from logging.handlers import SysLogHandler
    #syslog_handler = SysLogHandler()
    #app.logger.addHandler(syslog_handler)


# Connect to OpenERP
connection = openerplib.get_connection(hostname=app.config['ERP_HOST'], database=app.config['ERP_DB'], login=app.config['ERP_USER'], password=app.config['ERP_PASSWORD'])

# Models
employee_model = connection.get_model('hr.employee')
user_model = connection.get_model('res.users')
attendance_model = connection.get_model('hr.attendance')
timesheet_model = connection.get_model('hr_timesheet_sheet.sheet')
department_model = connection.get_model('hr.department')
address_model = connection.get_model('res.partner')

# Consistent sets
departments = department_model.search_read([])


##
# Main routes
#
##

# Display welcome/sign-in page at root of site
@app.route("/", methods=['GET', 'POST'])
def sign_in():
    today = str(date.today().strftime('%Y-%m-%d'))
    employees_signed_in = []
    employees = employee_model.search_read(domain=[("active", "=", True)], fields=['id', 'name', 'state', 'image_small', 'work'])
    employee_choices = [('%s : %s' % (employee['id'], employee['name'])) for employee in employees]
    signed_in = False
    event = 0
    sheet = 0

    # Set up attendance form
    class AttendanceForm(Form):
        employee = TextField('Volunteer', [
            validators.Required(),
            validators.AnyOf(employee_choices, message=u'Please select a valid volunteer ID/name; if your name does not appear when you begin typing it, please check with a staffer or click the New Volunteer link above!')],
            description=u'Begin entering your name (first and/or last, not your username), then select your name & ID from the list; if you can\'t find it, please ask a staffer for help!')

        work = RadioField('What are you working on?', [validators.Required()],
                          choices=[(department['id'],
                          department['name']) for department in departments], coerce=int)
        action = HiddenField()

    # Generate attendance entry form (defined in TimesheetForm above)
    form = AttendanceForm(request.form)

    # Sign in user if form is validated and submitted
    if request.method == 'POST' and form.validate():
        employee_id = int(request.form['employee'][:request.form['employee'].find(':')])
        department_id = request.form['work']
        employee = get_volunteer(employee_id)
        sign_in_event = volunteer_sign_in(employee_id, department_id)
        employees_signed_in.append({'id': employee_id, 'photo': employee['image_small'], 'name': employee['name']})
        signed_in = True

  # Get employees that are signed in and signed out
    employees_signed_out = [('%s : %s' % (employee['id'], employee['name'])) for employee in employees if employee['state'] == 'absent']
    employees_signed_in.extend([{'id': employee['id'], 'photo': employee['image_small'], 'name': employee['name']} for employee in employees if employee['state'] == 'present'])

    # Determine current department for signed in employees
    for employee in employees_signed_in:
        current_work = get_current_timesheet(employee['id'], False)
        if current_work:
            employee['work'] = current_work['department_id'][1]
        else:
            employee['work'] = 'Unknown'

  # Return template
    return render_template(
        'index.html',
        form=form,
        event=attendance_model.read(event),
        employees=employees,
        employees_signed_out=json.dumps(employees_signed_out),
        employees_signed_in=employees_signed_in,
        erp_db=app.config['ERP_DB'],
        erp_host=app.config['ERP_HOST'],
        department_limits=app.config['DEPARTMENT_LIMITS'],
        department_index={department['name']: department['id'] for department in departments},
        signed_in=signed_in)


# Display new volunteer form
@app.route("/volunteer/new", methods=['GET', 'POST'])
def sign_up():
    # employees = get_volunteers()
    users = get_users()
    new_volunteer = False

    # Set up new volunteer form
    class VolunteerForm(Form):
        name = TextField('Full Name', [validators.Required()],
                         description=u"Please enter your full name, first (given) name first, family (last) name last.")
        email = TextField('Email Address',
                          [validators.Email(message='Please enter a valid email address')])
        phone = TextField('Phone #')
        street = TextField('Street Address')
        city = TextField('City')
        zip = TextField('Zip Code', [validators.Required()])
        username = TextField('Username/Login',
                             [validators.Required(), validators.Length(min=3),
                             validators.NoneOf([user['login'] for user in users],
                             message="Username is already in use, please choose another")])
        password = PasswordField('Password',
                                 [validators.Required(), validators.EqualTo('password_confirm',
                                 message='Passwords must match')],
                                 description=u"The default password is the one from the 'Need a Password' box below; remember this (or write it down), since it will also be your password for Moodle & discussion groups!")
        password_confirm = PasswordField('Repeat Password')
        emergency_contact_name = TextField('Name')
        emergency_contact_phone = TextField('Phone #')
        action = HiddenField()

    form = VolunteerForm(request.form)
    # If form validates and is submitted create new volunteer
    if request.method == 'POST' and form.validate():
        # First, create the 'user', since the 'employee' record will link to this
        user = create_user(request.form['username'], request.form['password'],
                           request.form['name'], request.form['email'])

        # Create an 'address' record to store the volunteer's address info
        address = create_address(request.form['name'], request.form['street'],
                                 request.form['city'], request.form['zip'])

        # Create the 'employee' record, linking it to the just-created 'user'.
        # this is required for timesheet entry; also link to the home address
        employee = create_volunteer(request.form['name'], request.form['email'], user, address)

        # Try to import attendances for the newly-created username
        import_ledger_data(request.form['username'])

        # Template values
        new_volunteer = request.form['name']

    return render_template('signup.html', form=form,
                           new_volunteer=new_volunteer, users=[user['login'] for user in users],
                           erp_db=app.config['ERP_DB'], erp_host=app.config['ERP_HOST'])


# Volunteer list
@app.route("/volunteers", methods=['GET'])
def volunteers_page():
    volunteers = get_volunteers()

    return render_template('volunteers.html',
                           volunteers=volunteers,
                           erp_db=app.config['ERP_DB'], erp_host=app.config['ERP_HOST'])


# Volunteer report page, number of hours
@app.route("/volunteer/report", methods=['GET', 'POST'])
def volunteer_report():
    employee = get_volunteer(request.args.get('id'))
    timesheets = get_timesheets(request.args.get('id'))

    return render_template('timesheet_report.html',
                           timesheet_lines=timesheets,
                           employee=employee,
                           employee_photo=employee['image_small'],
                           erp_db=app.config['ERP_DB'],
                           erp_host=app.config['ERP_HOST'])


# Sign out user, then redirect to index page
@app.route("/volunteer/sign_out", methods=['GET', 'POST'])
def sign_out():
    volunteer_sign_out(request.args.get('volunteer_id'))
    return redirect(url_for('sign_in'))


# Import timesheets from CSV
@app.route("/timesheets/import", methods=['GET', 'POST'])
def timesheet_import():
    employee = get_volunteer(request.args.get('new_id'))
    old_id = request.args.get('old_id')


##
# RESTful API routes
#
##

# Get non-sensitive config data
@app.route('/api/config', methods=['GET'])
def api_config_get():
    config = app.config
    config.pop('PERMANENT_SESSION_LIFETIME', 0)
    config.pop('ERP_PASSWORD', 0)
    config.pop('ERP_USER', 0)
    return output_json(config)


# Get all volunteers.  Careful because images are output as blob data.
@app.route('/api/volunteers', methods=['GET'])
def api_volunteers_get():
    e = employee_model.search_read()
    return output_json(e)


# Add volunteer
@app.route('/api/volunteer/add', methods=['POST'])
def api_volunteers_add():
    return output_json('')


# Get volunteer
@app.route('/api/volunteer/<int:volunteer_id>', methods=['GET'])
def api_volunteer_get(volunteer_id):
    v = get_volunteer(volunteer_id)
    return output_json(v)


# Sign in volunteer to specific department
@app.route('/api/volunteer/sign_in/<int:volunteer_id>/<int:department_id>', methods=['POST'])
def api_volunteer_sign_in(volunteer_id, department_id):
    s = volunteer_sign_in(volunteer_id, department_id)
    return output_json(s)


# Sign out a volunteer
@app.route('/api/volunteer/sign_out/<int:volunteer_id>', methods=['POST'])
def api_volunteer_sign_out(volunteer_id):
    s = volunteer_sign_out(volunteer_id)
    return output_json(s)


# Get departments
@app.route('/api/departments', methods=['GET'])
def api_departments():
    d = department_model.search_read([])
    return output_json(d)


# Get timesheet data for volunteer
@app.route('/api/timesheet/<int:volunteer_id>', methods=['GET'])
def api_timesheet(volunteer_id):
    t = get_timesheets_from_id(volunteer_id)
    return output_json(t)


##
# Helper functions
#
##

# Wrapper for json since Flask's jsonify is weird
def output_json(data):
    return Response(json.dumps(data), mimetype='application/json')


# Get active volunteers
def get_volunteers():
    return employee_model.search_read(domain=[('active', '=', True)], fields=[])


# Get system users
def get_users():
    return user_model.search_read(domain=[], fields=['login', 'label'])


# Get volunteer
def get_volunteer(volunteer_id):
    return employee_model.search_read([('id', '=', volunteer_id)])[0]


# Get timesheets object, from employee ID
def get_timesheets(employee_id):
    v = get_volunteer(employee_id)
    key = [employee_id, v['name']]
    return timesheet_model.search_read([('employee_id', '=', key)])


# Get timesheets object only from employee ID
#
# For whatever reason, the search works with the key
# but not always.  WTF.
def get_timesheets_from_id(employee_id):
    return timesheet_model.search_read([('employee_id', '=', employee_id)])


# Create new user
def create_user(username, password, name, email):
    new_user = {
        'login': username,
        'password': password,
        'name': name,
        'email': email,
    }
    return user_model.create(new_user)


# Create address.  Name should be a valid "name" of a real user
def create_address(name, street, city, zipcode):
    if name:
        new_address = {
            'name': name,
            'street': street,
            'city': city,
            'zip': zipcode
        }
        return address_model.create(new_address)
    else:
        return False


# Create new employee record
def create_volunteer(name, email, user_id, address_id):
    new_employee = {
        'name': name,
        'work_email': email,
        'user_id': user_id,
        'address_home_id': address_id
    }
    return employee_model.create(new_employee)


# Signout volunteer, given ID
def volunteer_sign_out(volunteer_id, event_day=False, event_time=False):
	if not (event_day and event_time):
		event_day = str(date.today().strftime('%Y-%m-%d')),
		event_time = str(datetime.utcnow().strftime('%H:%M:%S'))
	event_entry = {
        'employee_id': volunteer_id,
        'name': '%s %s' % (event_day, event_time),
        'day': event_day,
        'action': 'sign_out'
	}
	return attendance_model.create(event_entry)


# Sign in volunteer, given ID and department
def volunteer_sign_in(volunteer_id, department_id, event_day=False, event_time=False):
    timesheet = get_current_timesheet(volunteer_id, department_id)
    if not (event_day and event_time):
		event_day = str(date.today().strftime('%Y-%m-%d')),
		event_time = str(datetime.utcnow().strftime('%H:%M:%S'))
    new_event = {
        'employee_id': volunteer_id,
        'name': '%s %s' % (event_day, event_time),
        'day': event_day,
        'action': 'sign_in',
        'sheet_id': timesheet['id']
    }
    return attendance_model.create(new_event)


# Get current timesheet.  Returns sheet object
def get_current_timesheet(volunteer_id, department_id):
    today = str(date.today().strftime('%Y-%m-%d'))
    timesheets = timesheet_model.search_read([('employee_id', '=', volunteer_id), ('date_from', '=', today)])

    # If there are no current timesheets and a department id given, make one
    if len(timesheets) > 0:
        return timesheets[0]
    elif department_id:
        new_sheet = {
            'employee_id': volunteer_id,
            'company_id': 1,
            'date_from': today,
            'date_current': today,
            'date_to': today,
            'department_id': department_id,
        }
        # This returns the timesheet ID, not the timesheet object
        sheet_id = timesheet_model.create(new_sheet)
        return timesheet_model.search_read([('id', '=', sheet_id)])[0]
    else:
        return False


# Import data from couch/ledger legacy system
def import_timesheets(old_user, new_user):
	my_timesheets = get_timesheets(new_user)
        with open(app.config['TIMESHEET_IMPORT_FILE'], 'rb') as csvfile:
		timesheet_reader = csv.DictReader(csvfile)
		for row in timesheet_reader:
			if row['volunteer'] == old_user:
				for department in departments:
					if department['name'] == row['work']:
						work_id = department['id']
				volunteer_sign_out(new_user, event_day=timesheet_date, event_time=timesheet_sign_out)
				volunteer_sign_in(new_user, work_id, event_day=timesheet_date, event_time=timesheet_sign_in)


# Main application.
if __name__ == "__main__":
    try:
        app.run()
    except:
        logging.error("Unexpected error:", sys.exc_info()[0])
        raise
