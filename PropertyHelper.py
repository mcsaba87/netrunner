import os
import yaml


class PropertyHelper:

    PROPERTY_TYPES = ["ros_address", "ros_username", "ros_password", "cleanup", "netrunner_subnet",
                      "verbose", "testTimeout", "insertTestData", "syslogServer", "syslogPort", "runTestsCron"]

    PROPERTIES_FILE="properties.yml"
    properties = yaml.safe_load(open(PROPERTIES_FILE))

    # returns the value of the requested property, preferring environment variables and falling back to properties.yml
    def getProperty(self, property_type: PROPERTY_TYPES):
        try:
            return os.getenv(property_type,self.properties[property_type])
        except:
            return None

    def getAll(self):
        ret = dict()
        for x in self.PROPERTY_TYPES:
            ret[x] = self.getProperty(x)
        return ret