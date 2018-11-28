import uuid
import hashlib
import pymysql
import asyncio
from aioprocessing import AioProcess
import json

#__all__ = ('ClientHandler')
DB_ADDR = ('127.0.0.1', 3306)#db in docker(address)
INSTANCE_ADDR = ('10.0.8.15', 42000)#to xenserver
'''
DB : MariaDB (in docker)
DB Name : Project
	- table : Session table(session_info)(user_id, session:uuid)
			: Login Info table(login_info)(primary(자동생성), user_id, password, owned_instance:uuid(divided by space))
			--> all str(varchar)
			login info에 is_running col 추가

--------Have to insert owned instance when they call run_instance in xen--------
'''
class ClientHandler():
	def __init__(self, data, req_type:int, loop=None, client_addr=None):
		self.req_type = req_type
		self.modules = (self.signup_handler,
						self.login_handler,
						self.logout_handler,
						self.command_handler,
						self.request_handler)
		self.data = data
		self.loop = loop
		self.client_addr = client_addr
		self.db = pymysql.connect(host=DB_ADDR[0], port=DB_ADDR[1], user='root', password='0584qwqw', db='Project', cursorclass=pymysql.cursors.DictCursor)

	def __call__(self):
		return self.modules[self.req_type].__call__(self.data)

	def __del__(self):
		#끝나면 db connection 닫음
		if self.db:
			self.db.close()
		else:
			pass

	#DB connect, insert id, password
	def signup_handler(self, data):
		user_id = data['id']
		user_pw = data['password']
		#insert id, password
		'''sql_query = "INSERT INTO login_info VALUES (" + user_id + "," + user_pw + ");"

		cursor = self.db.cursor()
		cursor.execute(sql_query)'''
		if self.insert_validation(user_id, user_pw):
			#send signup complete message!
			return 100
		else:
			#send duplicated(or invalid) id message
			return 400

	#DB connect, select id, password -- validation - 강제종료로 세션이 있으면 그거주기?
	def login_handler(self, data):
		cursor = self.db.cursor()
		user_id = data['id']
		user_pw = data['password']
		ret_dict = {}
		sql_query = "SELECT * FROM login_info WHERE user_id = '" + user_id + "';"
		cursor.execute(sql_query)
		result = cursor.fetchall()
		#((a, b),)
		if result:
			db_pw = result[0]['password']
			encryted_user_pw = hashlib.sha256(user_pw.encode()).hexdigest()

			if db_pw == encryted_user_pw:
				#login success
				user_session = self.set_session()
				session_query = "INSERT INTO session_info VALUES ( '" + user_id + "', '" + user_session + "');"
				cursor.execute(session_query)
				self.db.commit()
				#send session to client --> tuple type
				ret_dict = self.get_run_ip(result[0], cursor)
				cursor.close()
				#return 101, user_session
				return 101, user_session, ret_dict
		else:
			#No User --> send login failed message
			cursor.close()
			return 401
		#return 101

	#DB connect, delete session(in session table)
	def logout_handler(self, data):
		user_id = data['id']
		#user_session = data['session']
		try:
			cursor = self.db.cursor()
			#sql_query = "SELECT * FROM session_info WHERE session = '"+user_session+"';"
			#sql_query = "DELETE FROM session_info WHERE session = '"+user_session+"';"
			sql_query = "DELETE FROM session_info WHERE user_id = '"+user_id+"';"
			cursor.execute(sql_query)
			self.db.commit()
			cursor.close()
			return 102
		except:
			print("Delete Session Failed")
			#logout failed
			cursor.close()
			return 402

	def command_handler(self, data):
		'''
		{'type': ...,
		'data':
			{category: asdf, detail: asdf, session: asdf}
		}
		detail : cpu, mem, size, name(id-name 형태로 저장할듯), password(root), id(login id)
		'''
		category = data['category']#create, delete, run, stop
		clnt_session = data['session']
		#clnt_session = clnt_session.hex
		detail = data['detail']
		detail['client'] = self.client_addr#클라이언트 주소
		if category == 'create':
			detail['name'] = detail['id']+'-'+detail['name']
		
		cursor = self.db.cursor()
		sql_query = "SELECT * FROM session_info WHERE session = '"+clnt_session+"';"
		cursor.execute(sql_query)
		result = cursor.fetchall()

		if result:
			#do handling
			send_dict = {'type': category, 'detail': detail}
			print(send_dict)#for debug
			#coro = asyncio.open_connection(INSTANCE_ADDR[0], INSTANCE_ADDR[1], loop=self.loop)
			#task = asyncio.ensure_future(coro)
			#reader, writer = self.loop.run_until_complete(task)#?
			#self.loop.run_until_complete(send_to(send_dict, self.loop, self.client_addr))
			proc = AioProcess(target=connect_proc, args=(send_dict, self.loop, self.client_addr))
			proc.start()
			#proc.join()#join

			cursor.close()
			return 103
		else:
			#unvalid session!
			cursor.close()
			return 403
	
	def request_handler(self, data):
		hostname = data['name']
		target_date = data['date']
		clnt_session = data['session']

		ret_data = {'type': 'show', 'detail': {}}#client log 찍지 말자이건;

		cursor = self.db.cursor()
		sql_query = "SELECT * FROM session_info WHERE session = '"+clnt_session+"';"
		cursor.execute(sql_query)

		if not cursor.fetchall():
			return 404, session, ret_data

		sql_query = "SELECT * FROM usage_info WHERE hostname = '"+ hostname +"' AND DATE(time)='"+ target_date +"';"
		cursor.execute(sql_query)
		result = cursor.fetchall()

		usage_list = self.init_usage()#0 cpu / 1 net / 2 bd
		
		try:
			if result:
				for val in result:
					timestamp = val['time']#맞나
					new_time = int(timestamp[0:2])*60 + int(timestamp[4:5])
					usage_list[0][int(new_time/5)] = val['cpu']
					usage_list[1][int(new_time/5)] = [val['tx'], val['rx']]#맞나?
					usage_list[2][int(new_time/5)] = [val['rd'], val['wr']]#맞나..?
			else:
				pass
			ret_data['detail']['cpu'] = usage_list[0]
			ret_data['detail']['network'] = usage_list[1]
			ret_data['detail']['bd'] = usage_list[2]

			return 104, session, ret_data
		except:
			return 404, session, ret_data


	#0 list generate
	def init_usage(self):
		zero_list = [0 for i in range(0, 288)]#1440 / 5 = 288
		double_list = [[0,0] for i in range(0, 288)]
		return [zero_list, double_list, double_list]

	#make session and return it, insert session(in session table)
	#session id --> uuid
	def set_session(self):
		sid = uuid.uuid4()
		sid_str = sid.__str__()
		sql_query = "SELECT * FROM session_info WHERE session = '"+sid_str+"';"
		
		cursor = self.db.cursor()
		cursor.execute(sql_query)
		result = cursor.fetchall()
		#if session uuid exists
		if result:
			#sid = self.set_session()#get another uuid
			print("uuid already exists")
			#return sid
			return uuid.uuid4().hex
		else:
			return sid.hex

	#id, pw validation
	def insert_validation(self, user_id, password):
		
		if "'" in user_id or '"' in user_id:
			#invalid user id
			return 0

		cursor = self.db.cursor()
		#id duplicate check
		sql_query = "SELECT * FROM login_info WHERE user_id =  '" + user_id + "';"

		cursor.execute(sql_query)
		result = cursor.fetchall()

		if result:
			#id 중복
			cursor.close()
			return 0
		else:
			#password sha
			encrypted_pw = hashlib.sha256(password.encode()).hexdigest()
			insert_query = "INSERT INTO login_info VALUES ('" + user_id + "', '" + encrypted_pw +"', '', '');"
			cursor.execute(insert_query)
			self.db.commit()
			cursor.close()
			return 1

	def get_run_ip(self, result, cursor):
		#{name:{state, ip}, ...}
		ret_dict = {}
		owned = result['owned_instance'].split()
		is_run = result['is_running'].split()
		for o in owned:
			if o in is_run:
				sql_query = "SELECT * FROM ip_table WHERE name = '"+ o +"';"
				cursor.execute(sql_query)
				table_data = cursor.fetchall()
				if table_data:
					t = table_data[0]
					ret_dict[o] = {'state': 'running', 'ip': t['ip']}
			else:
				ret_dict[o] = {'state': 'stopped', 'ip': ''}

		return ret_dict


async def send_to(data, loop, client_addr):
	print(data)
	reader, writer = await asyncio.open_connection(INSTANCE_ADDR[0], INSTANCE_ADDR[1], loop=loop)
	writer.write(json.dumps(data).encode())
	writer.write_eof()
	await writer.drain()
	
	resp = await reader.read()#모든 경우 확인 메세지 보냄

	writer.close()
	#이건 왜 보내지...?
	'''
	client_reader, client_writer = await asyncio.open_connection(client_addr[0], 42000)
	client_writer.write(resp)#message 전달
	client_writer.write_eof()
	await client_writer.drain()

	client_writer.close()'''

def connect_proc(send_dict, loop, client_addr):
	policy = asyncio.get_event_loop_policy()
	policy.set_event_loop(policy.new_event_loop())
	loop = asyncio.get_event_loop()
	loop.run_until_complete(send_to(send_dict, loop, client_addr))

if __name__ == '__main__':
	pass
