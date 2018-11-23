#!/bin/bash
#Get Xen Guset IP address(Need Guest name)

target_name=$1
network="10.0.8.0/24"
umac=`xl network-list ${target_name} | grep -oh ".\{2\}:.\{2\}:.\{2\}:.\{2\}:.\{2\}:.\{2\}"`

ip=`nmap -sP $network | grep -i -B 2 $umac | grep -oh ".\{1,3\}\..\{1,3\}\..\{1,3\}\..\{1,3\}"`
echo $ip

