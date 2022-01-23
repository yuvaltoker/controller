
class TestsParser:
    def __init__(self, file):
        # self.list_of_basic_commands includes the key words/signs which later help cutting the test into small pieces 
        self.list_of_basic_commands = {'Name:', 'Test:', '(', 'EXPECT'}
        self.file = file
        self.file_lines = {}
        self.tests = []

    def file_to_lines(self):
        with open(self.file, 'r') as file:
            self.file_lines = file.readlines()
            self.file_lines = [line.rstrip() for line in self.file_lines]
        return self.file_lines

    # this function takes a line and cut it's pieces which are shown in self.list_of_commands 
    def cut_and_parse_into_variables(self, str):
        print()

