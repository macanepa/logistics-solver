class ColorSettings:
    is_dev = False
    print_color = True


class Color:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    ORANGE = '\033[33m'
    BLUE = '\033[34m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    LIGHTGREY = '\033[37m'
    DARKGREY = '\033[90m'
    LIGHTRED = '\033[91m'
    LIGHTGREEN = '\033[92m'
    YELLOW = '\033[93m'
    LIGHTBLUE = '\033[94m'
    PINK = '\033[95m'
    LIGHTCYAN = '\033[96m'
    RESET = '\033[0m'


def mcprint(text="", format_="", color=None):
    # if not ColorSettings.is_dev:
    # colorama.init(convert=True)

    text = "{}{}".format(format_, text)
    if color and ColorSettings.print_color:
        text = "{}{}{}".format(color, text, Color.RESET)
    print(text)
