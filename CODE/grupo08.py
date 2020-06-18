import os
import sys

import utilities
from mcutils import menu_manager as mc

mc.Color_Settings.print_color = True
mc.Color_Settings.is_dev = True
mc.Log_Settings.display_logs = True
utilities.initialize()

about = mc.Credits(authors=["Matías Cánepa"],
                   team_name="Team 8",
                   github_account="macanepa")

mf_exit_application = mc.Menu_Function(title="Exit", function=mc.exit_application)
mf_import_input_data = mc.Menu_Function(title="Change Input Data Folder", function=utilities.import_input_data)
mf_optimize = mc.Menu_Function(title="Optimize", function=utilities.optimize)
mf_about = mc.Menu_Function(title="About", function=about.print_credits)
mf_display_information = mc.Menu_Function(title="Display Information", function=utilities.display_information)

mc_main_menu = mc.Menu(title="Main Menu", options=[mf_import_input_data, mf_optimize, mf_display_information, mf_about, mf_exit_application], back=False)

while True:
    mc_main_menu.show()