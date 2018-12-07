import asyncio
import sys
import logging
from multiprocessing import Process
import datetime
import json
from instance_handler import *

SERVER_ADDR = ('127.0.0.1', 42000)
#RELAY_ADDR = ('127.0.0.1', 42001)#relay async 주소

class InstanceServer():
	def __init__(self, server_addr, loop):
		self.loop = loop
		self.address = server_addr[0]
		self.port = server_addr[1]
		self.server = self.loop.run_until_complete(asyncio.start_server(self.accept_connection, "", self.port, loop=self.loop))

	async def accept_connection(self, reader, writer):
		print("Connection Accepted : {0}\nFrom Address : {1}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), writer.get_extra_info('peername')))
		data = await reader.read()
		data = json.loads(data.decode())
		print(data)
		if data:
			await self.handle_connection(data, writer)
		else:
			print("No data")


	async def handle_connection(self, data, writer):
		cmd_type = data['type']
		detail = data['detail']
		code = 0
		try:
			if cmd_type == 'create':
				p = Process(target=create_sequence, args=(detail,))
				p.start()
				code = 1
			else:
				handle_instance(cmd_type, detail)
				code = 1
		except ValueError:
			print('Error : No Module Selected. Out Of Range')
		finally:
			if code:
				if not cmd_type == 'create':
					msg = {'type': 'Success', 'data': cmd_type+' Succees'}
					writer.write(json.dumps(msg).encode())
					writer.write_eof()
					await writer.drain()
				else:
					msg = {'type': 'Success', 'data': 'Create Start'}
					writer.write(json.dumps(msg).encode())
					writer.write_eof()
					await writer.drain()
			else:
				msg = {'type': 'Fail', 'data': 'Error Occured while handling '+cmd_type}
				writer.write(json.dumps(msg).encode())
				writer.write_eof()
				await writer.drain()



def main():
	loop = asyncio.get_event_loop()
	server = InstanceServer(SERVER_ADDR, loop)

	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass
	finally:
		loop.close()

if __name__ == '__main__':
	main()
