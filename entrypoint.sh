#!/bin/sh

NIC=`ifconfig -a | sed 's/[ \t].*//;/^\(lo\|\)$/d'`
echo "[+] Starting DHCP client on ${NIC}..."
udhcpc -i ${NIC} -q -b

echo "[+] DHCP acquired, starting Flask app..."
mkdir /log
cd app
exec /venv/bin/python3 app.py > /log/netrunner.log

#don't exit on failure
exec tail -f /dev/null

