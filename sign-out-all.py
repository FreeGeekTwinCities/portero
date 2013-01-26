from datetime import date, datetime, timedelta
from flask import Flask
import portero_config
import logging

app = Flask(__name__)
app.config.from_object('portero_config')

app.debug = app.config['DEBUG']
if app.debug:
	logging.basicConfig(level=logging.DEBUG)
else:
	logging.basicConfig(level=logging.INFO)
	from logging.handlers import SMTPHandler
	mail_handler = SMTPHandler(app.config['SMTP_HOST'], app.config['SMTP_USER'], app.config['ADMINS'], 'Portero Error')
	mail_handler.setLevel(logging.ERROR)
	app.logger.addHandler(mail_handler)
	#file_handler = FileHandler(app.config['LOG_FILE'])
	#file_handler.setLevel(logging.INFO)
	#app.logger.addHandler(file_handler)

import openerplib
connection = openerplib.get_connection(hostname=app.config['ERP_HOST'], database=app.config['ERP_DB'], login=app.config['ERP_USER'], password=app.config['ERP_PASSWORD'])

employee_model = connection.get_model("hr.employee")
employees = employee_model.search_read([("active", "=", True)])

attendance_model = connection.get_model("hr.attendance")
timesheet_model = connection.get_model("hr_timesheet_sheet.sheet")
    	
today = str(date.today().strftime('%Y-%m-%d'))
now = str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
auto_signout_hours = int(app.config['AUTO_SIGNOUT_HOURS'])

employees_signed_in = [{'id': employee['id'], 'name': employee['name']} for employee in employees if employee['state'] == 'present']
#print employees_signed_in

for employee in employees_signed_in:
	#print employee
	current_timesheets = timesheet_model.search([("employee_id", "=", employee['id']), ("date_from", "=", today)])
	if len(current_timesheets):
		sheet = current_timesheets[0]
		#Check to see if automatically-signed-out users are logged out "now", or get a pre-set number of hours credited
		if auto_signout_hours > 0:
			sign_in = attendance_model.search_read([("sheet_id", "=", sheet)])[0]
			#Parse the sign-in time from the 'name' value of the attendance object
			sign_in_time = datetime.strptime(sign_in['name'], '%Y-%m-%d %H:%M:%S')
			#print sign_in_time
			#Next, we'll create a 'timedelta' object containing the credited hours
			time_diff = timedelta(hours=auto_signout_hours)
			#print time_diff
			#Finally, we add the credited hours to the sign-in time to generate a new sign-out time
			sign_out_time = (sign_in_time + time_diff).strftime('%Y-%m-%d %H:%M:%S')
			#print sign_out_time
		else:
			#If auto_signout_hours is set to zero, just sign users out at time script is run
			sign_out_time = now
		new_event = {
			'employee_id' : employee['id'],
			'name' : sign_out_time,
			'day' : today,
			'action' : 'sign_out',
			'sheet_id' : int(sheet)
		}
		print new_event
		event = attendance_model.create(new_event)		
