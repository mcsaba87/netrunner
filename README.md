# Purpose
TDD (Test Driven Development) has been around for a long time in IT. This concept has not been utilized in networking before. Netrunner is an attempt to change that and helps to implement TDN (Test Driven Networking) in your network.
Before you implement your access control lists / policies / firewall rules, you can write a set of testcases to verify that the network behaves as intended. 
You can also write test cases in retrospect to monitor for unwanted changes, like a forgotten, permanently temporary 'allow all' rule on your firewall. 

# Requirements
Netrunner uses RouterOS, thus it runs on Mikrotik devices which are able to run containers.
- Mikrotik L009
- Mikrotik RB5009
- Mikrotik hap ax2
- Mikrotik hap ac3
- Mikrotik CCR (adm64)
- Mikrotik CHR (x86 - this can be hosted on various virtualization platforms)
https://help.mikrotik.com/docs/spaces/ROS/pages/84901929/Container


# Build instructions
Install dependencies:
```
apt-get install python3-librouteros
apt-get install python3-flask
apt-get install qemu-user-static
apt-get install podman
systemctl --user restart podman
```

Adapt 'properties.yaml' as needed, then build image and export as tar file:
```
TAG="armv7"
ARCH="linux/arm/v7" # linux/arm/v7, linux/arm64, linux/amd64
podman build   --platform ${ARCH}   --network host -t netrunner:${TAG} .
podman save --format docker-archive netrunner:${TAG} > /tmp/netrunner.tar
```
Upload the image to your router:
```
scp /tmp/netrunner.tar  admin@192.168.74.7:usb1-part1/netrunner.tar
```
Prepare RouterOS configuration:
```
/interface veth add address="" dhcp=no gateway="" gateway6="" mac-address=24:0A:0F:EE:71:4B name=veth1
/interface vlan add interface=bridge name=vlan3999 vlan-id=3999
/ip address add address=172.16.39.1/24 interface=vlan3999 network=172.16.39.0
/interface bridge port add bridge=bridge interface=veth1 pvid=3999
/ip pool add name=netrunner-pool ranges=172.16.39.2/31
/ip dhcp-server network add address=172.16.39.0/24 dns-server=172.16.39.1 gateway=172.16.39.1
/ip dhcp-server add address-pool=netrunner-pool interface=vlan3999 name=netrunner-server
/ip firewall nat add action=masquerade chain=srcnat comment="netrunner default outbound access" src-address=172.16.39.0/24
\# The netrunner webapp will be accessible via 192.168.74.7
/ip firewall nat add action=dst-nat chain=dstnat comment="web access to netrunner" dst-address=192.168.74.7 dst-port=5000 protocol=tcp to-addresses=172.16.39.3 to-ports=5000
```
Set up credentials to your router:
```
/container envs add key=ros_address list=netrunner value=192.168.74.7
/container envs add key=ros_password list=netrunner value=api
/container envs add key=ros_username list=netrunner value=api
```

Run the container:
```
/container add cmd=/entrypoint.sh file=usb1-part1/netrunner.tar interface=veth1 name=netrunner root-dir=usb1-part1/tmp workdir=/app
```
At this point netrunner is running on your router. In case of production environments it is advised to limit access to it with the firewall and to use a proxy with SSL offloading for secure access.
In a lab environment just point your browser at:
```
http://192.168.74.7:5000
```