#!/bin/bash


echo "snmpd:127.0.0.1" >> /etc/hosts.allow
echo "master agentx" >> /etc/snmp/snmpd.conf

# read hie code snippet in https://stackoverflow.com/questions/48684497/snmpget-unknown-user-name

#snmpd -f -Lf snmpd_file.log -C -M /usr/share/snmp/mibs --rwcommunity=public --master=agentx --agentXSocket=tcp:localhost:161 udp:1662 &
snmpd -f -Lf snmpd_file.log -C -M /usr/share/snmp/mibs -c /etc/snmp/snmpd.conf --master=agentx --agentXSocket=tcp:localhost:161 udp:1662 &
#/usr/local/sbin/snmpd -c /var/net-snmp/snmpd.conf -c /usr/local/share/snmp/snmpd.conf -c /etc/snmp/snmpd.conf
service snmpd restart

cd create_snmpd
make example-daemon
./example-daemon -f -Lf subagent_file.log -x tcp:localhost:161 &

# keeps the container alive:
while true; do
    sleep 5
done
