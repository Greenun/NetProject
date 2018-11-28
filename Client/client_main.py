from PyQt5.QtWidgets import *
from PyQt5 import uic
import asyncio
import client_protocol as cp
from multiprocessing import Process, Manager
from threading import Timer
import json

class Form(QMainWindow):
	def __init__(self):
		super().__init__()
		self.login_ui = uic.loadUi('./ui/Login_form.ui')
		self.main_ui = uic.loadUi('./ui/main_form.ui')
		self.signup_ui = uic.loadUi('./ui/signup_form.ui')
		self.create_ui = uic.loadUi('./ui/create_form.ui')
		self.old_value = None#비교용

		self.login_ui.signup_btn.clicked.connect(self.init_signup)
		self.login_ui.login_btn.clicked.connect(self.login)
		self.login_ui.show()

	#-----singup_ui function start----------
	def init_signup(self):
		self.signup_ui.ok_btn.clicked.connect(self.signup)
		self.signup_ui.cancel_btn.clicked.connect(self.cancel)

		self.signup_ui.show()

	def cancel(self):
		self.signup_ui.ok_btn.clicked.disconnect()
		self.signup_ui.cancel_btn.clicked.disconnect()
		self.signup_ui.close()

	def signup(self):
		send_data = {'type':'signup', 'data':{}}
		user_id = self.signup_ui.id_input.text()
		user_pw = self.signup_ui.pw_input.text()

		if not user_id or not user_pw:
			QMessageBox.about(self, "Error", "Need ID and Password.")
		send_data['data']['id'] = user_id
		send_data['data']['password'] = user_pw
		#print(send_data)
		resp = cp.main(send_data)
		print(resp)
		if resp['type'] == 'Success':
			QMessageBox.about(self, "Success", "Success")
			self.cancel()
		else:
			QMessageBox.about(self, "Error", "Invalid Info for signup")
	#-------signup ui end---------------
	#---------------login ui function start---------------
	def login(self):
		send_data = {'type':'login', 'data':{}}
		user_id = self.login_ui.id_input.text()
		user_pw = self.login_ui.pw_input.text()
		send_data['data']['id'] = user_id
		send_data['data']['password'] = user_pw

		resp = cp.main(send_data)
		#resp = None
		#resp = {'type':'Success', 'session': 'asdf', 'data': {'msg':'ad', 'detail':{'a':{'state':'running', 'ip':'123.123.123.123'}}}}
		#resp = json.loads(resp.decode())
		#resp_json = resp
		if resp:
			#resp_json = json.loads(resp.decode())
			if resp['type'] == "Success":
				self.main_ui.id_label.setText(user_id)
				self.user_id = user_id#user id 저장 매 요청마다 보냄
				self.login_ui.close()
				self.user_session = resp['session']#session 적용
				print(self.user_session)
				self.init_main(resp['data']['detail'])
			else:
				QMessageBox.about(self, "Error", "Invalid ID or Password")
		else:
			QMessageBox.about(self, "Error", "Login Failed. No response")
	#--------login ui function ends-----------------

	def init_main(self, resp):
		self.main_ui.logout_btn.clicked.connect(self.logout)
		self.main_ui.create_btn.clicked.connect(self.create)
		self.main_ui.run_btn.clicked.connect(self.run)
		self.main_ui.stop_btn.clicked.connect(self.stop)
		self.main_ui.delete_btn.clicked.connect(self.delete)
		self.main_ui.show_btn.clicked.connect(self.show)
		#--------------connect signal ----------------

		header = ['Host name', 'State' ,'Host ip']
		self.main_ui.ins_table.setColumnCount(3)
		self.main_ui.ins_table.setRowCount(0)
		self.main_ui.ins_table.setHorizontalHeaderLabels(header)
		self.instance_dict = Manager().dict()#shared dict
		self.add_row(resp)
		self.main_ui.list_box.addItems([name for name in resp.keys()])
		#self.main_ui.list_box.currentText()

		self.listener = Process(target=cp.async_listen, args=(self.instance_dict,))
		self.listener.start()
		self.check_dict()

		self.main_ui.show()

	def create(self):
		self.create_ui.submit_btn.clicked.connect(self.create_submit)
		self.create_ui.cancel_btn.clicked.connect(self.create_cancel)

		self.create_ui.show()

	def create_submit(self):
		#print("뿅")
		hostname = self.create_ui.name_input.text()
		root_pw = self.create_ui.pw_input.text()
		
		send_data = {'type':'command', 'data':{'category':'create',
		'session': self.user_session,
		'detail':{

		}}}

		if not hostname or not root_pw:
			print("Needs hostname and root password")
			return

		if self.create_ui.type1.isChecked():
			send_data['data']['detail']['mem'] = '128mb'
			send_data['data']['detail']['size'] = '5gb'
		elif self.create_ui.type2.isChecked():
			send_data['data']['detail']['mem'] = '256mb'
			send_data['data']['detail']['size'] = '10gb'
		elif self.create_ui.type3.isChecked():
			send_data['data']['detail']['mem'] = '512mb'
			send_data['data']['detail']['size'] = '20gb'
		else:
			print('Please Check')
			return

		send_data['data']['detail']['id'] = self.user_id
		send_data['data']['detail']['name'] = hostname
		send_data['data']['detail']['password'] = root_pw

		print(send_data)
		resp = cp.main(send_data)
		QMessageBox.about(self, "Success", "Submit")
		self.create_cancel()#종료
		self.main_ui.log_show.append(json.dumps(resp))

	def create_cancel(self):
		self.create_ui.submit_btn.clicked.disconnect()
		self.create_ui.cancel_btn.clicked.disconnect()
		self.create_ui.close()

	def run(self):
		hostname = self.main_ui.list_box.currentText()#선택한 name

		send_data = {'type':'command', 'data':{'category': 'run',
		'session':self.user_session,
		'detail':{'id': self.user_id,
		'name': hostname
		}}}
		resp = cp.main(send_data)
		self.main_ui.log_show.append(json.dumps(resp))

	def stop(self):
		hostname = self.main_ui.list_box.currentText()#선택한 name

		send_data = {'type':'command', 'data':{'category': 'stop',
		'session':self.user_session,
		'detail':{'id': self.user_id,
		'name': hostname
		}}}
		resp = cp.main(send_data)
		self.main_ui.log_show.append(json.dumps(resp))

	def delete(self):
		hostname = self.main_ui.list_box.currentText()#선택한 name

		send_data = {'type':'command', 'data':{'category': 'delete',
		'session':self.user_session,
		'detail':{'id': self.user_id,
		'name': hostname
		}}}
		resp = cp.main(send_data)
		self.main_ui.log_show.append(json.dumps(resp))

	def logout(self):
		user_id = self.user_id

		send_data = {'type': 'logout', 'data':{'id': user_id}}
		print(send_data)
		resp = cp.main(send_data)
		#print(resp)
		self.listener.terminate()
		self.timer.cancel()
		self.main_ui.close()


	def show(self):
		#hostname, datetime(일 단위)
		print(self.main_ui.list_box.count())
		print(self.main_ui.list_box.itemText(0))

	def add_row(self, data):
		for key in data.keys():
			row_pos = self.main_ui.ins_table.rowCount()
			self.main_ui.ins_table.insertRow(row_pos)

			self.main_ui.ins_table.setItem(row_pos, 0, QTableWidgetItem(key))
			self.main_ui.ins_table.setItem(row_pos, 1, QTableWidgetItem(data[key]['state']))
			self.main_ui.ins_table.setItem(row_pos, 2, QTableWidgetItem(data[key]['ip']))


	def check_dict(self):
		#dict --> {name : {ip: , state:}, name2 : ...}
		print("what..")
		#table도 업데이트 해야해
		if self.old_value != self.instance_dict.copy():
			self.main_ui.log_show.append(json.dumps(self.instance_dict.copy()))#
			self.update_table()
			self.old_value = self.instance_dict.copy()
		else:
			pass
		self.timer = Timer(20, self.check_dict)
		self.timer.start()
	#---------------main ui function ends----------------

	def update_table(self):
		target = self.instance_dict.copy()
		row_count = self.main_ui.ins_table.rowCount()
		#row 수가 적으면 증가시킴
		while row_count < len(target.keys()):
			self.main_ui.ins_table.insertRow(row_count)
			row_count += 1
		for row, name in enumerate(target.keys()):
			self.update_listbox(name)
			#self.main_ui.list_box.addItems([name])#이미 있으면 추가하면 안댐!
			self.main_ui.ins_table.setItem(row, 0, QTableWidgetItem(name))
			self.main_ui.ins_table.setItem(row, 1, QTableWidgetItem(target[name]['state']))
			self.main_ui.ins_table.setItem(row, 2, QTableWidgetItem(target[name]['ip']))#고민
			'''for col, val in enumerate(target[name].values(), 1):
				self.main_ui.ins_table.setItem(row, col, QTableWidgetItem(val))'''
	def update_listbox(self, new_item):
		count = self.main_ui.list_box.count()
		all_items = [self.main_ui.list_box.itemText(i) for i in range(0, count)]
		if new_item in all_items:
			pass
		else:
			self.main_ui.list_box.addItems([new_item])			

async def test1():
	print('shit')
	await asyncio.sleep(0.6)

if __name__ == '__main__':
	app = QApplication([])
	w = Form()
	app.exec()
#login_form = uic.loadUiType("./ui/Login_form.ui")
#main_form = uic.loadUiType("./ui/main_form.ui")
#print(ui_form)
'''
class Login(QMainWindow, login_form[0]):
	def __init__(self):
		super().__init__()
		self.setupUi(self)

class MainForm(QMainWindow, main_form[0]):
	def __init__(self):
		super().__init__()
		self.setupUi(self)

if __name__ == '__main__':
	app =QApplication([])
	mywindow = MainForm()
	mywindow.show()
	app.exec_()
'''