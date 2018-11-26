import json

TYPE = ('signup', 'login', 'logout', 'command', 'request', 'management', 'show')
'''
{type: ***,
data: {
	something---
}}

xen handler --> instance 생성 시 instance id db에 저장

signup --> id, password 
login --> id, password
logout --> id, session     ------------from client to relay
accept --> session (from relay to client) (key = data)
command --> category(create, modify, delete, run, stop), session(key = session), detail(id포함)/ run, stop
--> uuid or instance name
management --> cpu, mem, network(tx, rx), bd(blockdevice - rd, wr) (from xen to relay)
show --> cpu, mem, network(tx, rx), vbd(blockdevice - rd, wr) (from relay to client)
'''


def get_type(req_type):
	return TYPE.index(req_type)

#data:list -- accept : data == session
def encapsulate(request_type, data, session=''):
	data_unit = {'type':'' ,'data':{}}
	data_unit['type'] = request_type
	req_num = get_type(request_type)
	#key 값이 없을 경우 예외처리
	if req_num == 0 or req_num == 1: 
		data_unit['data']['id'] = data[0]
		data_unit['data']['password'] = data[1]
	elif req_num == 2:
		data_unit['data']['id'] =  data[0]
	elif req_num == 3:
		#command
		data_unit['data']['category'] = data[0]
		data_unit['data']['detail'] = data[1]#dict e.g., {cpu:asdf, mem:asdf, size:asdf...}
		data_unit['data']['session'] = session
	elif req_num == 4:
		#accept
		data_unit['data']['id'] = data[0]
		data_unit['data']['session'] = session#data[1]
	elif req_num == 5 or req_num == 6:
		data_unit['data']['cpu'] = data[0]
		data_unit['data']['mem'] = data[1]
		data_unit['data']['network'] = data[2]#tuple
		data_unit['data']['bd'] = data[3]#tuple

	data_unit['session'] = session
	return data_unit

def extract(data_unit):
	#request_type : str
	request_type = data_unit['type']
	#data : dict
	data = data_unit['data']
	
	return request_type, data



