import graphviz
from stack import Stack
from AFD import AFD
from collections import deque
from camino import Camino

class AFN():

    def __init__(self, estado_inicial, alfabeto = [], estados = [], estados_de_aceptacion = [], transitions = {}, estado_final = None, related_token = None) -> None:
        self.estado_final = estado_final
        self.alfabeto: list = alfabeto #Aceptado como trancisiones (nombre de arista, digamos)
        self.estados: list = estados #Estados (vertices)
        self.estado_inicial = estado_inicial
        self.estados_de_aceptacion: set = set([item for item in estados_de_aceptacion if item in self.estados])

        self.transitions: dict = transitions if transitions else {estado: {caracter: [] for caracter in self.alfabeto} for estado in self.estados}#Trancisiones que se realizan entre (representa las aristas), Vertical:  // None indica que no hay trancision
        self.hasTransitionE: bool = 'ε' in self.alfabeto 
        self.cerraduras_de_estados = { estado : set() for estado in self.estados }
        self.caminos = []
        self.find_cerradura()
        


    def draw_afn(self):
        afn = graphviz.Digraph(format='pdf')
        afn.graph_attr['rankdir'] = 'LR'
        afn.node('start', style='invis')
        for state in self.estados:
            if state==self.estado_inicial:
                afn.node(state, shape='diamond', color='red')
            elif state not in self.estados_de_aceptacion:
                afn.node(state)
            else:
                afn.node(state, shape='doublecircle')

        for state in self.transitions:
            trans = self.transitions.get(state)
            for symbol in trans:
                transitions = trans.get(symbol)
                if transitions!=None:
                    for next_state in transitions:
                        label = symbol.replace(' ', 'BS').replace('\t', '/t').replace('\n', '/n')
                        afn.edge(state, next_state, label=label)

        afn.render('afn', view=True)

    def find_cerradura(self):
        cerradura = {state: set() for state in self.estados}
        for state in self.estados:
            closure = set()
            stack = Stack()
            stack.push(state)
            while stack.items:
                current_state = stack.pop()
                closure.add(current_state)
                epsilon_transitions = self.transitions[current_state].get('ε', [])
                for next_state in epsilon_transitions:
                    if next_state not in closure:
                        stack.push(next_state)
            cerradura[state] = closure
        self.cerraduras_de_estados = cerradura
        return cerradura

    def to_afd(self):
        tabla_trancisiones_AFD = {'VACIO': {input: 'VACIO' for input in self.alfabeto}}# Tabla inicialmente con el estado vacío
        new_states  = ['VACIO']
        accepted_states = []
        needs_empty_state = False
        
        def esEstadoAceptado(nuevoEstado: set):
            index = 0
            aceptado = False
            nuevoEstado = list(nuevoEstado)
            while index!=len(nuevoEstado) and not aceptado:
                if nuevoEstado[index] in self.estados_de_aceptacion: aceptado = True
                index += 1        
            return aceptado
        
        pendientes = [self.cerraduras_de_estados.get(self.estado_inicial)]

        while len(pendientes)!=0:
            estado_tratado = pendientes[0]
            new_states.append(estado_tratado)
            transitions = {}
            for input in self.alfabeto:
                if input!= 'ε':
                    next_state = set()
                    for estado_de_cerradura in estado_tratado:
                        next_possible_states = self.transitions.get(estado_de_cerradura).get(input)
                        if next_possible_states:
                            for estados_siguientes in next_possible_states:
                                for cerr in self.cerraduras_de_estados.get(estados_siguientes): 
                                    next_state.add(cerr)
                            
                    if next_state:
                        transitions[input] = str(next_state)
                        if not next_state in new_states: 
                            pendientes.append(next_state)
                            if esEstadoAceptado(next_state) and not str(next_state) in accepted_states: accepted_states.append(str(next_state))
                    else:
                        needs_empty_state = True
                        transitions[input] = 'VACIO'
            tabla_trancisiones_AFD[str(estado_tratado)] = transitions
            pendientes.pop(0)
        if not needs_empty_state:
            new_states.pop(0)
            tabla_trancisiones_AFD.pop('VACIO')
        return AFD(str(self.cerraduras_de_estados.get(self.estado_inicial)), [alf for alf in self.alfabeto if alf != 'ε'], [str(state) for state in new_states], accepted_states, tabla_trancisiones_AFD)
    
    def check_cadena(self, cadena):
        aprueba = True
        cont = 0
        while aprueba and cont!=len(cadena):
            aprueba = cadena[cont] in self.alfabeto
            cont += 1
        return aprueba

    def simulacion(self, w, show_path = False):
        if not self.check_cadena(w):
            print("Cadena invalida")
            return
        camino = Camino(f"Camino cadena: {w}", w, self.cerraduras_de_estados, self.transitions, self.estado_inicial, self.estados_de_aceptacion)
        self.caminos, tiempo = camino.setup_tree()
        __path_to_string = lambda  path: ' '.join([str(t) for t in path])
        not_succesful_paths = []
        succesfull_paths = []
        for paths in camino.caminos_enlistado:
            str_path = __path_to_string(paths[0])
            if paths[1]:
                succesfull_paths.append(str_path)
            else:
                not_succesful_paths.append(str_path)
        if show_path:
            if succesfull_paths:
                print("La cadena puede ser aceptada")
                print("----------Caminos que llevana a la aceptacion----------")
                for pth in succesfull_paths:
                    print(pth)
            if not_succesful_paths:
                if not succesfull_paths:
                    print("La cadena no es aceptada")
                print("----------Caminos fallidos----------")
                for pth in not_succesful_paths:
                    print(pth)

        return len(succesfull_paths)>0
 

