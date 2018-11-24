import asyncio
import logging
import datetime
import json
import pymysql

'''
해야할 일 : header type : request, info, complete 처리
request --> client로부터 받아서 db 검색 후 전달
info --> xen server로부터 받아서 db에 저장
show --> request받고 돌려주는 type
complete --> create 완료 시 owned instance update 중요!

usage_info(table)

name(guest), cpu, network [tx, rx], vbd [rd, wr]
'''

DB_ADDR = ('127.0.0.1', 3306)#db in docker(address)
INSTANCE_ADDR = ('127.0.0.1', 42000)#to xen server
#RELAY_TYPE = ('info', 'request', 'complete')

class RelayHandler():
	def __init__(self, data, req_type, reader, writer, loop):
		self.data = data
		self.req_type = req_type
		self.loop = loop
		self.reader = reader
		self.writer = writer

		self.db = pymysql.connect(host=DB_ADDR[0], port=DB_ADDR[1], user='root', password='0584qwqw', db='Project',
			cursorclass=pymysql.cursors.DictCursor)
		self.modules = (self.handle_info, self.handle_request, self.handle_complete)

	#def __call__(self):
	#	module_pt = self.modules[RELAY_TYPE.index(self.req_type)]
	#	self.loop.run_until_complete(module_pt())

	def __del__(self):
		if self.db:
			self.db.close()
		else:
			pass

	async def handle_info(self):
		#from xen
		pass

	async def handle_request(self):
		#from client
		pass

	async def handle_complete(self):
		#from xen
		#is running 인지도 알아야 할텐데..
		if self.data['msg'] == 'create':
			user_id = self.data['id']
			cursor = self.db.cursor()
			sql_query = "SELECT * FROM login_info WHERE user_id = '" + user_id + "';"

			cursor.execute(sql_query)
			result = cursor.fetchall()[0]

			if result:
				old_owned = result['owned_instance']
				old_run = result['is_running']
				owned = ''
				is_running = ''
				if old_owned:
					owned = old_owned+' '+self.data['name']
				else:
					owned = self.data['name']
				if old_run:
					is_running = old_run+' '+self.data['name']
				else:
					is_running = self.data['name']

				update_query = "UPDATE login_info SET owned_instance = '"+ owned + "', is_running = '"+ is_running+"' WHERE user_id = '"+user_id+"';"#update
				cursor.execute(update_query)
				self.db.commit()

				send_data = {'type': 'create', 'data': {'ip':self.data['ip'],'state':'running' ,'msg':'Success'}}
				send_data = json.dumps(send_data).encode()
				clnt_addr = self.data['client']
				await self.send_to(send_data, clnt_addr)

				cursor.close()
				return 105
			else:
				print("No User Data.")
				return 405

		elif self.data['msg'] == 'run':
			#run --> is_running update, (type:run)send ip, state(인스턴스 running), msg to client
			user_id = self.data['id']
			hostname = self.data['name']

			cursor = self.db.cursor()
			sql_query = "SELECT * FROM login_info WHERE user_id = '" + user_id + "';"

			cursor.execute(sql_query)
			result = cursor.fetchall()[0]

			if result:
				old_run = result['is_running']
				is_running = ''

				if old_run:
					is_running = old_run + ' ' + hostname
				else:
					is_running = hostname

				update_query = "UPDATE login_info SET is_running = '" + is_running + "' WHERE user_id='"+ user_id + "';"
				cursor.execute(update_query)
				self.db.commit()

				send_data = {'type':'run', 'data': {'ip': self.data['ip'], 'state':'running', 'msg':'Success'}}
				send_data = json.dumps(send_data).encode()
				clnt_addr = self.data['client']
				await self.send_to(send_data, clnt_addr)
				cursor.close()
				return 106
			else:
				print('No User Data')
				return 406

		elif self.data['msg'] == 'stop':
			#stop --> is_running update, (type:stop)send ip(빈칸), state, msg to client
			user_id = self.data['id']
			hostname = self.data['name']

			cursor = self.db.cursor()
			sql_query = "SELECT * FROM login_info WHERE user_id = '" + user_id + "';"
			cursor.execute(sql_query)
			result = cursor.fetchall()[0]

			if result:
				old_run = result['is_running']
				is_running = ''
				if old_run:
					old_list = old_run.split()
					if hostname in old_list:
						old_list.remove(hostname)
						is_running = ' '.join(old_list)
					else: print("There is no hostname")
				else:
					is_running = ''
					print("No Instance is Running")

				update_query = "UPDATE login_info SET is_running = '" + is_running + "' WHERE user_id='"+ user_id + "';"
				cursor.execute(update_query)
				self.db.commit()

				send_data = {'type':'stop', 'data': {'ip': '', 'state':'stopped', 'msg':'Success'}}
				send_data = json.dumps(send_data).encode()
				clnt_addr = self.data['client']
				await self.send_to(send_data, clnt_addr)
				cursor.close()
				return 107
			else:
				print('No User Data')
				return 407

		elif self.data['msg'] == 'delete':
			#delete --> running 중엔 delete 못하도록 설정해야함(client에서)
			#owned_instance update, (type:delete)send msg to client(Success 받으면 client에서 제거)
			user_id = self.data['id']
			hostname = self.data['name']

			cursor = self.db.cursor()
			sql_query = "SELECT * FROM login_info WHERE user_id = '" + user_id + "';"
			cursor.execute(sql_query)
			result = cursor.fetchall()[0]
			if result:
				old_owned = result['owned_instance']
				owned = ''
				if old_owned:
					old_list = old_owned.split()
					if hostname in old_list:
						old_list.remove(hostname)
						owned = ' '.join(old_list)
					else: print("There is no hostname")
				else:
					owned = ''
					print('No instance is owned')
				update_query = "UPDATE login_info SET owned_instance = '" + owned + "' WHERE user_id='"+ user_id + "';"
				cursor.execute(update_query)
				self.db.commit()

				send_data = {'type':'delete', 'data': {'ip': '', 'state':'deleted', 'msg':'Success'}}
				send_data = json.dumps(send_data).encode()
				clnt_addr = self.data['client']
				await self.send_to(send_data, clnt_addr)
				cursor.close()
				return 108
			else:
				print('No User Data')
				return 408
		else:
			print("Error -- No Task..")

	async def send_to(send_data, clnt_addr):
		client_reader, client_writer = await asyncio.open_connection(clnt_addr[0], 42000)#포트는 client에 열어놓는 포트 사용
		client_writer.write(send_data)
		client_writer.write_eof()
		client_writer.close()
