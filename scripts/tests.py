# this file will include- TestFile(?), DlepTest, SnmpTest


class TestFile:
    def __init__(self):
        self.dlep_tests = []
        self.snmp_tests = []
        self.name = ''
        self.is_name_set = False

    def set_name(self, name):
        self.name = name
        self.is_name_set = True

class DlepTest:
    def __init__(self):
        print('im dlep test')



class SnmpTest:
    def __init__(self):
        print('im snmp test')