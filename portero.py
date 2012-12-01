import pkg_resources
pkg_resources.require("Flask")

from flask import Flask, render_template, request, url_for, redirect
from flask.ext.bootstrap import Bootstrap
from wtforms import Form, DateField, DecimalField, TextField, SelectField, validators
from proteus import config as tryton_config, Model
from datetime import date, datetime
from decimal import *
import json
import portero_config

app = Flask(__name__)
app.config.from_object('portero_config')
print app.config
app.debug = app.config['DEBUG']
Bootstrap(app)

tryton_config = tryton_config.set_trytond(database_name=app.config['TRYTON_DB'], user=app.config['TRYTON_USER'], password=app.config['TRYTON_PASSWORD'])
print tryton_config

#Look up company model, and get name of first company - we'll use this for e.g. welcome page
Company = Model.get('company.company')
company = Company.find()[0].party
company_address = company.addresses[0]

#Get Tryton models for later use
Work = Model.get('timesheet.work')
Works = [(work.id, work.name) for work in Work.find()]
Employee = Model.get('company.employee')
Employees = [(employee.id, employee.party.name) for employee in Employee.find([('company', '=', 1)])]
TimesheetLine = Model.get('timesheet.line')
Sale = Model.get('sale.sale')
Purchase = Model.get('purchase.purchase')
Party = Model.get('party.party')
Parties = [('%s : %s' % (party.id, party.name)) for party in Party.find()]
Product = Model.get('product.product')
Products = [(product.id, product.template.name) for product in Product.find()]
PurchaseLine = Model.get('purchase.line')
Currency = Model.get('currency.currency')
Unit = Model.get('product.uom')

#Set up timesheet fields for later use
class TimesheetForm(Form):
	date = DateField('Date', [validators.Required()])
	hours = DecimalField('Hours', [validators.NumberRange(min=0.25, max=24, message='Please enter the number of hours you worked.')])
	description = TextField('Description', [validators.Optional()])
	employee = SelectField('Volunteer', [validators.Required()], choices=Employees, coerce=int)
	work = SelectField('Work', [validators.Required()], choices=Works, coerce=int)

#Set up transaction (donation/sale) fields
class TransactionForm(Form):
	description = TextField('Description')
	party = TextField('Donor')
	date = DateField('Date')
	item1_quantity = DecimalField('Number Donated')
	item1_type = SelectField('Item Type', [validators.Required()], choices=Products, coerce=int)
	item1_description = TextField('Item Description')

#Display welcome page at root of site
@app.route("/")
def hello():
	return render_template('hello.html', company=company)

@app.route("/timesheet", methods=['GET', 'POST'])
def enter_timesheet():
	#Generate timesheet entry form (defined in TimesheetForm above)
	form = TimesheetForm(request.form)
	
	#If there's POST data, construct & save a new timesheet line
	if request.method == 'POST' and form.validate():
		line = TimesheetLine()
		line.hours = float(request.form['hours'])
		line.description = request.form['description']
		line.work = Work(request.form['work'])
		line.employee = Employee(request.form['employee'])
		line.date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
		line.save()
		return redirect(url_for('timesheet_report', volunteer_id=request.form['employee'], name=line.employee.name, work=line.work.name, ))

	#Finally, render timesheet page
	return render_template('timesheet.html', form=form, company=company)

@app.route("/timesheet/volunteer/<int:volunteer_id>")
def timesheet_report(volunteer_id):
	timesheet_lines = [timesheet_line for timesheet_line in TimesheetLine.find([('employee', '=', volunteer_id)])]
	return render_template('timesheet_report.html', timesheet_lines=timesheet_lines)

@app.route("/donation", methods=['GET', 'POST'])
def enter_donation():
	#Generate donation entry form (defined above)
	form = TransactionForm(request.form)

	if request.method == 'POST':
		donation = Purchase()
		if ':' in request.form['party']:
			donation.party = Party(int(request.form['party'][:request.form['party'].find(':')]))
		else:
			new_party = Party()
			new_party.name = request.form['party']
			new_party.save()
			donation.party = new_party
		donation.purchase_date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
		donation.currency = Currency(152)
		donation.save()
		
		#Once donation has been created add item 'line' to it
		donation_line = donation.lines.new()
		donation_line.purchase = Purchase(donation.id)
		donation_line.type = 'line' 
		donation_line.quantity = Decimal(request.form['item1_quantity'])
		donation_line.product = Product(int(request.form['item1_type']))
		donation_line.description = donation_line.product.name
		donation_line.unit = Unit(1)
		donation_line.unit_price = donation_line.product.cost_price
		donation_line.save()
		return redirect(url_for('donation_receipt', donation_id=donation.id))
		
	#Finally, render donation page
	return render_template('transaction.html', form=form, transaction_type='donation', company=company, parties=json.dumps(Parties))
	
@app.route("/donation/receipt/<int:donation_id>")
def donation_receipt(donation_id):
	donation = Purchase(donation_id)
	return render_template('receipt.html', company=company, company_address=company_address, transaction=donation, date=donation.purchase_date, transaction_type='Donation')

@app.route("/sale", methods=['GET', 'POST'])
def enter_sale():
	#Generate sale entry form (defined above)
	form = TransactionForm(request.form)

	if request.method == 'POST':
		sale = Sale()
		if ':' in request.form['party']:
			sale.party = Party(int(request.form['party'][:request.form['party'].find(':')]))
		else:
			new_party = Party()
			new_party.name = request.form['party']
			new_party.save()
			sale.party = new_party
		sale.sale_date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
		sale.save()
		
		#Once parent 'sale' has been created add item 'line' to it
		sale_line = sale.lines.new()
		sale_line.sale = Sale(sale.id)
		sale_line.type = 'line' 
		sale_line.quantity = Decimal(request.form['item1_quantity'])
		sale_line.product = Product(int(request.form['item1_type']))
		if request.form['item1_description']:
			sale_line.description = '%s - %s' % (sale_line.product.name, request.form['item1_description'])
		else:
			sale_line.description = sale_line.product.name
		sale_line.unit = Unit(1)
		sale_line.unit_price = sale_line.product.list_price
		sale_line.save()
		return redirect(url_for('sale_receipt', sale_id=sale.id))
		
	#Finally, render sale page
	return render_template('transaction.html', form=form, transaction_type='sale', company=company, parties=json.dumps(Parties))
	
@app.route("/sale/receipt/<int:sale_id>")
def sale_receipt(sale_id):
	sale = Sale(sale_id)
	return render_template('receipt.html', company=company, company_address=company_address, transaction=sale, date=sale.sale_date, transaction_type='Sale')

if __name__ == "__main__":
    app.run()
