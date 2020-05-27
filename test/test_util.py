import json


class TestUtils:
    @staticmethod
    def read_json_file(file_path: str):
        file = open("./test/data/{0}".format(file_path))
        data = json.load(file)
        return json.dumps(data, indent=2, sort_keys=True)
