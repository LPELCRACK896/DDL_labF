from Tokenized_AFD import render_super_afn, SuperAFN, file_into_list
import os
from yalex_to_regex import read_yalex
from data_classes import Error, Response
from Yalex_pickle import YalexPickle
import pickle
from stack import Stack
from YALEX import Yalex
from YAPL import Yapl, LRCERO
import c_styles as cs

def yalex_output_to_parser(filename_output = "output0"):
    errors = Stack() 
    if not exist_file(filename_output):
        errors.push(f"El archivo {filename_output} no existe en su directorio")
        return Response(400, False, errors), str("")
    lines = None
    with open(filename_output, 'r') as file: lines = file.readlines()
    return Response(200, True, errors) ,[line.strip() for line in lines if line.strip() if not line.strip().startswith("#")]

def exist_file(filename):
    current_dir =  os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(current_dir, filename) 
    return os.path.exists(file_path)

def check_pickle(filename):
    if exist_file(filename):
        print(cs.s_blue(f"File '{filename}' already exist in directory"))
        return True
    print(cs.s_magenta(f"File '{filename}' doesnt exist in directory"))
    return False

def build_single_yalex_pickle(yalex_pickle_target: YalexPickle):
    errores = Stack()
    yalex_filename = yalex_pickle_target.yalex_reference
    try: Yalex(yalex_filename)
    except ValueError as e:
        errores.push(Error(404, str(e), "File not found"))  
        return Response(500, False, errores), None
    reading_yalex_errors, lets, rules, _ = read_yalex(yalex_filename)
    if not lets and not rules:
        errores.add_stack_on_top(reading_yalex_errors.items)
        return Response(500, False, errores), None
    
    sup = SuperAFN(lets, rules)
    _, error = sup.build_lets_regex()
    if error:
        errores.push(Error(500,error, "Coherencia en yalex"))
        return Response(500, False, errores), None
    yalex_pickle_target.super_afn = sup
    yalex_pickle_target.state = "listo"
    
    print(cs.s_cyan("======COMENZANDO CONSTRUCCION SUPER AUTOMATA(ESTO PUEDE TOMAR  MUCHO TIEMPO)======"))
    _, error = sup.build_afds()
    if error:
        errores.push(Error(500, error, "CONSTRUCCION SUPERAUTMOATA"))
        return Response(500, False, errores), None
    with open(yalex_pickle_target.filename, 'wb') as f:
        pickle.dump(yalex_pickle_target, f)
    print(cs.s_green(f"{yalex_pickle_target.filename} fue serializado"))
    with open(yalex_pickle_target.filename, 'rb') as f:
        sup = pickle.load(f)
    return Response(200, True, errores),  sup

def simulacion_input(superafn: SuperAFN, filename_input, output):
    if not exist_file(filename_input):
        print("El archivo input no exxiste en el directorio actual")
        return Response(status=500, success=False, errors = Stack().push(Error(404, f"No se encontro el archivo input '{filename_input}'", "NOT FOUND")))
    f_list, token_or_err = superafn.tokenize_file(file_into_list(filename_input))
    superafn.token_result_into_file_just_token(f_list, token_or_err, output)
    return Response(status = 200, success=True, msg=f"{filename_input} simulado. Resultados en {output}")

def build_yalex_pickles(create_unexisting = True):
    targets = [YalexPickle(filename = "superafn_yalex.pickle", yalex_reference="ya.lex"), YalexPickle(filename = "superafn_yalex1.pickle", yalex_reference="ya1.lex"), YalexPickle(filename = "superafn_yalex_test.pickle", yalex_reference="ya_test.lex")]
    results = []
    for target in targets:
        if check_pickle(target.filename):
            with open(target.filename, 'rb') as f:
                sup = pickle.load(f)
            results.append(sup)
        else:
            if create_unexisting:
                print(cs.s_blue("Creando version compilada"))
                response, sup  = build_single_yalex_pickle(target) 
                response: Response = response
                if not response.success:
                    print(cs.s_yellow("==========================="))
                    print(cs.s_yellow("==========================="))
                    print(cs.s_yellow("No fue posible construir el pickle debido a un fallo en la compilación de yalex y super automata"))
                    print(cs.s_yellow("==========================="))
                    print(cs.s_yellow("==========================="))
                    for error in response.errors.items: print(cs.s_red(str(error)))
                else:
                    results.append(sup)
            else:
                print(cs.s_blue("NO SE CREARA LA version compilada"))
                results.append(target)
    return results

def main():
    response = build_yalex_pickles()
    sup: YalexPickle = response[0]
    superafn: SuperAFN = sup.super_afn
    input_filename = "input"
    simulacion_input(superafn, input_filename, "output0")

if __name__ == "__main__":
    main()