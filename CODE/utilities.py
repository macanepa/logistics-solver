import os
import sys
from pprint import pprint

import model
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
                if line.strip() == "":
                    continue
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
    data = Data.INPUT_DATA

    if len(data.keys()) == 0:
        raise Exception("There is no data")

    # Generating: Plants
    mc.mcprint(text="Generating Plants")
    ra_a = {}
    for plant in data['plants']:
        ra_a[plant] = data['plants'][plant]['RegionID']

    # Generating: Suppliers
    mc.mcprint(text="Generating Suppliers")
    rs_s = {}
    for supplier in data['suppliers']:
        rs_s[supplier] = data['suppliers'][supplier]['RegionID']

    # Generating: Region of Reception (assuming region of reception == region of closest plant)
    mc.mcprint(text="Generating Region of Reception")
    rr_r = {}
    pl_ra = {}
    for reception in data['receptions']:
        closest_plant = data['receptions'][reception]['ClosestAssemblyPlant']
        for plant in data['plants']:
            pl_ra[(reception, plant)] = 0
            if plant == closest_plant:
                rr_r[reception] = data['plants'][plant]['RegionID']
                pl_ra[(reception, plant)] = 1

    # Generating: Supplier Stock
    mc.mcprint(text="Generating Supplier Stock")
    s_s = {}
    for supplier in data['suppliers']:
        s_s[supplier] = int(data['suppliers'][supplier]['ItemAvailability'])

    # Generating: Demand
    mc.mcprint(text="Generating Demand")
    m_ap = {}
    for order_id in data['orders']:
        order = data['orders'][order_id]
        item_id = order['ItemID']
        if item_id in data['items'].keys():
            m_ap[(order['PlantID'], item_id)] = int(order['NumItemsOrdered'])
        else:
            error_message = "{} includes {} but this item has not been declared in the input file".format(order_id,
                                                                                                          item_id)
            raise Exception(error_message)

    # Generating: Tax Supplier -> Reception (changing region)
    mc.mcprint(text="Generating Tax Supplier -> Reception (changing region)")
    t_sd = {}
    for supplier in rs_s:
        for reception in rr_r:
            coordinate = [rr_r[reception], rs_s[supplier]]
            id_ = "_".join(['surcharge'] + coordinate)
            if id_ in data['surcharge'].keys():
                t_sd[(supplier, reception)] = float(data['surcharge'][id_]['TaxPerContainer'].replace(",", "."))
            else:
                t_sd[(supplier, reception)] = 0

    # Generating: Cost of Item (in supplier)
    mc.mcprint(text="Generating Cost of Item (in supplier)")
    cs_sp = {}
    for supplier in data['suppliers']:
        item = data['suppliers'][supplier]['ItemProduced']
        cs_sp[(supplier, item)] = int(data['suppliers'][supplier]['UnitItemCost'])

    # Generating: Cost from Reception -> Supplier (includes taxes)
    mc.mcprint(text="Generating Cost from Reception -> Supplier (includes taxes)")
    corridor_types = [
        'Automatic',
        'Manual',
        'Subcontractor',
    ]
    cor = corridor_types
    k_daj = {}
    for corridor in data['corridor']:
        if not len(corridor.split("_")) > 1:
            continue
        reception, plant = corridor.split("_")[1:]
        for corridor_type in corridor_types:
            corridor_real_type = corridor_type
            corridor_type = "TransportationCostPerContainer" + corridor_type
            total_cost = int(data['corridor'][corridor][corridor_type])
            if corridor_type == corridor_types[2]:
                total_cost += float(data['corridor'][corridor]['TaxPerContainer'].replace(",", "."))
            k_daj[(reception, plant, corridor_real_type)] = total_cost

    # Generating: Handling Cost at Plant
    mc.mcprint(text="Generating Handling Cost at Plant")
    cd_aj = {}
    for plant in data['plants']:
        for corridor_type in corridor_types:
            id_ = "PlantHandlingCostPerContainer" + corridor_type
            cd_aj[(plant, corridor_type)] = 0
            if id_ in data['plants'][plant].keys():
                cd_aj[(plant, corridor_type)] = float(data['plants'][plant][id_].replace(",", "."))

    # Generating: Handling Cost at Reception
    mc.mcprint(text="Generating Handling Cost at Reception")
    cd_dj = {}
    for reception in data['receptions']:
        for corridor_type in corridor_types:
            cd_dj[(reception, corridor_type)] = 0
            id_ = "ReceptionHandlingCostPerContainer" + corridor_type
            if id_ in data['receptions'][reception].keys():
                cd_dj[(reception, corridor_type)] = float(data['receptions'][reception][id_].replace(",", "."))

    # Generating: Transportation Cost from Supplier -> Reception
    mc.mcprint(text="Generating Transportation Cost from Supplier -> Reception")
    ld_sd = {}
    for supplier in data['suppliers']:
        for reception in data['receptions']:
            id_ = "_".join(["route_supplier"] + [supplier, reception])
            if id_ not in data['route_supplier'].keys():
                continue
            ld_sd[(supplier, reception)] = int(data['route_supplier'][id_]['TransportationCostPerContainer'])

    # Generating: Weight for Item
    mc.mcprint(text="Generating Weight for Item")
    f_p = {}
    for item in data['items']:
        f_p[item] = float(data['items'][item]['UnitWeight'])

    # Generating: Max Number of Items per Container
    mc.mcprint(text="Generating Max Number of Items per Container")
    w_p = {}
    for item in data['items']:
        w_p[item] = int(data['items'][item]['MaximumNumPerContainer'])

    # Generating: Max Number of Container from reception -> Pant (using automatic corridor)
    mc.mcprint(text="Generating Max Number of Container from reception -> Pant (using automatic corridor)")
    rca_d = {}
    for reception in data['receptions']:
        rca_d[reception] = int(data['receptions'][reception]['ReceptionMaxNumOfContainersAutomatic'])

    # Generating: Max Weight from Reception -> Plant (using corridor automatic)
    mc.mcprint(text="Generating Max Weight from Reception -> Plant (using corridor automatic)")
    rwa_d = {}
    for reception in data['receptions']:
        rwa_d[reception] = float(data['receptions'][reception]['ReceptionMaxSumOfWeightsAutomatic'].replace(",", "."))

    # Generating: Max Number of Container from Reception -> Plant (using corridor manual)
    mc.mcprint(text="Generating Max Number of Container from Reception -> Plant (using corridor manual)")
    rcm_d = {}
    for reception in data['receptions']:
        rcm_d[reception] = int(data['receptions'][reception]['ReceptionMaxNumOfContainersManual'])

    # Generating: Max Number of Items from Reception -> Plant (using corridor manual)
    mc.mcprint(text="Generating Max Number of Items from Reception -> Plant (using corridor manual)")
    rim_d = {}
    for reception in data['receptions']:
        rim_d[reception] = int(data['receptions'][reception]['ReceptionMaxNumOfItemsManual'])

    # Generating: Binary can send from Reception -> Plant (using corridor ?)
    mc.mcprint(text="Generating Binary can send from Reception -> Plant (using corridor ?)")
    e_da = {}
    for reception in data['receptions']:
        for plant in data['plants']:
            e_da[(reception, plant)] = 0
    for reception in data['receptions']:
        plant = data['receptions'][reception]['ClosestAssemblyPlant'].replace("Assembly", "")
        e_da[(reception, plant)] = 1

    # Generating: Binary can Item use Corridor automatic?
    mc.mcprint(text="Generating Binary can Item use Corridor automatic?")
    i_i = {}
    for item in data['items']:
        is_automatic_compatible = int(data['items'][item]['IsAutomaticCompatible'])
        i_i[item] = 1 if is_automatic_compatible > 0 else 0

    Data.PARAMETERS = {
        'RAa': ra_a,  # Region of plant a
        'RRr': rr_r,  # Region of reception r
        'RSs': rs_s,  # Region of supplier s
        'PLra': pl_ra,
        'Ss': s_s,
        'Map': m_ap,
        'Tsd': t_sd,
        'CSsp': cs_sp,
        'Kdaj': k_daj,
        'CDaj': cd_aj,
        'CDdj': cd_dj,
        'LDsd': ld_sd,
        'Fp': f_p,
        'Wp': w_p,
        'RCAd': rca_d,
        'RWAd': rwa_d,
        'RCMd': rcm_d,
        'RIMd': rim_d,
        'Eda': e_da,
        'COR': cor,
        'Ii': i_i,
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
    mc.mcprint(text="Applying Rollback...", color=mc.Color.ORANGE)
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
    except Exception as e:
        clear_all_data()
        mc.register_error(error_string="The input directory doesn't contain a valid structure")
        mc.register_error(error_string=e)
        return


def optimize():
    # Only if model has been created properly
    if model.Model.model:
        print(mc.Color.GREEN)
        cwd = os.getcwd()
        os.chdir(ConfigFiles.DIRECTORIES["output"])  # Change dir to write the problem in output folder
        model.Model.model.writeProblem()
        print(mc.Color.CYAN)
        model.Model.model.optimize()
        model.display_optimal_information()
        os.chdir(cwd)  # Head back to original working directory
        print(mc.Color.RESET)
    else:
        mc.register_error(error_string="The model hasn't been created properly")


def construct_model():
    try:
        model.build_model(data=Data.INPUT_DATA, parameters=Data.PARAMETERS)
        mc.mcprint(text="Model has been constructed successfully", color=mc.Color.GREEN)
        mc.mcprint(text="\nThe instance is ready to be optimized", color=mc.Color.GREEN)
    except Exception as e:
        mc.register_error(error_string="There was an error generating the model")
        mc.register_error(error_string=e)


def display_parameters():
    pprint(Data.PARAMETERS)
