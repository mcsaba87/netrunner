import string

from librouteros import Api, api, connect, plain

from PropertyHelper import PropertyHelper
from app import get_routeros_connection, propertiesHelper
from models import TestCase


class RouterHelper:

    api = None
    properties = None
    propertiesHelper = None

    def get_routeros_connection(self):
        return connect(
            host=self.propertiesHelper.getProperty("ros_address"),
            username=self.propertiesHelper.getProperty("ros_username"),
            password=propertiesHelper.getProperty("ros_password"),
            login_method=plain
        )

    def __init__(self):
        self.propertiesHelper = PropertyHelper()
        RouterHelper.api = get_routeros_connection()

    def setupTestcase(self, testCase: TestCase):
        interface = self.addVlanInterface(testCase.srcVlan)
        self.addIpAddress(testCase.srcAddr, interface)
        self.addRoute(testCase.dstAddr, testCase.gateway)
        self.addSrcNat(propertiesHelper.getProperty('netrunner_subnet'), testCase.srcAddr)


    def identity(self):
        return list(api.path("system", "identity"))[0]

    def addVlanInterface(self, vlanID: int):

        #resolve bridge name
        bridges = self.api("/interface/bridge/print")
        if not bridges:
            raise RuntimeError("No bridge interface found")
        bridge_name = next(bridges)["name"]

        #add vlan interface if not present
        interface=""
        for v in list (self.api("/interface/vlan/print")):
            if v.get("vlan-id") == vlanID:
                interface=v
        if interface == "":
            reply = list(self.api("/interface/vlan/add", **{"name": "vlan"+str(vlanID), "vlan-id": str(vlanID), "interface": bridge_name, "comment": "NETRUNNER"}))

        return str("vlan"+str(vlanID))

    def addIpAddress(self, addr: string, interface: string):
        address=""
        for v in list(self.api("/ip/address/print")):
            if v.get("interface") == str(interface):
                address=v
        if address=="":
            #adds ip address
            list(self.api("/ip/address/add", **{"interface": interface, "address": addr, "comment": "NETRUNNER"}))

    def addSrcNat(self, srcAddr: string, toAddr: string):
        #set up NAT
        reply = list(self.api("/ip/firewall/nat/add", **{"src-address": srcAddr, "chain": "srcnat", "action": "src-nat", "to-addresses": toAddr.split("/")[0], "comment": "NETRUNNER"}))
        rule_id = reply[0]["ret"]
        #move to the top
        list(self.api("/ip/firewall/nat/move", **{".id": rule_id, "destination": "0"}))

    def addRoute(self, dstAddr, gateway):
        list(self.api("/ip/route/add", **{"dst-address": dstAddr, "gateway": gateway, "comment": "NETRUNNER"}))

    def cleanup(self):

        if (propertiesHelper.getProperty("cleanup")):
            print("Cleaning up router...")

            for route in list(self.api("/ip/route/print")):
                if route.get("comment")=="NETRUNNER":
                    list(self.api("/ip/route/remove", **{".id": route[".id"]}))

            natRules = list(self.api("/ip/firewall/nat/print"))
            for v in natRules:
                if v.get("comment")=="NETRUNNER":
                    list(self.api("/ip/firewall/nat/remove", **{".id": v[".id"]}))

            addresses = list(self.api("/ip/address/print"))
            for v in addresses:
                if v.get("comment")=="NETRUNNER":
                    list(self.api("/ip/address/remove", **{".id": v[".id"]}))

            vlans = list(self.api("/interface/vlan/print"))
            for v in vlans:
                if v.get("comment")=="NETRUNNER":
                    list(self.api("/interface/vlan/remove", **{".id": v[".id"]}))

        #api.close()