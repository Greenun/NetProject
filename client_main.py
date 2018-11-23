import asyncio
import time
from transfer_unit import *
import json

#import functools

HOST = '127.0.0.1'
PORT = 42000


class ClientProtocol(asyncio.Protocol):
	def __init__(self, loop, future=None):
		self.stream_data = {}#json dump
		self.transport = None
		self.future = future
		self.loop = loop
		self.__done = loop.create_future()

	def connection_made(self, transport):
		self.transport = transport
		self.address = transport.get_extra_info('peername')
		print('address: {0}\nProtocol: {1}'.format(self.address, self.transport.get_protocol()))

		data = encapsulate('signup', ['iopuy1234', '0584qwqw'])
		print(data)
		self.transport.write(json.dumps(data).encode())

	def data_received(self, data):
		#task = asyncio.ensure_future(self.future)
		print('Received From Server : {0}'.format(data))
		print(data)
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

def sign_up():
	pass

def login():
	pass

def logout():
	pass


async def data_listener(future):
	print('start!!')
	reader, writer = await asyncio.open_connection(HOST, PORT)
	print('reading')
	writer.write(b'Send From Client')
	writer.write(b'')
	x = await reader.read()
	print('read : '+x)
	writer.close()
	await writer.wait_closed()

	if not future.done():
		future.set_result(True)



if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	client_completed = asyncio.Future()
	#sub_coro = asyncio.ensure_future(data_listener())#data_listener(client_completed)
	coro = loop.create_connection(lambda: ClientProtocol(loop), HOST, PORT)

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