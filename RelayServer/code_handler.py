import asyncio
import logging
import sys
import json

#command 전송 시 handler는 어떻게 할까
CODE_DICT = {100: '', 101: '', 102: '', 400: '', 401: '', 402: ''}

class CodeHandler():
	def __init__(self, code, transport, session=None):
		self.code = ''
		self.session = ''
		self.result = None
		if type(code) == type(()):
			self.code = code[0]
			self.session = code[1]
			self.result = code[2]
		else:	
			self.code = code
			self.session = session
		self.transport = transport
	
	def run_handler(self):
		if self.code == 100 or self.code == 400:
			self.signup_code()
		elif self.code == 101 or self.code == 401:
			self.login_code()
		elif self.code == 102 or self.code == 402:
			self.logout_code()
		elif self.code == 103 or self.code == 403:
			self.cmd_handler()
		else:
			pass

	def signup_code(self):
		if self.code == 100:
			data = {'type': 'Success', 'data': 'Sign up Succeed'}
			self.transport.write(json.dumps(data).encode())
			#self.transport.write_eof()
		elif self.code == 400:
			data = {'type': 'Fail', 'data': 'Sign up Failed'}
			self.transport.write(json.dumps(data).encode())
			#self.transport.write_eof()
		else:
			print("invalid code in signup")

	def login_code(self):
		#use self.session
		#login --> session과 owned, is_running을 모두 넘겨줌
		if self.code == 101:
			data = {'type': 'Success', 'data':{'msg':'Login Succeed', 'detail':{}},'session': self.session}
			if self.result:
				data['data']['detail'] = self.result
			self.transport.write(json.dumps(data).encode())
			#self.transport.write_eof()
		elif self.code == 401:
			data = {'type': 'Fail', 'data': 'Login Failed'}
			self.transport.write(json.dumps(data).encode())
		else:
			print("invalid code in login")

	def logout_code(self):
		if self.code == 102:
			data = {'type': 'Success', 'data': 'Logout Succeed'}
			self.transport.write(json.dumps(data).encode())
		elif self.code == 402:
			data = {'type': 'Fail', 'data': 'Logout Failed'}
			self.transport.write(json.dumps(data).encode()) 
		else:
			print("invalid code in logout")

	def cmd_handler(self):
		if self.code == 103:
			data = {'type': 'Progressing', 'data':'Progressing...'}
			self.transport.write(json.dumps(data).encode())
		elif self.code == 403:
			data = {'type': 'Fail', 'data':'Invalid Session'}
			self.transport.write(json.dumps(data).encode())
		else:
			print("invalid code in command")