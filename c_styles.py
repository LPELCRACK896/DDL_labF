BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
UNDERLINE = '\033[4m'
BLINK = '\033[5m'
INVERTED = '\033[7m'
HIDDEN = '\033[8m'

available_styles = {
    "black": BLACK,
    "red": RED,
    "green": GREEN,
    "yellow": YELLOW,
    "blue": BLUE,
    "magenta": MAGENTA,
    "cyan": CYAN,
    "white": WHITE,
    "bold": BOLD,
    "dim": DIM,
    "underline": UNDERLINE,
    "blink": BLINK,
    "inverted": INVERTED,
    "hidden": HIDDEN,
}

def __style(string, style):
    if style not in available_styles.keys():
        print("Estilo no valido")
        return string
    return available_styles.get(style) + string + RESET

def s_green(string):
    return __style(string, "green")

def s_red(string):
    return __style(string, "red")

def s_yellow(string):
    return __style(string, "yellow")

def s_black(string):
    return __style(string, "black")

def s_blue(string):
    return __style(string, "blue")

def s_magenta(string):
    return __style(string, "magenta")

def s_cyan(string):
    return __style(string, "cyan")

def s_white(string):
    return __style(string, "white")

def s_dim(string):
    return __style(string, "dim")

def s_underline(string):
    return __style(string, "underline")

def s_blink(string):
    return __style(string, "blink")

def s_inverted(string):
    return __style(string, "inverted")

def s_hidden(string):
    return __style(string, "hidden")

def s_bold(string):
    return __style(string, "bold")

"""
## Funcion prototype replace t_sttyle -> style_wish
def s_t_sttyle(string):
    return __style(string, "t_sttyle")    
"""


if __name__ =="__main__":
    cadena = "hola putos"

    print(s_underline(s_bold(s_black(cadena))))
    print(s_underline("otro texto"))
    print(cadena)