import asyncio
import sys
import json
import logging
import datetime
from relay_handler import RelayHandler

SERVER_ADDR = ('127.0.0.1', 42001)
RELAY_TYPE = ('info', 'request', 'complete')

class RelayAsync():
	def __init__(self, server_addr, loop):
		self.loop = loop
		self.address = server_addr[0]
		self.port = server_addr[1]

		self.server = self.loop.run_until_complete(asyncio.start_server(self.accept_connection, "", self.port, loop=self.loop))

	async def accept_connection(self, reader, writer):
		print("Connection Accepted : {0}\nFrom Address : {1}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), writer.get_extra_info('peername')))
		data = await reader.read()
		data = json.loads(data.decode())
		print(data)#for debug

		if data:
			await self.handle_connection(data, reader, writer)
		else:
			print("No data")



	async def handle_connection(self, data, reader, writer):
		req_type = data['type']
		detail = data['data']
		handle_relay = RelayHandler(data, req_type, reader, writer, self.loop)
		await handle_relay.modules[RELAY_TYPE.index(req_type)]

def main():
	loop = asyncio.get_event_loop()
	server = RelayAsync(SERVER_ADDR, loop)

	try:
		loop.run_forever()
	except:
		pass
	finally:
		loop.close()

if __name__ == '__main__':
	main()
