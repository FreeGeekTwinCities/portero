import pkg_resources
pkg_resources.require("Flask")

from flask import Flask, render_template, request
from wtforms import Form, DateField, DecimalField, TextField, SelectField, validators
from proteus import config, Model
from datetime import date

config = config.set_trytond(database_name='test', user='admin', password='test')
print config

#Look up company model, and get name of first company - we'll use this for e.g. welcome page
Company = Model.get('company.company')
company = Company.find()[0].party.name

#Get Tryton models for later use
Work = Model.get('timesheet.work')
Employee = Model.get('company.employee')
TimesheetLine = Model.get('timesheet.line')

app = Flask(__name__)
app.debug = True

#Set up timesheet fields for later use
class TimesheetForm(Form):
	date = DateField('Date')
	hours = DecimalField('Hours')
	description = TextField('Description')
	employee = SelectField('Volunteer')
	work = SelectField('Work')

#Display welcome page at root of site
@app.route("/")
def hello():
	return render_template('hello.html', company=company)

@app.route("/timesheet", methods=['GET', 'POST'])
def enter_timesheet():
	#If there's POST data, construct & save a new timesheet line
	if request.method == 'POST':
		line = TimesheetLine()
		line.hours = float(request.form['hours'])
		line.description = request.form['description']
		line.work = Work(request.form['work'])
		line.employee = Employee(request.form['employee'])
		#line.date = date(request.form['date'])
		line.save()

	#Generate timesheet entry form (defined in TimesheetForm above)
	form = TimesheetForm(request.form)
	#Get list of available work types, and add them as options for "work" field on form
	form.work.choices = [(work.id, work.name) for work in Work.find()]
	#Get list of active volunteers/employees, and add these as options for "employee" field
	form.employee.choices = [(employee.id, employee.party.name) for employee in Employee.find([('company', '=', 1)])]

	#Finally, render timesheet page
	return render_template('timesheet.html', form=form, company=company)

@app.route("/transaction")
def enter_transaction():
	return "stub"
	
if __name__ == "__main__":
    app.run()
