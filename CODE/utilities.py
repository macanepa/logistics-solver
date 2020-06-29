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
    create_parameters()
    construct_model()

def print_input_data():
    print(mc.Color.PINK)
    pprint(Data.INPUT_DATA)
    print(mc.Color.RESET)

def import_data():
    mc.mcprint(text="Do some magic importing the data from the csv files :D",
               color=mc.Color.PINK)
    mc.mcprint(text="The current folder is ({})".format(ConfigFiles.DIRECTORIES["input_data"]),
               color=mc.Color.PINK)
    # Use correct directory

    path_dirs = {}
    input_data_path = ConfigFiles.DIRECTORIES["input_data"]
    for directory in os.listdir(input_data_path):
        path_dirs[directory] = os.path.join(input_data_path, directory)

    data = {}
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

def create_parameters():

    data = Data.INPUT_DATA

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
    for reception in data['receptions']:
        closest_plant = data['receptions'][reception]['ClosestAssemblyPlant']
        for plant in data['plants']:
            if plant == closest_plant:
                RRr[reception] = data['plants'][plant]['RegionID']
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
            pprint(data['surcharge'])
            print(id_)
            Tsd[tuple(coordinate)] = 0
            if id in data['surcharge'].keys():
                Tsd[tuple(coordinate)] = data['surcharge'][id_]

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
            if id_ in data['plants'][plant].keys():
                CDaj[(plant, corridor_type)] = float(data['plants'][plant][id_].replace(",","."))

    # Handling Cost in reception using corridor j
    CDdj = {}
    # TODO: change model to include automatic handling
    for reception in data['receptions']:
        for corridor_type in corridor_types:
            id_ = "ReceptionHandlingCostPerContainer" + corridor_type
            if id_ in data['receptions'][reception].keys():
                CDdj[reception] = float(data['receptions'][reception]['ReceptionHandlingCostPerContainerManual'].replace(",","."))


    # Container transportation cost from supplier to reception
    LDsd = {}
    for route in data['route_supplier']:
        supplier = data['route_supplier'][route]['SupplierID']
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
        RCAd[reception] = data['receptions'][reception]['ReceptionMaxNumOfContainersAutomatic']

    # Max weight from reception d using corridor automatic
    RWAd = {}
    for reception in data['receptions']:
        RWAd[reception] = data['receptions'][reception]['ReceptionMaxSumOfWeightsAutomatic']

    # Max number of container from reception d using corridor manual
    RCMd = {}
    for reception in data['receptions']:
        RCMd[reception] = data['receptions'][reception]['ReceptionMaxNumOfContainersManual']

    # Max number of items from reception d using corridor manual
    RIMd = {}
    for reception in data['receptions']:
        RIMd[reception] = data['receptions'][reception]['ReceptionMaxNumOfItemsManual']

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
    }

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
    try:
        select_input_data_folder()
        import_data()
        print_input_data()
    except:
        mc.register_error(error_string="The directory doesn't contain a valid structure")
        return
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
        model.display_optimal_information()
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

def construct_model():
    model.build_model(data=Data.INPUT_DATA, parameters=Data.PARAMETERS)
    mc.mcprint(text="Model Constructed Successfully", color=mc.Color.ORANGE)

def display_parameters():
    pprint(Data.PARAMETERS)
