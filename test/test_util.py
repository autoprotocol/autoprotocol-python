import json


class TestUtils:
    @staticmethod
    def load_json_file(file_path: str):
        file = open("./test/data/{0}".format(file_path))
        return json.load(file)

    @staticmethod
    def read_json_file(file_path: str):
        data = TestUtils.load_json_file(file_path)
        return json.dumps(data, indent=2, sort_keys=True)
