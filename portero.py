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
employees = employee_model.search_read([("active", "=", True)])
print employees

employees_signed_out = [('%s : %s' % (employee['id'], employee['name'])) for employee in employees]
print employees_signed_out

attendance_model = connection.get_model("hr.attendance")
print attendance_model
attendances_today = attendance_model.search_read([('day', '=', str(date.today().strftime('%Y-%m-%d')))])
#attendances = attendance_model.search_read([])
print attendances_today

timesheet_model = connection.get_model("hr_timesheet_sheet.sheet")
print timesheet_model
timesheets = timesheet_model.search_read([])
print timesheets

analytic_model = connection.get_model('account.analytic.account')
print analytic_model
analytic_accounts = analytic_model.search_read([])
for account in analytic_accounts:
	print account['name']
	
department_model = connection.get_model('hr.department')
print department_model
departments = department_model.search_read([])
print departments

app.debug = app.config['DEBUG']
    
Bootstrap(app)

#Set up attendance form
class AttendanceForm(Form):
	employee = TextField('Volunteer')
	work = RadioField(choices=[(department['id'], department['name']) for department in departments], coerce=int)
	action = HiddenField()
	
##Display welcome page at root of site
@app.route("/", methods=['GET', 'POST'])
def hello():
	#Generate attendance entry form (defined in TimesheetForm above)
	form = AttendanceForm(request.form)
	event = 0
	sheet = 0
		
	if request.method == 'POST':
		employee_id = int(request.form['employee'][:request.form['employee'].find(':')])
		today = str(date.today().strftime('%Y-%m-%d'))
		new_sheet = {
			'employee_id' : employee_id,
			'company_id' : 1,
			'date_from' : today,
			'date_to' : today,
			'department_id' : 1,
		}
		sheet = timesheet_model.create(new_sheet)
		print sheet
		new_event = {
			'emp_id' : employee_id,
			'name' : '2012-12-06 01:24:29',
			'day' : today,
			'action' : 'sign_in',
			'sheet_id' : sheet
		}
		event = attendance_model.create(new_event)
		print event
	
	return render_template('hello.html', form=form, event=attendance_model.read(event), employees=employees, employees_signed_out=json.dumps(employees_signed_out))

#@app.route("/timesheet", methods=['GET', 'POST'])
#def enter_timesheet():
	##Generate timesheet entry form (defined in TimesheetForm above)
	#form = TimesheetForm(request.form)
	
	##If there's POST data, construct & save a new timesheet line
	#if request.method == 'POST':
		#line = TimesheetLine()
		#line.hours = float(request.form['hours'])
		#line.description = request.form['description']
		#line.work = Work(request.form['work'])
		#employee_id = int(request.form['employee'][:request.form['employee'].find(':')])
		#print employee_id
		#line.employee = Employee(employee_id)
		#print line.employee
		#line.date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
		#line.save()
		#return redirect(url_for('timesheet_report', volunteer_id=line.employee.id, name=line.employee.name, work=line.work.name))

	##Finally, render timesheet page
	#return render_template('timesheet.html', form=form, company=company, employees=json.dumps(Employees))

#@app.route("/timesheet/volunteer/<int:volunteer_id>")
#def timesheet_report(volunteer_id):
	#timesheet_lines = [timesheet_line for timesheet_line in TimesheetLine.find([('employee', '=', volunteer_id)])]
	#return render_template('timesheet_report.html', timesheet_lines=timesheet_lines)

#@app.route("/donation", methods=['GET', 'POST'])
#def enter_donation():
	##Generate donation entry form (defined above)
	#form = TransactionForm(request.form)

	#if request.method == 'POST':
		#donation = Purchase()
		#if ':' in request.form['party']:
			#donation.party = Party(int(request.form['party'][:request.form['party'].find(':')]))
		#else:
			#new_party = Party()
			#new_party.name = request.form['party']
			#new_party.save()
			#donation.party = new_party
		#donation.purchase_date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
		#donation.currency = Currency(152)
		#donation.save()
		#donation.state = 'confirmed'
		#donation.save()
		
		##Once donation has been created add item 'line' to it
		#for line_num in range(1, 6):
			#if request.form['item%s_quantity' % line_num]:
				#donation_line = donation.lines.new()
				#donation_line.purchase = Purchase(donation.id)
				#donation_line.type = 'line' 
				#donation_line.quantity = Decimal(request.form['item%s_quantity' % line_num])
				#donation_line.product = Product(int(request.form['item%s_type' % line_num]))
				#if request.form['item%s_description' % line_num]:
					#donation_line.description = '%s - %s' % (donation_line.product.name, request.form['item%s_description' % line_num])
				#else:
					#donation_line.description = donation_line.product.name
				#donation_line.unit = Unit(1)
				#donation_line.unit_price = donation_line.product.cost_price
				#donation_line.save()
				
		#return redirect(url_for('donation_receipt', donation_id=donation.id))
		
	##Finally, render donation page
	#return render_template('transaction.html', form=form, transaction_type='donation', company=company, parties=json.dumps(Parties))
	
#@app.route("/donation/receipt/<int:donation_id>")
#def donation_receipt(donation_id):
	#donation = Purchase(donation_id)
	#return render_template('receipt.html', company=company, company_address=company_address, transaction=donation, date=donation.purchase_date, transaction_type='donation', product_prices=json.dumps(product_prices))

#@app.route("/sale", methods=['GET', 'POST'])
#def enter_sale():
	##Generate sale entry form (defined above)
	#form = TransactionForm(request.form)

	#if request.method == 'POST':
		#sale = Sale()
		#if ':' in request.form['party']:
			#sale.party = Party(int(request.form['party'][:request.form['party'].find(':')]))
		#else:
			#new_party = Party()
			#new_party.name = request.form['party']
			#new_party.save()
			#sale.party = new_party
		#sale.sale_date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
		#sale.save()
		#sale.state = 'confirmed'
		#sale.save()
		
		##Once parent 'sale' has been created, add item 'lines' to it
		#for line_num in range(1, 6):
			#if request.form['item%s_quantity' % line_num]:
				#sale_line = sale.lines.new()
				#sale_line.sale = Sale(sale.id)
				#sale_line.type = 'line' 
				#sale_line.quantity = Decimal(request.form['item%s_quantity' % line_num])
				#sale_line.product = Product(int(request.form['item%s_type' % line_num]))
				#if request.form['item%s_description' % line_num]:
					#sale_line.description = '%s - %s' % (sale_line.product.name, request.form['item%s_description' % line_num])
				#else:
					#sale_line.description = sale_line.product.name
				#sale_line.unit = Unit(1)
				#sale_line.unit_price = Decimal(request.form['item%s_price' % line_num])
				#sale_line.save()
		#return redirect(url_for('sale_receipt', sale_id=sale.id))
		
	##Finally, render sale page
	#return render_template('transaction.html', form=form, transaction_type='sale', company=company, parties=json.dumps(Parties), product_prices=json.dumps(product_prices))
	
#@app.route("/sale/receipt/<int:sale_id>")
#def sale_receipt(sale_id):
	#sale = Sale(sale_id)
	#return render_template('receipt.html', company=company, company_address=company_address, transaction=sale, date=sale.sale_date, transaction_type='Sale')

if __name__ == "__main__":
    app.run()
