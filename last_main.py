from stack import Stack
from data_classes import Error, Response
from Yalex_pickle import YalexPickle
from YALEX import Yalex
from YAPL import Yapl, LRCERO
import c_styles as cs
from pre_run import simulacion_input, build_yalex_pickles, yalex_output_to_parser
from Tokenized_AFD import render_super_afn, SuperAFN, file_into_list

yalex_files = ["ya.lex", "ya1.lex"]
yapl_files = ["yapl.lex", "yapl1.lex"]

def compile(indice_programa = 0, input_file = "input", ) -> Stack:
    if indice_programa>1:
        print(cs.s_yellow("Indice de programa no valido"))
        return
    errores = Stack()
    yalex_filename: str = yalex_files[indice_programa]
    yapl_filename: str = yapl_files[indice_programa]

    yalex: Yalex = None
    yapl: Yapl = None
    yalex_precompiled: YalexPickle  = build_yalex_pickles(create_unexisting=False)[indice_programa]

    try:
        yalex = Yalex(yalex_file= yalex_filename)
    except ValueError as e:
        errores.push(Error(500, str(e), "File"))  
        return errores
    try:
        yapl = Yapl(yapl_file= yapl_filename, yalex = yalex)
    except ValueError as e:
        errores.push(Error(500, str(e), "File"))  
        return errores
    
    errores.add_stack_on_top(yapl.errors.items)
    errores.add_stack_on_top(yalex.errors.items)
    
    lr0 = LRCERO(yapl)
    lr0.render(f"lr0_{indice_programa}")
    print(lr0.parser_table)
    if yalex_precompiled.state == "non-defined":
        print(cs.s_yellow("Programa no ha sido previamente cargado, no es posible seguir"))
    #Simulacion de cadenas de input con automatas pre compilados
    super_automat: SuperAFN = yalex_precompiled.super_afn
    output_simulacion_inicial = "output0"
    response: Response = simulacion_input(superafn=super_automat, filename_input=input_file, output=output_simulacion_inicial)
    if not response.success:
        errores.add_stack_on_top(response.errors.items)
        return errores
    response, tokens_input = yalex_output_to_parser(output_simulacion_inicial)
    if not response.success:
        errores.add_stack_on_top(response.errors.items)
        return errores
    print(tokens_input)
    result, belongs = lr0.parse_input(tokens_input)
    if not result.success:
        errores.add_stack_on_top(result.errors.items)
        return errores 
    if result.status != 200:
        errores.add_stack_on_top(result.errors.items)

    pertenece_string = cs.s_green("El input si es aceptado por la gramatica") if belongs else cs.s_yellow("El input no es aceptado")
    print(cs.s_bold(cs.s_underline(pertenece_string)))
    return errores

def main() -> int:
    compiling_errors = compile()
    if not compiling_errors.isEmpty():
        print(cs.s_black("======ERRORES DURANTE COMPILACION======"))
        for error in compiling_errors.items: print(cs.s_red(str(error)))
        return -1
    
    print(cs.s_green("No hubo errores durante compilacion"))
if __name__ == "__main__":
    procces_result = main()
    if procces_result!=0:
        pass
    else:
        print(cs.s_yellow("Proceso finalizado sin exito"))

    