import asyncio
import logging
import sys
import time
import datetime
import subprocess
from multiprocessing import Process

REQ_TYPES = ('create', 'delete', 'run', 'stop')
RELAY_ADDR = ('127.0.0.1', 42001)#relay async 주소 
BASE_DIR = '/etc/xen/'
'''
delete, run, stop 시 is_running과 owned_instance 주목 필요
'''

def get_type(req_type):
	return REQ_TYPES.index(req_type)

def handle_instance(req_type, data_detail):
	req = get_type(req_type)
	modules = (create_sequence, delete_image, run_image, stop_image)#create image is in seq
	modules[req](data_detail)

def create_image(data_detail):
	#default --> xenial
	cmd = """xen-create-image --hostname={0} --memory={1} --size={2} --dhcp --pygrub --dist=xenial --dir=/data/xen --bridge=xenbr0 --boot --password={3} --role=editor""".format(data_detail['name'], 
		data_detail['mem'], data_detail['size'], data_detail['password'])#vcpu는 1로 고정(default)
	cmd = cmd.split(' ')
	f = open('/dev/null', 'w')
	subprocess.call(cmd, stdout=f)#run create image

def create_sequence(data_detail):
	#ip 얻기까지 끝나면 detail 내의 id, name도 함께 전송
	proc = Process(target=create_image, args=(data_detail,))
	print("Create Image Start : {0}".format(str(datetime.datetime.now())))
	proc.start()
	time.sleep(2)#buffer time
	result = subprocess.check_output('./script/get_tail.sh '+data_detail['name'], stderr=subprocess.STDOUT, shell=True).decode()
	result = result[0:len(result)-1]
	proc.terminate()
	print("Create Image End : {0}".format(str(datetime.datetime.now())))
	instance_ip = ''
	if result == 'Done':
		time.sleep(8)#for boot time
		while not instance_ip:
			instance_ip = subprocess.check_output('./script/ip_get.sh '+data_detail['name'], stderr=subprocess.STDOUT, shell=True).decode()
			instance_ip = instance_ip[0:len(instance_ip)-1]
			print("ip : " + instance_ip)
	elif result == 'Error':
		print("Error!")
	else:
		print("Fatal Error")

	#loop = asyncio.get_event_loop()
	send_data = {'type': 'complete', 'data': {'id':data_detail['id'], 'name':data_detail['name'], 'msg':'create', 'client':data_detail['client']}}
	print(send_data)
	loop.run_until_complete(send_complete(send_data))

	loop.close()
	
async def send_complete(send_data):
	#to relay
	reader, writer = await asyncio.open_connection(RELAY_ADDR[0], RELAY_ADDR[1])
	send_data = json.dumps(send_data).encode()
	writer.write(send_data)
	writer.write_eof()
	await writer.drain()

def delete_image(data_detail):
	name = data_detail['name']
	cmd = "xen-delete-image --dir=/data/xen --hostname={0}".format(name)
	cmd = cmd.split(' ')
	subprocess.call(cmd)

	send_data = {'type':'complete', 'data': {'name': data_detail['name'], 'id': data_detail['id'],'msg':'delete'}}
	loop = asyncio.get_event_loop()
	loop.run_until_complete(send_complete(send_data))
	loop.close()


def run_image(data_detail):
	name = data_detail['name']
	name = BASE_DIR + name + '.cfg'
	cmd = "xl create {0}".format(name)
	cmd = cmd.split(' ')
	subprocess.call(cmd)

	send_data = {'type':'complete', 'data': {'name': data_detail['name'], 'id': data_detail['id'],'msg':'run'}}
	print(send_data)
	loop = asyncio.get_event_loop()
	loop.run_until_complete(send_complete(send_data))
	loop.close()

def stop_image(data_detail):
	name = data_detail['name']
	cmd = "xl shutdown {0}".format(name)
	cmd = cmd.split(' ')
	subprocess.call(cmd)

	send_data = {'type':'complete', 'data': {'name': data_detail['name'], 'id': data_detail['id'],'msg':'stop'}}
	loop = asyncio.get_event_loop()
	print(loop.is_running())
	loop.run_until_complete(send_complete(send_data))
	loop.close()