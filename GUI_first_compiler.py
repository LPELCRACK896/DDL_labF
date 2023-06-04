from c_styles import *
from Tokenized_AFD import render_super_afn, SuperAFN, file_into_list
import os
from dataclasses import dataclass
from yalex_to_regex import read_yalex

@dataclass
class MySuperAFN:
    alias: str
    object: SuperAFN
    yalexfile: str

def add_super_afn(alias, replace = False ):
    pass

def validate_input(question: str , condition_func: callable):
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
                error = None
            else:
                error = err
                print(s_red(f"Input invalido:ERR {str(error)}"))

    return res, error, kill

def validate_yalex_file(filename):
    if os.path.exists(filename): 
        return filename, "Archivo encontrado.", True
    return filename, f"No se encontro el archivo yalex {filename} en el directorio actual", False

def seek_menu():
    print(s_magenta("---Menu---"
          +"\n1. Añadir compilador"
          +"\n2. Ejecutar input para compilador"
          +"\n3. Ver compiladores actuales"
          +"\n4. Crear superautomata"
          +"\n5. Salir"
          ))

def seek_compiladores(superafns: dict[str:MySuperAFN]):
    if not superafns:
        print(s_yellow("Aun no sea han compilado compiladores"))
        input("Enter para continuar...")
        return
    print("--Compiladores--\n")
    for i, item in enumerate(superafns):
        print(f"{i+1}. {item} ")
    input("Enter para continuar...")

def lambda_gen_validate_options(options):
    return lambda input: ((input, None, True) if input in options else (False, "No ingreso una opcion valida. Considera las opciones"+str(options), False))

def ui_add_compiler(superafns: dict[str:MySuperAFN]):
    name = input("Ingrese nombre de nuevo compilador(puede reemplazar existente): ")
    if name in superafns:
        print(s_yellow("¡WARNING! Se reemplazara el compilador acctual"))
    filename, error, menu_kill = validate_input("Ingrese el archivo yalex como referencia", validate_yalex_file)
    if menu_kill:
        print(s_red("Forzando cierre"))
        return
    
    if error:
        print(s_red(str(error)))
        return 
    
    errors, lets, rules, r_priority = read_yalex(filename)
    

    if errors:
        for error in errors.items:
            print(s_red(str(error)))
        return 
        
    sup = SuperAFN(lets, rules) #Objeto que quiero serializar
    _, error = sup.build_lets_regex()
    if error:
        print(s_red(error))
        return 
        
    _, error = sup.build_afds()
    if error:
        print(s_red(str(error)))
        return 
    
    superafns[name] = MySuperAFN(name, sup, filename)

def ui_execute_input(superafns: dict[str:MySuperAFN]):
    input_filename, error, menu_kill = validate_input("Ingrese el archivo input que desea probar: ", validate_yalex_file)
    if menu_kill:
        print(s_red("Forzando cierre"))
        return
    
    if error:
        print(s_red(str(error)))
        return    
    
    compiler_alias, error, menu_kill = validate_input("Ingrese el alias del compilador que desea utilizar: ", lambda_gen_validate_options(list(superafns.keys())))
    if menu_kill:
        print(s_red("Forzando cierre"))
        return
    
    if error:
        print(s_red(str(error)))
        return  
    
    my_super_afn: MySuperAFN = superafns[compiler_alias]
    sup: SuperAFN = my_super_afn.object
    
    f_list = file_into_list(input_filename)
    f_list, token_or_err = sup.tokenize_file(f_list)
    token_results_file = input(s_blue("Ingrese el nombre con el que desea guardar el resultado de los tokens: "))
    token_compiled_file = input(s_blue("Ingrese el nombre con el que desea guardar los tokens compilados (py), no incluir extension:"))
    sup.token_results_into_file(f_list, token_or_err, token_results_file)
    sup.complie_tokens(f_list, token_or_err, "tokens", f"{token_compiled_file}.py" )

def ui_render_superafn(superafns: dict[str:MySuperAFN]):
    compiler_alias, error, menu_kill = validate_input("Ingrese el alias del compilador que desea utilizar: ", lambda_gen_validate_options(list(superafns.keys())))
    if menu_kill:
        print(s_red("Forzando cierre"))
        return
    
    if error:
        print(s_red(str(error)))
        return  
    
    my_super_afn: MySuperAFN = superafns[compiler_alias]
    sup: SuperAFN = my_super_afn.object

    name = input(s_blue("Ingrese el nombre con el que desea guardar el PDF: "))
    render_super_afn(sup.token_afds, name)

def main():
    superafns: dict[str:MySuperAFN] = {}
    go = True
    while go:
        seek_menu()
        res, error, menu_kill = validate_input("¿Que opcione desea?", lambda_gen_validate_options(["1", "2", "3","4", "5"]) )
        if not menu_kill:
            if res == "1":
                ui_add_compiler(superafns)
            elif res == "2":
                ui_execute_input(superafns)
            elif res == "3":
                seek_compiladores(superafns)
            elif res == "4":
                ui_render_superafn(superafns)
            else:
                go = False    
        else:
            print(s_red("Finalizando programa forzosamente"))
            go = False



        


if __name__ == "__main__":
    main()
