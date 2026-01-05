import datetime
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = ""
    testCaseId = db.Column(db.Integer, nullable=False)
    result = db.Column(db.Integer, nullable=False)
    resultMsg = ""
    message = db.Column(db.String(100), nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "testCaseId": self.testCaseId,
            "result": self.result,
            "message": self.message,
            "created_at": self.created_at
        }

class TestCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    #This should be an enum of: ping, http, https, ssh, rdp, dns, tcp, udp
    type = db.Column(db.String(8), nullable=False)
    srcAddr = db.Column(db.String(15), nullable=True)
    srcVlan = db.Column(db.Integer, nullable=True)
    dstAddr = db.Column(db.String(15), nullable=False)
    dstPort = db.Column(db.Integer, nullable=True)
    gateway = db.Column(db.String(15), nullable=True)
    passOnFailure = db.Column(db.Integer, nullable=False)
    aux = db.Column(db.String(50), nullable=True)

    def dup(self):
        ret = self.from_dict(self.to_dict())
        ret.name = ret.name + " [DUP]"
        return ret

    def to_dict(self):
        return {
            #"id": self.id,
            "name": self.name,
            "srcAddr": self.srcAddr,
            "dstAddr": self.dstAddr,
            "srcVlan": self.srcVlan,
            "dstPort": self.dstPort,
            "gateway": self.gateway,
            "passOnFailure": self.passOnFailure,
            "type": self.type,
            "aux": self.aux
        }

    @staticmethod
    def from_dict(data):
        return TestCase(
            name=data["name"],
            srcAddr=data["srcAddr"],
            dstAddr=data["dstAddr"],
            srcVlan=data["srcVlan"],
            dstPort=data["dstPort"],
            gateway=data["gateway"],
            passOnFailure=data["passOnFailure"],
            type=data["type"],
            aux=data["aux"]
        )