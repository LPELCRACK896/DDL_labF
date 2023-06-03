import os
import re
from data_classes import Error, LR0Item, ParserTable
from graphviz import Digraph
from stack import Stack
from YALEX import Yalex
from dataclasses import dataclass
import pandas as pd
import numpy as np

class Yapl():
    def __new__(cls, yapl_file, yalex: Yalex):
        if not cls.check_file(yapl_file):
            raise ValueError(f"Failed to create Yalex object with file {yapl_file}")
        return super(Yapl, cls).__new__(cls)

    def __init__(self, yapl_file, yalex: Yalex) -> None:
        self.errors = Stack()
        self.yapl_file = yapl_file
        self.yalex: Yalex = yalex
        self.body = self.__read()
        self.tokens, self.producciones = self.__extract_token_and_productions()

    @staticmethod
    def check_file(filename:str):
        only_filename, extension = filename.rsplit('.', 1)
        if not extension=="lex":
            print("Invalid extension")
            return False
        current_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(current_dir, filename) 
        if not os.path.exists(file_path):
            print("File doesn't exist in directory")
            return False
        return True

    def __extract_token_and_productions(self):
        self.tokens = None
        self.producciones = {}
        if len(self.body.split("%%"))!=2:
            self.errors.push(Error(500, f"No se encontro el numero preciso de divisiones para el archivo yapl {self.yapl_file}", "FORMAT"))
            return None, None
        seccion_tokens, seccion_producciones = self.body.split("%%")
        self.tokens, self.producciones = self.__extract_tokens(seccion_tokens), self.__extract_producciones(seccion_producciones)
        self.errors.add_stack_on_top([Error(500, f"Formato no adecuado en linea: {linea}", "FORMATFILE") for linea in seccion_tokens.split('\n') if not linea.startswith("%token") and not linea.startswith("IGNORE") and linea.strip()])
        self.errors.add_stack_on_top([Error(404, f"No es posible definir el nombre de una produccion con la de un token: REVISAR: {token}", "VARIABLES") for token in self.tokens if token in self.producciones])
        self.__cross_validate_tokens()
        return self.tokens, self.producciones

    def __extract_tokens(self, seccion_tokens):
        return [word for line in seccion_tokens.split('\n') 
            if line.startswith("%token") 
            for word in line[len("%token"):].strip().split(' ')]

    def __extract_producciones(self, seccion_producciones:str):
        last_variable = None
        rules = []
        for linea in  seccion_producciones.split("\n"):
            linea = linea.strip()
            if linea:
                if linea.endswith(';'):
                    linea = linea[:-1]
                    if linea: rules.append(linea)
                    self.producciones[last_variable] = rules
                    last_variable = None
                    rules = []
                elif linea.endswith(':'):
                    if last_variable:
                        self.producciones[last_variable] = rules
                        rules = []
                    last_variable = linea[:-1]
                elif last_variable:
                    if linea.startswith(('|', '->')): rules.extend([item.strip() for item in linea.split('|') if item.strip()])
                    elif '|' in linea: rules.extend(linea.split('|'))
                    else: rules.append(linea)
        return self.producciones
    
    def __cross_validate_tokens(self):
        valid_tokens = [token for token in self.tokens for lex_token in self.yalex.tokens if token == (lambda token: eval(token[1]))(lex_token)]
        self.errors.add_stack_on_top([Error(400, f"Token \"{token}\" no definidio en yalex-> {self.yalex.filename}", "YALEX-YALP") for token in self.tokens if token not in valid_tokens])
        if (len(valid_tokens))<len(self.yalex.tokens): self.errors.push(Error(400, "Numero de tokens en yalex menor al del yalp", "TOKENS DEFINITION YALEX-YALP"))
        self.tokens = valid_tokens
        return valid_tokens
            
    def __read(self):
        contenido = None
        with open(self.yapl_file, "r") as f: 
            contenido = f.read()
        return re.sub(r'/\*.*?\*/', '', contenido, flags=re.DOTALL)
    
    def get_producciones(self): return {key: [rule.split() for rule in value] for key, value in self.producciones.items()}

class LRCERO():
    
    def __init__(self, yapl: Yapl) -> None:
        self.errores = Stack()
        self.producciones = yapl.get_producciones()
        self.estados, self.transiciones = self.__LR_cannonical_collections()
        self.terminales, self.no_terminales = (lambda producciones: (set(symbol for no_terminal in list(producciones.keys()) for production in producciones[no_terminal] for symbol in production if symbol not in list(producciones.keys())), set(producciones.keys())))(self.producciones)
        self.primero = LL_first_sets(self.producciones, self.terminales, self.no_terminales)
        self.siguientes = LL_follow_sets(self.producciones, self.primero, self.no_terminales)
        self.action_table = pd.DataFrame(index=range(len(self.estados)), columns=list(self.terminales))
        self.goto_table = pd.DataFrame(index=range(len(self.estados)), columns=list(self.no_terminales))
        self.parser_table: pd.DataFrame = self.__build_parser_table()

    def __LR_cannonical_collections(self):
        simbolo_inicial = list(self.producciones.keys())[0]
        simbolo_de_gram_aumentada = f"{simbolo_inicial}'"
        produccion_aumentada, posicion = (simbolo_de_gram_aumentada, [simbolo_inicial]), 0  
        item_i = LR0Item(produccion_aumentada, posicion=posicion)
        estados = [self.__LR_closure([item_i])]
        transiciones = []

        state_stack = Stack()
        state_stack.push(estados[0])

        while not state_stack.isEmpty():
            actual = state_stack.pop()
            for simbolo in  set(simb for item in actual for simb in item.produccion[1][item.posicion:item.posicion + 1]):
                siguiente = self.__LR_goto(actual, simbolo)
                if siguiente:
                    if siguiente not in estados:
                        estados.append(siguiente)
                        state_stack.push(siguiente)
                    transiciones.append((estados.index(actual), simbolo, estados.index(siguiente)))
        aceptacion = len(estados)
        for num_estado, estado in enumerate(estados):
            i = 0
            alcanza_aceptacion = False
            for item in estado:
                if not alcanza_aceptacion:
                    if not item.derivado and item.posicion == len(item.produccion[1]) and  item.produccion[0] == simbolo_de_gram_aumentada:
                        transiciones.append((num_estado, '$', aceptacion))
                        alcanza_aceptacion = True
        estados.append([])
        self.estados = estados
        self.transiciones = transiciones
        return estados, transiciones

    def __LR_goto(self, estado_actual, simbolo):
        return self.__LR_closure([LR0Item(item.produccion, item.posicion + 1) for item in estado_actual if item.posicion < len(item.produccion[1]) and item.produccion[1][item.posicion] == simbolo])

    def __LR_closure(self, items: list):
        encuentra_nuevo = True
        while encuentra_nuevo:
            encuentra_nuevo = False
            temp_items = items.copy()
            for item in temp_items:
                if item.posicion < len(item.produccion[1]) and item.produccion[1][item.posicion] in self.producciones:
                    for produccion in self.producciones[item.produccion[1][item.posicion]]:
                        n_item = LR0Item((item.produccion[1][item.posicion], produccion), 0, True)
                        if n_item not in items:
                            items.append(n_item)
                            encuentra_nuevo = True
            if not encuentra_nuevo: return items

    def __build_parser_table(self) -> pd.DataFrame:
        simbolo_inicial = list(self.producciones.keys())[0]
        simbolo_de_gram_aumentada = f"{simbolo_inicial}'"
        copia_estados = self.estados.copy()
        copia_terminales = list(self.terminales.copy())[:]
        final = copia_estados.pop()
        if len(final)!=0:
            self.errores.push(Error(500, "Espera el ultimo estado vacio", "LABF" ))
            return None
        
        all_producciones = [(llave, tuple(valor)) for llave in self.producciones for valor in self.producciones[llave]]
        i_producciones = {prod: idx for idx, prod in enumerate(all_producciones)}
        self.action_table = self.action_table.fillna(np.nan)
        self.goto_table = self.goto_table.fillna(np.nan)
        for i, estado in enumerate(copia_estados):
            for itemlr in estado:
                variable = itemlr.produccion[0]
                derivacion = itemlr.produccion[1] 
                itemlr: LR0Item = itemlr # Solo para que reconozca el tipo
                if  itemlr.posicion == len(derivacion) and variable == simbolo_de_gram_aumentada : self.action_table.loc[i, '$'] = "A"
                elif itemlr.posicion == len(derivacion):
                   for symb in self.siguientes.get(variable, []):
                       i_produccion = (variable, tuple(derivacion))
                       if symb != "$" and pd.notna(self.action_table.loc[i, symb]): self.errores.push(Error(600, f"ERROR EN GRAMATICA sobre simbolo {symb} - REDUCE", "INCOMPATIBILIDAD GRAMATICA NO SLR"))
                       else: self.action_table.loc[i, symb] = f"R{i_producciones.get(i_produccion, -1)}"
            for transicion in self.transiciones:
                if i == transicion[0]:
                    inicio =  transicion[1]
                    final =  transicion[2]
                    if inicio in self.no_terminales:
                        if pd.notna(self.goto_table.loc[i, inicio]): self.errores.push(Error(600, f"Duplicacion de accion sobre  {inicio}", "INCOMPATIBILIDAD GRAMATICA NO SLR"))
                        self.goto_table.loc[i, inicio] = str(final)
                    elif inicio in self.terminales:
                        if pd.notna(self.action_table.loc[i, inicio]) and inicio != "$": self.errores.push(Error(600, f"Duplicacion de accion sobre  {inicio}", "INCOMPATIBILIDAD GRAMATICA NO SLR"))
                        elif inicio != "$": self.action_table.loc[i, inicio] = f"S{final}"
                    else: self.errores.push(Error(600, f"Valor de trancicions no encontrado en terminales o no termianlles {inicio}", "INCOMPATIBILIDAD GRAMATICA NO SLR"))


        return self.__setup_parser_table()

    def __setup_parser_table(self):
        self.action_table = self.action_table.fillna("-")
        self.goto_table = self.goto_table.fillna("-")
        self.parser_table = pd.concat([self.action_table, self.goto_table], axis=1)
        self.parser_table = self.parser_table.drop(self.parser_table.index[- 1])
        self.action_table = self.action_table.drop(self.action_table.index[-1])
        self.goto_table = self.goto_table.drop(self.goto_table.index[-1])
        return self.parser_table
    
    def render(self, filename):
        grafico = Digraph("LRCERO", format='pdf')
        grafico.attr(rankdir="LR")
        grafico.attr('node', shape='circle')
        for num_estado, estado in enumerate(self.estados):
            label = None
            if not num_estado == (len(self.estados)-1):
                derivados = [str(item) for item in estado if item.derivado]
                no_derivados = [str(item) for item in estado if not item.derivado]
                label = f"Estado {num_estado}\n\n"+"---No derivados---\n"+"\n".join(no_derivados) + '\n---Derivados---\n' + '\n'.join(derivados)
            else: label = "ACEPTADO"
            grafico.node(str(num_estado), label= label)
        for trancision in self.transiciones: grafico.edge(tail_name=str(trancision[0]), head_name=str(trancision[2]), label = trancision[1])
        grafico.render(filename.split('.')[0], cleanup=True)

def LL_first_sets(producciones, terminales, no_terminales):
    firsts = {no_terminal: set() for no_terminal in no_terminales}

    cambiado = True
    while cambiado:
        cambiado = False
        for no_terminal in no_terminales:
            for produccion in producciones[no_terminal]:
                i = 0
                seguir = True
                while seguir and i < len(produccion):
                    simbolo = produccion[i]
                    if simbolo in terminales:
                        if simbolo not in firsts[no_terminal]:
                            firsts[no_terminal].add(simbolo)
                            cambiado = True
                        seguir = False
                    else:
                        añadido = len(firsts[no_terminal])
                        firsts[no_terminal].update(firsts[simbolo] - {None})
                        if len(firsts[no_terminal]) != añadido:
                            cambiado = True
                        if None not in firsts[simbolo]:
                            seguir = False
                    i += 1
                else:
                    if None not in firsts[no_terminal]:
                        firsts[no_terminal].add(None)
                        cambiado = True
    return firsts

def LL_follow_sets(producciones, firsts, no_terminales):
    follow = {no_terminal: set() for no_terminal in no_terminales}
    follow[next(iter(no_terminales))].add('$')

    cambiado = True
    while cambiado:
        cambiado = False
        for no_terminal in no_terminales:
            for produccion in producciones[no_terminal]:
                indice = 0
                while indice < len(produccion):
                    simbolo = produccion[indice]
                    if simbolo in no_terminales:
                        if indice + 1 < len(produccion):
                            simbolo_siguiente = produccion[indice + 1]
                            if simbolo_siguiente in no_terminales:
                                añadido = len(follow[simbolo])
                                follow[simbolo].update(firsts[simbolo_siguiente] - {None})
                                if len(follow[simbolo]) != añadido:
                                    cambiado = True
                            else:
                                if simbolo_siguiente not in follow[simbolo]:
                                    follow[simbolo].add(simbolo_siguiente)
                                    cambiado = True
                        else:
                            añadido = len(follow[simbolo])
                            follow[simbolo].update(follow[no_terminal])
                            if len(follow[simbolo]) != añadido:
                                cambiado = True
                    indice += 1

    return follow

 