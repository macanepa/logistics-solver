import os
import sys

import model
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

def check_argument():
    if len(sys.argv) == 2:
        arg = sys.argv[-1]
        arg = os.path.join(os.getcwd(), arg)
        if os.path.isdir(arg):
            mc.mcprint(text="Input Data Directory: ({})".format(arg),
                       color=mc.Color.GREEN)
            ConfigFiles.DIRECTORIES["input_data"] = arg
        else:
            mc.register_error(error_string="The path '{}' doesn't exist".format(arg))
            mc.mcprint(text="Using default directory ({})".format(ConfigFiles.DIRECTORIES["input_data"]),
                       color=mc.Color.YELLOW)
    elif len(sys.argv) > 2:
        mc.register_error(error_string="Solver doesn't accept more than 1 argument")
        mc.exit_application(enter_quit=True)

def initialize():
    mc.mcprint(text="Initializing Solver...")
    check_argument()
    initialize_directories()
    import_data()

def import_data():
    mc.mcprint(text="Do some magic importing the data from the csv files :D",
               color=mc.Color.PINK)
    mc.mcprint(text="The current folder is ({})".format(ConfigFiles.DIRECTORIES["input_data"]),
               color=mc.Color.PINK)

def select_input_data_folder():
    list_dir = os.listdir(os.getcwd())
    menu_list = []
    for directory in list_dir:
        if not os.path.isfile(directory):
            menu_list.append(directory)

    mc_import_data = mc.Menu(title="Import Input Data", subtitle="Select the file to import",
                             options=menu_list, back=False)
    selected_index = int(mc_import_data.show())
    selected_folder = menu_list[selected_index - 1]
    ConfigFiles.DIRECTORIES["input_data"] = os.path.join(os.getcwd(), selected_folder)
    mc.mcprint(ConfigFiles.DIRECTORIES["input_data"], color=mc.Color.GREEN)
    return selected_folder

def import_input_data():
    select_input_data_folder()
    import_data()
    # TODO: Import the data to the dictionary at Class Data

def optimize():
    Data.INPUT_DATA["Remove Me"] = False
    # Only if data has been loaded properly
    if Data.INPUT_DATA.keys():
        # mc.mcprint(text="There is data",
        #            color=mc.Color.GREEN)
        print(mc.Color.GREEN)
        cwd = os.getcwd()
        os.chdir(ConfigFiles.DIRECTORIES["output"])  # Change dir to write the problem in output folder
        model.model.writeProblem()
        print(mc.Color.PURPLE)
        model.model.optimize()
        os.chdir(cwd)  # Head back to original working directory
        print(mc.Color.RESET)
    else:
        mc.mcprint(text="There is no data",
                   color=mc.Color.RED)

def display_information():
    text = "Displaying Information\n" \
           "\t- Input Data Directory: {}\n" \
           "\t- Objective Function: {}\n" \
           "\t- Other Stuff...".format(ConfigFiles.DIRECTORIES["input_data"], model.model.getObjective())

    mc.mcprint(text=text,
               color=mc.Color.PURPLE)