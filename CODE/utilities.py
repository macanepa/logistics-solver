import os

import model
# import mcutils as mc
from mcutils import menu_manager as mc


class ConfigFiles:
    DIRECTORIES = {"input_data": "{}".format(os.path.join(os.getcwd(), "input_data")),
                   "output": "{}".format(os.path.join(os.getcwd(), "output"))}

class Data:
    INPUT_DATA = {}

def initialize_directories():
    current_directories = os.listdir()
    for directory_name in ConfigFiles.DIRECTORIES:
        if directory_name not in current_directories:
            directory_path = os.path.join(os.getcwd(), directory_name)
            mc.mcprint(text="The directory '{}' doesn't exists.".format(directory_path),
                       color=mc.Color.YELLOW)
            os.mkdir(directory_name)
            mc.mcprint(text="Created '{}' successfully".format(directory_path),
                       color=mc.Color.GREEN)

def initialize():
    initialize_directories()

def get_directories_path(path):
    directories_list = os.listdir(path)



def import_data(file_name):
    with open(file_name, "r") as input_file:
        for index, line in enumerate(input_file):
            Data.INPUT_DATA[index] = line.strip()

def select_input_file():
    list_dir = os.listdir(ConfigFiles.DIRECTORIES["input_data"])
    mc_import_data = mc.Menu(title="Import Input Data", subtitle="Select the file to import",
                             options=list_dir, back=False)
    selected_index = int(mc_import_data.show())
    selected_file = list_dir[selected_index - 1]
    selected_file_path = os.path.join(os.getcwd(), ConfigFiles.DIRECTORIES["input_data"], selected_file)
    return selected_file_path

def import_input_data():
    file_name = select_input_file()
    import_data(file_name)

def optimize():
    if Data.INPUT_DATA.keys():
        mc.mcprint(text="There is data",
                   color=mc.Color.GREEN)
        model.model.optimize()
    else:
        mc.mcprint(text="There is no data",
                   color=mc.Color.RED)
