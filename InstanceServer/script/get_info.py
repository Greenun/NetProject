import subprocess
import sys
import asyncio
import json
import datetime

RELAY_AD = ('10.0.8.16', 42001)

def get_info():
	cmd = 'xentop -b -i 2 -d 1'
	info_str = subprocess.check_output(cmd.split()).decode()
	info_list = info_str.split('\n')
	info_list.pop()

	guest_num = int((len(info_list) / 2) - 2)
	if guest_num <= 0:
		print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": No Guest")
		return 0

	target = info_list[(-1)*guest_num:len(info_list)]
	main_dict = {}

	for t in target:
		t_list = t.split()
		name = t_list[0]
		cpu = t_list[3]
		network = [t_list[10], t_list[11]]
		bd = [t_list[14], t_list[15]]
		info_dict = {'cpu':cpu, 'network':network, 'bd': bd}
		main_dict[name] = info_dict

	return main_dict

async def send_info():
	info_dict = get_info()
	if not info_dict:
		return 0
	reader, writer = await asyncio.open_connection(RELAY_AD[0], RELAY_AD[1])
	send_dict = {}	
	send_dict['type'] = 'info'
	send_dict['data'] = info_dict
	send_data = json.dumps(send_dict).encode()
	writer.write(send_data)
	writer.write_eof()
	#await writer.drain()



if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.run_until_complete(send_info())
	loop.close()