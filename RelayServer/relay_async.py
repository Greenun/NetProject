import asyncio
import sys
import json
import logging
import datetime

SERVER_ADDR = ('127.0.0.1', 42001)

class RelayAsync():
	def __init__(self, server_addr, loop):
		self.loop = loop
		self.address = server_addr[0]
		self.port = server_addr[1]

		self.server = self.loop.run_until_complete(asyncio.start_server(self.accept_connection, "", self.port, loop=self.loop))

	async def accept_connection(self):
		print("Connection Accepted : {0}\nFrom Address : {1}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), writer.get_extra_info('peername')))


	async def handle_connection(self):
		pass

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
