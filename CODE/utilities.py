import os
import sys
from pprint import pprint

import model
# from model import Model as model
from mcutils import menu_manager as mc


class ConfigFiles:
    DIRECTORIES = {"input_data": "{}".format(os.path.join(os.getcwd(), "input_data")),
                   "output": "{}".format(os.path.join(os.getcwd(), "output"))}

class Data:
    INPUT_DATA = {}
    PARAMETERS = {}

def initialize_directories():
    current_directories = os.listdir()
    for directory_name in ConfigFiles.DIRECTORIES:
        if directory_name not in current_directories:
            directory_path = os.path.join(os.getcwd(), directory_name)
            mc.mcprint(text="The directory '{}' doesn't exists.".format(directory_path),
                       color=mc.Color.ORANGE)
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
    import_input_data()

def print_input_data():
    print(mc.Color.PINK)
    pprint(Data.INPUT_DATA)
    print(mc.Color.RESET)

def import_data():
    mc.mcprint(text="Importing from data input directory", color=mc.Color.ORANGE)
    mc.mcprint(text="The current directory is ({})".format(ConfigFiles.DIRECTORIES["input_data"]),
               color=mc.Color.ORANGE)

    path_dirs = {}
    input_data_path = ConfigFiles.DIRECTORIES["input_data"]
    for directory in os.listdir(input_data_path):
        path_dirs[directory] = os.path.join(input_data_path, directory)

    exclude = ['corridor.csv', 'surcharge.csv', 'route_supplier.csv']
    for file_name in path_dirs:
        path = path_dirs[file_name]
        with open(path) as file:
            object_data = {}
            first_line = True
            headers = []
            for line in file:
                if first_line:
                    if file_name in exclude:
                        headers = line.strip().split(";")
                    else:
                        headers = line.strip().split(";")[1:]
                    first_line = False
                    continue

                if file_name not in exclude:
                    split = line.strip().split(";")
                    object_data[split[0]] = {}
                    for index, attribute in enumerate(split[1:]):
                        object_data[split[0]][headers[index]] = attribute
                else:
                    split = line.strip().split(";")
                    object_data["_".join([file_name.split(".")[0]] + split[:2])] = {}
                    for index, attribute in enumerate(split):
                        object_data["_".join([file_name.split(".")[0]] + split[:2])][headers[index]] = attribute

        Data.INPUT_DATA[file_name.split(".")[0]] = object_data
    if len(Data.INPUT_DATA) == 0:
        raise Exception("No compatible data has been found. "
                        "Please please insert valid data or change the input data directory")

def create_parameters():
    # MM = 0
    data = Data.INPUT_DATA

    if len(data.keys()) == 0:
        raise Exception("There is no data")

    # Region of plant a
    RAa = {}
    for plant in data['plants']:
        RAa[plant] = data['plants'][plant]['RegionID']

    # Region of supplier s
    RSs = {}
    for supplier in data['suppliers']:
        RSs[supplier] = data['suppliers'][supplier]['RegionID']

    # Region of reception r (assuming region of reception = region of closest plant)
    RRr = {}
    PLra = {}
    for reception in data['receptions']:
        for plant in data['plants']:
            PLra[(reception, plant)] = 0
    for reception in data['receptions']:
        closest_plant = data['receptions'][reception]['ClosestAssemblyPlant']
        for plant in data['plants']:
            if plant == closest_plant:
                RRr[reception] = data['plants'][plant]['RegionID']
                PLra[(reception, plant)] = 1
                break


    # Supplier Stock
    Ss = {}
    for supplier in data['suppliers']:
        Ss[supplier] = int(data['suppliers'][supplier]['ItemAvailability'])

    # Assembly pant demand
    Map = {}
    for order in data['orders'].values():
        Map[(order['PlantID'], order['ItemID'])] = int(order['NumItemsOrdered'])

    # Tax from supplier to reception
    Tsd = {}
    # for surcharge in data['surcharge']:
    for supplier in RSs:
        for reception in RRr:
            coordinate = [RSs[supplier],RRr[reception]]
            id_ = "_".join(['surcharge'] + coordinate)
            Tsd[supplier, reception] = 0
            if id in data['surcharge'].keys():
                Tsd[supplier, reception] = data['surcharge'][id_]

    # Cost of item in supplier
    CSsp = {}
    for supplier in data['suppliers']:
        item = data['suppliers'][supplier]['ItemProduced']
        CSsp[(supplier, item)] = int(data['suppliers'][supplier]['UnitItemCost'])

    # Total cost from reception d to plant a using corridor j (including taxes)
    Kdaj = {}

    corridor_types =[
    'Automatic',
    'Manual',
    'Subcontractor',
    ]

    COR = corridor_types

    for corridor in data['corridor']:
        reception, plant = corridor.split("_")[1:]
        # print(data['corridor'][corridor])
        for corridor_type in corridor_types:
            corridor_real_type = corridor_type
            corridor_type = "TransportationCostPerContainer" + corridor_type
            total_cost = int(data['corridor'][corridor][corridor_type])
            total_cost += float(data['corridor'][corridor]['TaxPerContainer'].replace(",",".")) if corridor_type == corridor_types[2] else 0
            Kdaj[(reception, plant, corridor_real_type)] = total_cost


    # Handling Cost in plant a using corridor j
    CDaj = {}
    for plant in data['plants']:
        for corridor_type in corridor_types:
            id_ = "PlantHandlingCostPerContainer" + corridor_type
            CDaj[(plant, corridor_type)] = 0
            if id_ in data['plants'][plant].keys():
                CDaj[(plant, corridor_type)] = float(data['plants'][plant][id_].replace(",","."))

    # Handling Cost in reception using corridor j
    CDdj = {}
    # TODO: change model to include automatic handling
    for reception in data['receptions']:
        for corridor_type in corridor_types:
            CDdj[(reception, corridor_type)] = 0
            id_ = "ReceptionHandlingCostPerContainer" + corridor_type
            if id_ in data['receptions'][reception].keys():
                CDdj[(reception, corridor_type)] = float(data['receptions'][reception][id_].replace(",","."))


    # Container transportation cost from supplier to reception
    LDsd = {}
    for route in data['route_supplier']:
        for supplier in data['suppliers']:
            # LDsd[(supplier, reception)] = None
            if supplier == data['route_supplier'][route]['SupplierID']:
                reception = data['route_supplier'][route]['ReceptionID']
                LDsd[(supplier, reception)] = int(data['route_supplier'][route]['TransportationCostPerContainer'])

    # Weight of item p
    Fp = {}
    for item in data['items']:
        Fp[item] = float(data['items'][item]['UnitWeight'])

    # Max number of items per container
    Wp = {}
    for item in data['items']:
        Wp[item] = int(data['items'][item]['MaximumNumPerContainer'])

    # Max number of container from reception d using corridor automatic
    RCAd = {}
    for reception in data['receptions']:
        RCAd[reception] = int(data['receptions'][reception]['ReceptionMaxNumOfContainersAutomatic'])

    # Max weight from reception d using corridor automatic
    RWAd = {}
    for reception in data['receptions']:
        RWAd[reception] = float(data['receptions'][reception]['ReceptionMaxSumOfWeightsAutomatic'].replace(",","."))

    # Max number of container from reception d using corridor manual
    RCMd = {}
    for reception in data['receptions']:
        RCMd[reception] = int(data['receptions'][reception]['ReceptionMaxNumOfContainersManual'])

    # Max number of items from reception d using corridor manual
    RIMd = {}
    for reception in data['receptions']:
        RIMd[reception] = int(data['receptions'][reception]['ReceptionMaxNumOfItemsManual'])

    # Binary, can you send from reception d to plant a? (this is for corridor type 2)
    Eda = {}
    for reception in data['receptions']:
        for plant in data['plants']:
            Eda[(reception, plant)] = 0
    for reception in data['receptions']:
        plant = data['receptions'][reception]['ClosestAssemblyPlant'].replace("Assembly", "")
        Eda[(reception, plant)] = 1



    Data.PARAMETERS = {
        'RAa': RAa,  # Region of plant a
        'RRr': RRr,  # Region of reception r
        'RSs': RSs,  # Region of supplier s
        'PLra': PLra,
        'Ss': Ss,
        'Map': Map,
        'Tsd': Tsd,  # TODO: temporary 0, but should be present inside .csv Total cost from supplier to reception
        'CSsp': CSsp,
        'Kdaj': Kdaj,  # TODO: include tax # Done
        'CDaj': CDaj, # TODO: done
        'CDdj': CDdj,  # TODO: done
        'LDsd': LDsd,
        'Fp': Fp,
        'Wp': Wp,
        'RCAd': RCAd, # TODO: done
        'RWAd': RWAd, # TODO: done
        'RCMd': RCMd, # TODO: done
        'RIMd': RIMd, # TODO: done
        'Eda': Eda,
        'COR': COR, # the three different corridor types
    }

def select_input_data_folder():
    list_dir = os.listdir(os.getcwd())
    excluded_dirs = ['output',
                     '__pycache__',
                     'mcutils']
    menu_list = []
    for directory in list_dir:
        if not os.path.isfile(directory) and directory not in excluded_dirs:
            menu_list.append(directory)

    mc_import_data = mc.Menu(title="Import Input Data", subtitle="Select the directory to import",
                             options=menu_list, back=False)
    selected_index = int(mc_import_data.show())
    selected_folder = menu_list[selected_index - 1]
    ConfigFiles.DIRECTORIES["input_data"] = os.path.join(os.getcwd(), selected_folder)
    mc.mcprint(ConfigFiles.DIRECTORIES["input_data"], color=mc.Color.GREEN)
    return selected_folder

def clear_all_data():
    mc.mcprint(text="Removing all data!!!", color=mc.Color.ORANGE)
    Data.INPUT_DATA = {}
    Data.PARAMETERS = {}
    model.reset_model()
def import_input_data(select_new_folder=False):
    try:
        select_input_data_folder() if select_new_folder else None
        mc.mcprint(text="Importing raw data", color=mc.Color.ORANGE)
        import_data()
        mc.mcprint(text="The data has been imported successfully", color=mc.Color.GREEN)
        mc.mcprint(text="Generating parameters from input data", color=mc.Color.ORANGE)
        create_parameters()
        mc.mcprint(text="Parameters has been generated successfully", color=mc.Color.GREEN)
        mc.mcprint(text="Constructing Model", color=mc.Color.ORANGE)
        construct_model()
        mc.mcprint(text="Model has been constructed successfully", color=mc.Color.GREEN)
        mc.mcprint(text="\nThe instance is ready to be optimized", color=mc.Color.GREEN)
        # print_input_data()
        # clear_all_data()
    except Exception as e:
        clear_all_data()
        mc.register_error(error_string="The input directory doesn't contain a valid structure")
        mc.register_error(error_string=e)
        return
    # TODO: Import the data to the dictionary at Class Data

def optimize():
    # Only if model has been created properly
    if model.Model.model:
        # mc.mcprint(text="There is data",
        #            color=mc.Color.GREEN)
        print(mc.Color.GREEN)
        cwd = os.getcwd()
        os.chdir(ConfigFiles.DIRECTORIES["output"])  # Change dir to write the problem in output folder
        model.Model.model.writeProblem()
        print(mc.Color.PURPLE)
        model.Model.model.optimize()
        model.display_optimal_information()
        os.chdir(cwd)  # Head back to original working directory
        print(mc.Color.RESET)
    else:
        mc.register_error(error_string="The model hasn't been created properly")

def display_information():
    text = "Displaying Information\n" \
           "\t- Input Data Directory: {}\n" \
           "\t- Objective Function: {}\n" \
           "\t- Other Stuff...".format(ConfigFiles.DIRECTORIES["input_data"], model.Model.model.getObjective())

    mc.mcprint(text=text,
               color=mc.Color.PURPLE)

def construct_model():
    try:
        model.build_model(data=Data.INPUT_DATA, parameters=Data.PARAMETERS)
    except Exception as e:
        mc.register_error(error_string=e)

def display_parameters():
    pprint(Data.PARAMETERS)
