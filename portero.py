import pkg_resources
pkg_resources.require("Flask")

from flask import Flask, render_template, request, url_for, redirect
from flask.ext.bootstrap import Bootstrap
from wtforms import Form, DateField, DecimalField, TextField, SelectField, RadioField, validators
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

#Look up company model, and get name of first company - we'll use this for e.g. welcome page
Company = Model.get('company.company')
company = Company.find()[0].party
company_address = company.addresses[0]

#Get Tryton models for later use
Work = Model.get('timesheet.work')
Works = [(work.id, work.name) for work in Work.find()]
Employee = Model.get('company.employee')
Employees = [('%s : %s' % (employee.id, employee.party.name)) for employee in Employee.find([('company', '=', 1)])]
TimesheetLine = Model.get('timesheet.line')
Sale = Model.get('sale.sale')
Purchase = Model.get('purchase.purchase')
Party = Model.get('party.party')
Parties = [('%s : %s' % (party.id, party.name)) for party in Party.find()]
Product = Model.get('product.product')
product_list = Product.find()
products = [(product.id, product.template.name) for product in product_list]
product_prices = [(product.id, float(product.list_price)) for product in product_list]
PurchaseLine = Model.get('purchase.line')
Currency = Model.get('currency.currency')
Unit = Model.get('product.uom')

#Set up timesheet fields for later use
class TimesheetForm(Form):
	date = DateField('Date', [validators.Required()])
	hours = DecimalField('Hours', [validators.NumberRange(min=0.25, max=24, message='Please enter the number of hours you worked.')])
	description = TextField('Description', [validators.Optional()])
	employee = TextField('Volunteer')
	work = RadioField('Work', [validators.Required()], choices=Works, coerce=int)

#Set up transaction (donation/sale) fields
class TransactionForm(Form):
	description = TextField('Description')
	party = TextField('Donor/Purchaser')
	date = DateField('Date')
	#TODO: find a better way to create multiple lines/fields!
	item1_quantity = DecimalField('Number of Items')
	item1_type = SelectField('Item Type', choices=products, coerce=int)
	item1_price = DecimalField('Unit Price')
	item1_description = TextField('Item Description', [validators.Optional()])
	item2_quantity = DecimalField('Number of Items', [validators.Optional()])
	item2_type = SelectField('Item Type', choices=products, coerce=int)
	item2_price = DecimalField('Unit Price')
	item2_description = TextField('Item Description', [validators.Optional()])
	item3_quantity = DecimalField('Number of Items', [validators.Optional()])
	item3_type = SelectField('Item Type', choices=products, coerce=int)
	item3_price = DecimalField('Unit Price')
	item3_description = TextField('Item Description', [validators.Optional()])
	item4_quantity = DecimalField('Number of Items', [validators.Optional()])
	item4_type = SelectField('Item Type', choices=products, coerce=int)
	item4_price = DecimalField('Unit Price')
	item4_description = TextField('Item Description', [validators.Optional()])
	item5_quantity = DecimalField('Number of Items', [validators.Optional()])
	item5_type = SelectField('Item Type', choices=products, coerce=int)
	item5_price = DecimalField('Unit Price')
	item5_description = TextField('Item Description', [validators.Optional()])
	
#Display welcome page at root of site
@app.route("/")
def hello():
	return render_template('hello.html', company=company)

@app.route("/timesheet", methods=['GET', 'POST'])
def enter_timesheet():
	#Generate timesheet entry form (defined in TimesheetForm above)
	form = TimesheetForm(request.form)
	
	#If there's POST data, construct & save a new timesheet line
	if request.method == 'POST':
		line = TimesheetLine()
		line.hours = float(request.form['hours'])
		line.description = request.form['description']
		line.work = Work(request.form['work'])
		employee_id = int(request.form['employee'][:request.form['employee'].find(':')])
		print employee_id
		line.employee = Employee(employee_id)
		print line.employee
		line.date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
		line.save()
		return redirect(url_for('timesheet_report', volunteer_id=line.employee.id, name=line.employee.name, work=line.work.name))

	#Finally, render timesheet page
	return render_template('timesheet.html', form=form, company=company, employees=json.dumps(Employees))

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
		donation.state = 'confirmed'
		donation.save()
		
		#Once donation has been created add item 'line' to it
		for line_num in range(1, 6):
			if request.form['item%s_quantity' % line_num]:
				donation_line = donation.lines.new()
				donation_line.purchase = Purchase(donation.id)
				donation_line.type = 'line' 
				donation_line.quantity = Decimal(request.form['item%s_quantity' % line_num])
				donation_line.product = Product(int(request.form['item%s_type' % line_num]))
				if request.form['item%s_description' % line_num]:
					donation_line.description = '%s - %s' % (donation_line.product.name, request.form['item%s_description' % line_num])
				else:
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
	return render_template('receipt.html', company=company, company_address=company_address, transaction=donation, date=donation.purchase_date, transaction_type='donation', product_prices=json.dumps(product_prices))

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
		sale.state = 'confirmed'
		sale.save()
		
		#Once parent 'sale' has been created, add item 'lines' to it
		for line_num in range(1, 6):
			if request.form['item%s_quantity' % line_num]:
				sale_line = sale.lines.new()
				sale_line.sale = Sale(sale.id)
				sale_line.type = 'line' 
				sale_line.quantity = Decimal(request.form['item%s_quantity' % line_num])
				sale_line.product = Product(int(request.form['item%s_type' % line_num]))
				if request.form['item%s_description' % line_num]:
					sale_line.description = '%s - %s' % (sale_line.product.name, request.form['item%s_description' % line_num])
				else:
					sale_line.description = sale_line.product.name
				sale_line.unit = Unit(1)
				sale_line.unit_price = Decimal(request.form['item%s_price' % line_num])
				sale_line.save()
		return redirect(url_for('sale_receipt', sale_id=sale.id))
		
	#Finally, render sale page
	return render_template('transaction.html', form=form, transaction_type='sale', company=company, parties=json.dumps(Parties), product_prices=json.dumps(product_prices))
	
@app.route("/sale/receipt/<int:sale_id>")
def sale_receipt(sale_id):
	sale = Sale(sale_id)
	return render_template('receipt.html', company=company, company_address=company_address, transaction=sale, date=sale.sale_date, transaction_type='Sale')

if __name__ == "__main__":
    app.run()
