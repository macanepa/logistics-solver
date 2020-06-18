import colorama

class Color_Settings:
    is_dev=False
    print_color=True

class Color:
    BLUE = colorama.Fore.BLUE
    RED = colorama.Fore.RED
    GREEN = colorama.Fore.GREEN
    CYAN = colorama.Fore.CYAN
    BLACK = colorama.Fore.BLACK
    YELLOW = colorama.Fore.YELLOW
    MAGENTA = colorama.Fore.MAGENTA
    WHITE = colorama.Fore.WHITE

def mcprint(text="", format="", color=None):
    if not Color_Settings.is_dev:
        colorama.init(convert=True)

    text = "{}{}".format(format, text)
    if color and Color_Settings.print_color==True:
        text = "{}{}{}".format(color, text, colorama.Fore.RESET)
    print(text)
