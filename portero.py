import pkg_resources
pkg_resources.require("Flask")

from flask import Flask, render_template, request
from wtforms import Form, DateField, DecimalField, TextField, SelectField, validators
from proteus import config, Model
 
config = config.set_trytond(database_name='test', user='admin', password='test')
print config

Company = Model.get('company.company')
company = Company.find()[0].party.name

Work = Model.get('timesheet.work')
	
Employee = Model.get('company.employee')

TimesheetLine = Model.get('timesheet.line')

app = Flask(__name__)
app.debug = True

class TimesheetForm(Form):
	date = DateField('Date')
	hours = DecimalField('Hours')
	description = TextField('Description')
	employee = SelectField('Volunteer')
	work = SelectField('Work')

@app.route("/")
def hello():
	return render_template('hello.html', company=company)

@app.route("/timesheet", methods=['GET', 'POST'])
def enter_timesheet():
	if request.method == 'POST':
		line = TimesheetLine()
		print line.__dict__
		line.save()

	form = TimesheetForm(request.form)
	form.work.choices = [(work.id, work.name) for work in Work.find()]
	form.employee.choices = [(employee.id, employee.party.name) for employee in Employee.find([('company', '=', 1)])]

	return render_template('timesheet.html', form=form, company=company)

@app.route("/transaction")
def enter_transaction():
	return "stub"
	
if __name__ == "__main__":
    app.run()
