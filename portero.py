import pkg_resources
pkg_resources.require("Flask")

from flask import Flask, render_template, request, url_for, redirect
from flask.ext.bootstrap import Bootstrap
from wtforms import Form, DateField, DecimalField, TextField, SelectField, validators
from proteus import config, Model
from datetime import date, datetime

config = config.set_trytond(database_name='test', user='admin', password='test')
print config

#Look up company model, and get name of first company - we'll use this for e.g. welcome page
Company = Model.get('company.company')
company = Company.find()[0].party.name

#Get Tryton models for later use
Work = Model.get('timesheet.work')
Employee = Model.get('company.employee')
TimesheetLine = Model.get('timesheet.line')
Sale = Model.get('sale.sale')
Purchase = Model.get('purchase.purchase')
Party = Model.get('party.party')

app = Flask(__name__)
app.debug = True
Bootstrap(app)

#Set up timesheet fields for later use
class TimesheetForm(Form):
	date = DateField('Date')
	hours = DecimalField('Hours')
	description = TextField('Description')
	employee = SelectField('Volunteer')
	work = SelectField('Work')

#Set up transaction fields
class DonationForm(Form):
	transaction_type = SelectField('Volunteer', choices=[('sale', 'Sale'), ('purchase', 'Donation')])
	date = DateField('Date')
	hours = DecimalField('Hours')
	description = TextField('Description')
	party = SelectField('Donor')
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
		line.date = datetime.strptime(request.form['date'], "%m/%d/%Y").date()
		print line
		line.save()
		return redirect(url_for('timesheet_report', volunteer_id=request.form['employee'], name=line.employee.name, work=line.work.name, ))

	else:
		#Generate timesheet entry form (defined in TimesheetForm above)
		form = TimesheetForm(request.form)
		#Get list of available work types, and add them as options for "work" field on form
		form.work.choices = [(work.id, work.name) for work in Work.find()]
		#Get list of active volunteers/employees, and add these as options for "employee" field
		form.employee.choices = [(employee.id, employee.party.name) for employee in Employee.find([('company', '=', 1)])]

		#Finally, render timesheet page
		return render_template('timesheet.html', form=form, company=company)

@app.route("/timesheet/volunteer/<int:volunteer_id>")
def timesheet_report(volunteer_id):
	timesheet_lines = [(timesheet_line.date, timesheet_line.hours, timesheet_line.work.name, timesheet_line.description) for timesheet_line in TimesheetLine.find([('employee', '=', volunteer_id)])]
	return render_template('timesheet_report.html', timesheet_lines=timesheet_lines)

@app.route("/donation")
def enter_donation():
	
	#Generate timesheet entry form (defined in TimesheetForm above)
	form = DonationForm(request.form)
	#Get list of active parties, and add these as options for "party" field
	form.party.choices = [(party.id, party.name) for party in Party.find()]

	#Finally, render timesheet page
	return render_template('donation.html', form=form, company=company)
	
if __name__ == "__main__":
    app.run()
