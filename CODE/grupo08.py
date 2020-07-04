import utilities
from mcutils import menu_manager as mc

mc.ColorSettings.print_color = True
mc.ColorSettings.is_dev = True
mc.LogSettings.display_logs = True
utilities.initialize()

about = mc.Credits(authors=["Matías Cánepa",
                            "Javiera Araya",
                            "Ignacio Chocair",
                            "Florencia Peralta",
                            "Isidora Ramirez"],
                   team_name="Team 8",
                   github_account="macanepa",
                   email_address="macanepa@miuandes.cl",
                   company_name="TDB")

mf_exit_application = mc.MenuFunction(title="Exit", function=mc.exit_application)
mf_import_input_data = mc.MenuFunction("Change Input Data Folder", utilities.import_input_data, *[True])
mf_optimize = mc.MenuFunction(title="Optimize", function=utilities.optimize)
mf_about = mc.MenuFunction(title="About", function=about.print_credits)
mf_display_input_data = mc.MenuFunction(title="Display Input Data", function=utilities.print_input_data)
mf_display_parameters = mc.MenuFunction(title="Display Parameters", function=utilities.display_parameters)

mc_main_menu = mc.Menu(title="Main Menu",
                       options=[mf_import_input_data, mf_optimize, mf_display_input_data, mf_display_parameters,
                                mf_about, mf_exit_application], back=False)

while True:
    mc_main_menu.show()
