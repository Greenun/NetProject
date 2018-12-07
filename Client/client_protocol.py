import asyncio
import time
import json

HOST = '10.0.8.16'#10.0.8.16 --> desktop
PORT = 42000

recv_data = None

class ClientProtocol(asyncio.Protocol):
	def __init__(self, send_data, loop):
		self.send_data = send_data#json dump
		self.transport = None
		self.loop = loop
		self.__done = loop.create_future()
		self.all_data = b''

	def connection_made(self, transport):
		self.transport = transport
		self.address = transport.get_extra_info('peername')
		print('address: {0}\nProtocol: {1}'.format(self.address, self.transport.get_protocol()))
		print(self.send_data)
		self.transport.write(json.dumps(self.send_data).encode())

	def data_received(self, data):
		print('Received From Server : {0}'.format(data))
		self.all_data += data

	def eof_received(self):
		print('End Of File')
		global recv_data
		recv_data = json.loads(self.all_data.decode())
		self.transport.write_eof()
		self.transport.close()
		return True

	def write(self, data):
		self.transport.write(data)

	def connection_lost(self, err):
		print('Connection Lost : {0}'.format(err))
		self.__done.set_result(None)

	def wait_connection_lost(self):
		return self.__done


def main(data):
	loop = asyncio.get_event_loop()
	coro = loop.create_connection(lambda: ClientProtocol(data,loop), HOST, PORT)
	print(coro)

	try:
		transport, protocol = loop.run_until_complete(coro)
		loop.run_until_complete(protocol.wait_connection_lost())
	except KeyboardInterrupt:
		print("what...?")
	finally:
		print('Close Loop')
		return recv_data

def async_listen(shared_dict):
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
	update_dict = {}
	data = await reader.read()
	data = json.loads(data.decode())
	req_type = data['type']
	detail = data['data']
	#print(detail)
	#print(type(detail))
	print(detail['msg'])
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
	x = main('start')