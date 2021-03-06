import asyncio
import sys
import logging
import datetime
from client_handler import *
from transfer_unit import *
from code_handler import *
import json

SERVER_ADDR = ('10.0.8.16', 42000)#0.0.0.0
#command 전송 및 login 관련 관리

class RelayMain(asyncio.Protocol):
	def __init__(self, loop):
		self.stream_data = {}
		self.transport = None
		self.loop = loop
		self.client_address = ''

	def connection_made(self, transport):
		self.transport = transport
		self.client_address = transport.get_extra_info('peername')
		print('address: {0}'.format(self.client_address))

	def data_received(self, data):
		data = json.loads(data.decode())
		req_type, info_data = extract(data)
		clnt_handler = ClientHandler(info_data, get_type(req_type), self.loop, self.client_address)
		return_code = clnt_handler()
		code_handler = CodeHandler(return_code, self.transport)
		code_handler.run_handler()

		self.transport.write_eof()

	def eof_received(self):
		print('End Of File')
		return True

	def connection_lost(self, err):
		print('Server Connection Lost : {0}'.format(err))


if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	coro = loop.create_server(lambda: RelayMain(loop), *SERVER_ADDR)
	server = loop.run_until_complete(coro)

	print('Start Server Address : {0}\nPort : {1}'.format(*SERVER_ADDR))

	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass
	finally:
		server.close()
		loop.run_until_complete(server.wait_closed())
		loop.close()