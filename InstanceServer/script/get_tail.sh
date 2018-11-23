#!/bin/bash
#if last line is specific string, stop and echo

name=$1.log
error_msg='Aborting'
end_msg='Root Password'

while found=`tail -3 /var/log/xen-tools/$name`
do
	#echo $found
	if echo $found | grep -q "$end_msg"
	then
		echo 'Done'
		break
	elif echo $found | grep -q "$error_msg"
	then
		echo 'Error'
		break
	else
		#echo $found
		#echo 'Oh Yeah!'
		sleep 1.5
	fi
done

