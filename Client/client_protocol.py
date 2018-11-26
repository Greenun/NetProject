import asyncio
import time
#from transfer_unit import *
import json

#import functools

HOST = '127.0.0.1'#10.0.8.16
PORT = 42000

recv_data = None

class ClientProtocol(asyncio.Protocol):
	def __init__(self, send_data, loop):
		self.send_data = send_data#json dump
		self.transport = None
		self.loop = loop
		self.__done = loop.create_future()
		#self.recv_data = None

	def connection_made(self, transport):
		self.transport = transport
		self.address = transport.get_extra_info('peername')
		print('address: {0}\nProtocol: {1}'.format(self.address, self.transport.get_protocol()))

		#data = encapsulate('signup', ['iopuy1234', '0584qwqw'])
		#data = {'type':'login', 'data':{'id':'iopuy1234', 'password':'0584qwqw'}}
		'''data = {'type':'command', 'data':{'category':'run', 'session':'1058aad95a214cb98ad9a8f323d20351', 'detail': {
		'id':'iopuy1234',
		'name': 'guest1',
		}}}'''
		print(self.send_data)

		self.transport.write(json.dumps(self.send_data).encode())

	def data_received(self, data):
		#task = asyncio.ensure_future(self.future)
		print('Received From Server : {0}'.format(data))
		print(data)
		global recv_data
		recv_data = data
		self.transport.write_eof()

	def eof_received(self):
		print('End Of File')
		self.transport.close()
		return True

	def write(self, data):
		self.transport.write(data)

	def connection_lost(self, err):
		#self.transport.close()
		print('Connection Lost : {0}'.format(err))
		self.__done.set_result(None)

	def wait_connection_lost(self):
		return self.__done


def main(data):
	loop = asyncio.get_event_loop()
	#client_completed = asyncio.Future()
	#sub_coro = asyncio.ensure_future(data_listener())#data_listener(client_completed)
	#client_protocol = ClientProtocol(data, loop)
	coro = loop.create_connection(lambda: ClientProtocol(data,loop), HOST, PORT)

	try:
		#loop.run_until_complete(data_listener(client_completed))
		transport, protocol = loop.run_until_complete(coro)
		loop.run_until_complete(protocol.wait_connection_lost())
		#loop.run_until_complete(client_completed)
	except KeyboardInterrupt:
		pass
	finally:
		print('Close Loop')
		loop.close()
		return recv_data

def async_listen(shared_dict):
	'''
	policy = asyncio.get_event_loop_policy()
	policy.set_event_loop(policy.new_event_loop())
	loop = asyncio.get_event_loop()
	loop.run_until_complete()
	'''
	loop = asyncio.get_event_loop()
	print("fucking")
	loop.run_until_complete(asyncio.start_server(lambda r,w: listen_handle(r,w,shared_dict), "", 42000, loop=loop))#lambda r,w: listen_handle(r,w,shared_dict)
	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass
	finally:
		loop.close()
#, shared_dict
async def listen_handle(reader, writer, shared_dict):
	print("Oh Fuck")
	update_dict = {}
	data = await reader.read()
	data = json.loads(data.decode())
	req_type = data['type']
	detail = data['data']
	if detail['msg'] == 'Success':
		detail.pop('msg')
		hostname = detail['name']
		detail.pop('name')
		update_dict[hostname] = detail
		shared_dict.update(update_dict)
	else:
		pass
	print(shared_dict)

if __name__ == '__main__':
	x = main('fuck')
	#print(x)