from datetime import date, datetime
from flask import Flask
import portero_config

app = Flask(__name__)
app.config.from_object('portero_config')
	
import openerplib
connection = openerplib.get_connection(hostname=app.config['ERP_HOST'], database=app.config['ERP_DB'], login=app.config['ERP_USER'], password=app.config['ERP_PASSWORD'])

employee_model = connection.get_model("hr.employee")
employees = employee_model.search_read([("active", "=", True)])

attendance_model = connection.get_model("hr.attendance")
timesheet_model = connection.get_model("hr_timesheet_sheet.sheet")
    	
today = str(date.today().strftime('%Y-%m-%d'))
now = str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
employees_signed_in = [{'id': employee['id'], 'photo': employee['image_small'], 'name': employee['name']} for employee in employees if employee['state'] == 'present']
#print employees_signed_in

for employee in employees_signed_in:
	#print employee
	current_timesheets = timesheet_model.search([("employee_id", "=", employee['id']), ("date_from", "=", today)])
	if len(current_timesheets):
		sheet = current_timesheets[0]
		new_event = {
			'employee_id' : employee['id'],
			'name' : now,
			'day' : today,
			'action' : 'sign_out',
			'sheet_id' : int(sheet)
		}
		print new_event
		event = attendance_model.create(new_event)		
