import json
import time
import yaml
import os

from flask_sqlalchemy import SQLAlchemy

from Logger import Logger
from TestcaseValidator import TestCaseValidator, TestCaseValidationError
from models import TestCase, TestResult
import subprocess

from RouterHelper import *


def http(testcase: TestCase) -> bool:
    result = subprocess.run(
        ["/bin/sh", "-c", "wget -O /dev/null --no-check-certificate --tries 1 --timeout "+str(propertiesHelper.getProperty('testTimeout'))+" "+testcase.dstAddr],
        capture_output=True,
        text=True
    )
    print(f"Test {testcase.name} says: {result.stdout}")
    if testcase.passOnFailure:
        return bool(result.returncode)
    return not result.returncode


def ping(testcase: TestCase) -> bool:
    result = subprocess.run(
        ["/bin/sh", "-c", "ping -c1 "+testcase.dstAddr],
        capture_output=True,
        text=True
    )
    print(f"Test {testcase.name} says: {result.stdout}")
    if testcase.passOnFailure:
        return bool(result.returncode)
    return not result.returncode

def tcp(testcase: TestCase) -> bool:
    result = subprocess.run(
        ["/bin/sh", "-c", "nc -zv "+testcase.dstAddr+" "+str(testcase.dstPort)],
        capture_output=True,
        text=True
    )
    print(f"Test {testcase.name} says: {result.stdout}")
    if testcase.passOnFailure:
        return bool(result.returncode)
    return not result.returncode

def udp(testcase: TestCase) -> bool:
    result = subprocess.run(
        ["/bin/sh", "-c", "nc -zvu "+testcase.dstAddr+" "+str(testcase.dstPort)],
        capture_output=True,
        text=True
    )
    print(f"Test {testcase.name} says: {result.stdout}")
    if testcase.passOnFailure:
        return bool(result.returncode)
    return not result.returncode

def remote(testcase: TestCase) -> bool:
    auxJson = json.loads(testcase.aux)
    remoteRosApi = connect(
        host=auxJson["host"],
        username=auxJson["username"],
        password=auxJson["password"],
        login_method=plain
    )

    result = list(remoteRosApi("/ping", **{"address": testcase.dstAddr, "count": 1, "src-address": testcase.srcAddr}))
    print(f"Test {testcase.name} says: {result}")
    answerReceived=bool(result[0].get("received"))
    remoteRosApi.close()
    if testcase.passOnFailure:
        return not answerReceived
    return answerReceived

class RunLogic:

    validator = TestCaseValidator()
    propertiesHelper = PropertyHelper()
    logger = Logger(propertiesHelper.getProperty("syslogServer"), propertiesHelper.getProperty("syslogPort"))

    #TODO: do this asynchronously
    def run(self, db: SQLAlchemy, rosApi: Api, testcaseId):

        routerHelper = RouterHelper()
        testcases = None
        if testcaseId is None:
            testcases = TestCase.query.all()
        else:
            testcases = [TestCase.query.get(testcaseId)]

        print("Loaded " + str(len(testcases)) + " testcases.")
        for i in range(len(testcases)):
            testcase = testcases[i]

            result = False
            message = ""

            try:
                self.validator.validate(testcase)

                if not testcase.srcVlan is None and not testcase.srcAddr is None:
                    routerHelper.setupTestcase(testcase)
                    time.sleep(1)

                match testcase.type:
                    case 'ping':
                        result = ping(testcase)
                    case 'http':
                        result = http(testcase)
                    case 'tcp':
                        result = tcp(testcase)
                    case 'udp':
                        result = udp(testcase)
                    case 'remote':
                        result = remote(testcase)
                    case _:
                        print("Invalid test type for testcase "+ str(testcase.id))

                if result:
                    print(f"[OK] {testcase.name}")
                    self.logger.log("[OK]"+testcase.name)
                else:
                    print(f"[FAILED] {testcase.name}")
                    self.logger.log("[FAILED]"+testcase.name)


                if not testcase.srcVlan is None and not testcase.srcAddr is None:
                    print(f"Cleaning up the router after test {testcase.name}")
                    routerHelper.cleanup()
            except TestCaseValidationError as e:
                message = e
                print(f"Validation failed: {e}")

            except RuntimeError as error:
                print(f"Testcase execution failed: {testcase.name}")
                print(f"Testcase execution failed: {error}")
            except Exception as e:
                print(f"This should never happen: {e}")

            try:
                testResult= TestResult()
                testResult.testCaseId = testcase.id
                testResult.result = result
                testResult.message = message
                db.session.add(testResult)
                db.session.commit()
            except RuntimeError as error:
                print(f"Can't save test case: {error}")
            except:
                print("This should never happen2.")


