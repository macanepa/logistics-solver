import json


def get_dict_from_json(path):
    with open(path, "r") as json_file:
        dictionary = json.load(json_file)
    return dictionary


def generate_json(path, dictionary):
    with open(path, "w") as json_file:
        json.dump(dictionary, json_file)
