from c_styles import *
from Tokenized_AFD import union_afds, SuperAFN
import os

yalex_file = ""
input_file = ""


def __validate_input(question: str , condition_func: callable):
    finish = False
    kill = False
    error = None
    while not (finish or kill):
        res = input(s_bold(s_cyan(f"{question}\n(Ingrese 44 para finaliza programa)\n\n>")))
        if res=="44":
            kill = True
        else:
            res, err, approved = condition_func(res)  
            if approved:
                finish = True
            else:
                error = err
                print(s_red(f"Input invalido:ERR {error}"))

    return res, error, kill


def __validate_ylx_input(filename):
    global yalex_file
    if filename == "":
        if yalex_file != "":
            if os.path.exists(yalex_file):
                return yalex_file, "Yalex correcto.", True
            
            return "Intentelo de nuevo", f"No se encontro el archivo {yalex_file}", False
        
        return "Intentelo de nuevo", "No existe archivo default definido", False 
    
    if os.path.exists(filename):
        yalex_file = filename
        return yalex_file, "Yalex correcto.", True
    
    return "Intentelo de nuevo", f"No se encontro el archivo {yalex_file}", False



def compile():
    kill_all = False
    end_m = False
    error = error
    while not end_m and not kill_all:

        rs_input_file, error, kill_all = __validate_input("Ingrese el nombre del archivo o enter para usar el default ")
        if not kill_all:
            pass
    print(s_cyan("¿?"))
    pass

def run_input():
    pass

def main():
    pass

