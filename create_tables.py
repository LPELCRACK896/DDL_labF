from stack import Stack
from data_classes import Error
    

def get_tabla_de_acciones(estados: list, trancisiones, producciones: dict, siguiente, terminales, errores = Stack()):
    
    final = estados.pop()
    if len(final) != 0:
        errores.push(Error(500, "Error en el último estado de LR0", "LABF" ))
        return None, errores
    
    producciones_l = [(variable, tuple(derivado)) for variable, cadenas_de_derivacion in producciones.items() for derivado in cadenas_de_derivacion]
    producciones_i_d = {(variable, tuple(derivado)): i for i, (variable, cadenas_de_derivacion) in enumerate(producciones.items()) for derivado in cadenas_de_derivacion}

    
    no_terminales = list(producciones.keys())

    for i, estado in enumerate(estados):
        pass


def goto_table(transition, states):
    pass