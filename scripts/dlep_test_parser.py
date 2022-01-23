from scripts.test_parser import TestsParser


class DlepTestParser(TestsParser):
    def __init__(self, file):
        super().__init__(file)
        self.list_of_dlep_commands = {}
        

    # this function takes a line and cut it's pieces which are shown in self.list_of_commands 
    def parse_into_variables(self, str):
        print()