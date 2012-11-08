import pkg_resources
pkg_resources.require("Flask")

from flask import Flask, render_template
from proteus import config, Model
 
tryton_config = config.set_trytond(database_name='test', user='admin', password='test')
print tryton_config

app = Flask(__name__)

@app.route("/")
def hello():
	Party = Model.get('party.party')
	parties = Party.find()
	party_array = []
	for party in parties:
		party_array.append({'code': party.code, 'name': party.name})
	print party_array
	
	Work = Model.get('timesheet.work')
	works = Work.find()
	work_array = []
	for work in works:
		work_array.append({'id': work.id, 'name': work.name})
		
	Employee = Model.get('company.employee')
	employees = Employee.find([('company', '=', 1)])
	employee_array = []
	for employee in employees:
		employee_array.append({'id': employee.id})
	
	return render_template('hello.html', party_array=party_array, work_array=work_array, employees=employee_array)
	
if __name__ == "__main__":
    app.run()
