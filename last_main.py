from stack import Stack
from data_classes import Error
from YALEX import Yalex
from YAPL import Yapl, LRCERO
import c_styles as cs

yalex_files = ["ya.lex", "ya1.lex"]
yapl_files = ["yapl.lex", "yapl1.lex"]

def compile() -> Stack:
    errores = Stack()
    """ Interpretación de archivos yalex y yapl """
    yalex: Yalex = None
    yapl: Yapl = None
    try:
        yalex = Yalex(yalex_file= yalex_files[0])
    except ValueError as e:
        errores.push(Error(500, str(e), "File"))  
        return errores
    try:
        yapl = Yapl(yapl_file= yapl_files[0], yalex = yalex)
    except ValueError as e:
        errores.push(Error(500, str(e), "File"))  
        return errores
    
    errores.add_stack_on_top(yapl.errors.items)
    errores.add_stack_on_top(yalex.errors.items)
    
    lr0 = LRCERO(yapl)
    estados, transiciones = lr0.estados, lr0.transiciones
    firsts, nexts = lr0.primero, lr0.siguiente
    lr0.render("new_render")
    return errores

def main() -> int:
    compiling_errors = compile()
    if not compiling_errors.isEmpty():
        print("======ERRORES DURANTE COMPILACION======")
        for error in compiling_errors: print(cs.s_red("\t"+str(error)))
        return -1
    
    print(cs.s_green("No hubo errores durante compilacion"))
if __name__ == "__main__":
    procces_result = main()
    if procces_result!=0:
        pass
    else:
        print(cs.s_yellow("Proceso finalizado sin exito"))

    