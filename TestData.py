from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from models import TestCase


class TestData:

    def initTestData(self, db: SQLAlchemy):
        db.create_all()
        connection = db.engine.connect()
        connection.execute(text('delete from test_case;'))
        connection.commit()

        testcase = TestCase()
        testcase.name="Google DNS reachable"
        testcase.type="ping"
        testcase.dstAddr="8.8.8.8"
        testcase.passOnFailure=0
        db.session.add(testcase)

        testcase2 = TestCase()
        testcase2.name="gw reachable"
        testcase2.type="ping"
        testcase2.dstAddr="192.168.73.254"
        testcase2.passOnFailure=0
        db.session.add(testcase2)

        testcase3 = TestCase()
        testcase3.name="webfig reachable"
        testcase3.type="http"
        testcase3.dstAddr="https://192.168.74.254"
        testcase3.passOnFailure=0
        db.session.add(testcase3)

        testcase3 = TestCase()
        testcase3.name="local dns works"
        testcase3.type="udp"
        testcase3.dstPort=53
        testcase3.dstAddr="192.168.74.254"
        testcase3.passOnFailure=0
        db.session.add(testcase3)

        testcase4 = TestCase()
        testcase4.name="lab doesnt resolve dns"
        testcase4.type="udp"
        testcase4.dstPort=53
        testcase4.dstAddr="192.168.74.7"
        testcase4.passOnFailure=1
        db.session.add(testcase4)

        testcase5 = TestCase()
        testcase5.name="no NAS access for guests"
        testcase5.type="http"
        testcase5.dstAddr="192.168.74.240"
        testcase5.srcVlan=75
        testcase5.srcAddr="192.168.75.50/24"
        testcase5.gateway="192.168.75.254"
        testcase5.passOnFailure=1
        db.session.add(testcase5)

        testcase6 = TestCase()
        testcase6.name="NAS access for wifi"
        testcase6.type="http"
        testcase6.dstAddr="192.168.74.240"
        testcase6.srcVlan=73
        testcase6.srcAddr="192.168.73.50/24"
        testcase6.gateway="192.168.73.254"
        testcase6.passOnFailure=0
        db.session.add(testcase6)

        testcase7 = TestCase()
        testcase7.name="remote test case"
        testcase7.type="remote"
        testcase7.dstAddr="192.168.74.254"
        testcase7.srcAddr="192.168.34.251"
        testcase7.passOnFailure=0
        testcase7.aux='{"host":"192.168.34.251", "username":"api", "password":"almaspite"}'
        db.session.add(testcase7)

        db.session.commit()

