import graphviz
from typing import List, Dict, Optional, Set

class AFD():

    def __init__(self, estado_inicial, alfabeto = [], estados = [], estados_de_aceptacion = [], transitions = {}, estado_final = None) -> None:
        
        self.estado_final = estado_final
        self.alfabeto: list = alfabeto #Aceptado como trancisiones (nombre de arista, digamos)
        self.estados: list = estados #Estados (vertices)
        self.estado_inicial = estado_inicial
        self.estados_de_aceptacion: list = [item for item in estados_de_aceptacion if item in self.estados]
        self.transitions: dict = transitions # {state: {symbol: state, ..., symbol: state}}


    def draw_afd(self):
        afn = graphviz.Digraph(format='pdf')
        afn.graph_attr['rankdir'] = 'LR'
        afn.node('start', style='invis')
        nodos = []
        for state in self.estados:
            if state == self.estado_inicial:
                afn.node(state, shape='diamond', color='red')
                nodos.append((state, "inicial"))
            elif state not in self.estados_de_aceptacion:
                afn.node(state)
                nodos.append((state, "normal"))
            else:
                afn.node(state, shape='doublecircle')
                nodos.append((state, "aceptacion"))

        edge_labels = {}
        for state in self.transitions:
            trans = self.transitions.get(state)
            for symbol in trans:
                if symbol != 'ε':
                    next_state = trans.get(symbol)
                    label = symbol.replace(' ', 'BS').replace('\t', '/t').replace('\n', '/n')
                    edge_key = (state, next_state)
                    if edge_key in edge_labels:
                        edge_labels[edge_key].append(label)
                    else:
                        edge_labels[edge_key] = [label]

        for edge_key, labels in edge_labels.items():
            afn.edge(edge_key[0], edge_key[1], label=', '.join(labels))

        afn.render('afd', view=True)



    def simulacion(self, w, show_path = False, print_errors = False):
        path = []
        curr_state = self.estado_inicial
        for char in w:
            path.append(curr_state)
            if char not in self.alfabeto:
                if print_errors:
                    print("Cadena contiene caracteres que no pertenecen al alfabeto definido")
                return False
            curr_state = self.transitions.get(curr_state).get(char)
        path.append(curr_state)
        if show_path:
            path = "->".join(path)
            print(path)
        return curr_state in self.estados_de_aceptacion

    def __quick_fix_minmize_rm_unreacheble_states(self):

        def __explore_next(state, backtrack: list):
            backtrack.append(state)
            reached_states = set(backtrack)
            for chr in self.alfabeto:
                next_one = self.transitions.get(state).get(chr)
                if not next_one in backtrack:
                    reached_states = __explore_next(next_one, backtrack)

            return reached_states
        existing_states : set = set(self.estados)    
        reached_states: set = __explore_next(self.estado_inicial,  [])
        unreached_states = list(existing_states.difference(reached_states))

        for un_stt in unreached_states:     
            self.estados.remove(un_stt)
            del self.transitions[un_stt]
            if un_stt in self.estados_de_aceptacion:
                self.estados_de_aceptacion.remove(un_stt)
        return        




    def minimize(self):
        table = [[False for _ in range(len(self.estados))] for _ in range(len(self.estados))]

        for i in range(len(self.estados)):
            for j in range(i + 1, len(self.estados)):
                state1, state2 = self.estados[i], self.estados[j]
                if (state1 in self.estados_de_aceptacion) != (state2 in self.estados_de_aceptacion):
                    table[i][j] = True

        change = True
        while change:
            change = False
            for i in range(len(self.estados)):
                for j in range(i + 1, len(self.estados)):
                    if not table[i][j]:
                        state1, state2 = self.estados[i], self.estados[j]
                        for symbol in self.alfabeto:
                            next_state1, next_state2 = self.transitions[state1][symbol], self.transitions[state2][symbol]
                            idx1, idx2 = self.estados.index(next_state1), self.estados.index(next_state2)
                            if table[min(idx1, idx2)][max(idx1, idx2)]:
                                table[i][j] = True
                                change = True
                                break

        groups = []
        for i in range(len(self.estados)):
            for j in range(i + 1, len(self.estados)):
                if not table[i][j]:
                    state1, state2 = self.estados[i], self.estados[j]
                    for group in groups:
                        if state1 in group:
                            group.add(state2)
                            break
                        elif state2 in group:
                            group.add(state1)
                            break
                    else:
                        groups.append({state1, state2})

        new_states = []
        new_transitions = {}
        for group in groups:
            new_state = "/".join(sorted(group))
            new_states.append(new_state)
            new_transitions[new_state] = {}
            for symbol in self.alfabeto:
                old_state = next(iter(group))
                old_next_state = self.transitions[old_state][symbol]
                for other_group in groups:
                    if old_next_state in other_group:
                        new_transitions[new_state][symbol] = "/".join(sorted(other_group))
                        break
                else:
                    new_transitions[new_state][symbol] = old_next_state

        missing_states = set(self.estados).difference(new_states)
        for missing_state in missing_states:
            new_transitions[missing_state] = {}
            for symbol in self.alfabeto:
                old_next_state = self.transitions[missing_state][symbol]
                for other_group in groups:
                    if old_next_state in other_group:
                        new_transitions[missing_state][symbol] = "/".join(sorted(other_group))
                        break
                else:
                    new_transitions[missing_state][symbol] = old_next_state
        new_states.extend(missing_states)

        reachable_states = set()
        stack = [self.estado_inicial]

        while stack:
            state = stack.pop()
            if state not in reachable_states:
                reachable_states.add(state)
                for symbol in self.alfabeto:
                    next_state = self.transitions[state][symbol]
                    stack.append(next_state)

        missing_states = set(self.estados).difference(new_states)
        reachable_missing_states = missing_states.intersection(reachable_states)
        for missing_state in reachable_missing_states:
            new_transitions[missing_state] = {}
            for symbol in self.alfabeto:
                old_next_state = self.transitions[missing_state][symbol]
                for other_group in groups:
                    if old_next_state in other_group:
                        new_transitions[missing_state][symbol] = "/".join(sorted(other_group))
                        break
                else:
                    new_transitions[missing_state][symbol] = old_next_state
        new_states.extend(reachable_missing_states)

        self.estados = new_states
        self.transitions = new_transitions
        self.estado_inicial = "/".join(sorted([state for state in self.estados if self.estado_inicial in state.split("/")]))
        self.estados_de_aceptacion = ["/".join(sorted(group)) for group in groups if any(state in self.estados_de_aceptacion for state in group)]
        self.__quick_fix_minmize_rm_unreacheble_states()

    def rename_states(self):
        uppercase_alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        new_names = {}
        counter = 1

        for i, state in enumerate(self.estados):
            if i < len(uppercase_alphabet):
                new_names[state] = uppercase_alphabet[i]
            else:
                new_names[state] = uppercase_alphabet[i % len(uppercase_alphabet)] + str(counter)
                if (i + 1) % len(uppercase_alphabet) == 0:
                    counter += 1

        new_acc = [new_names[stt] for stt in self.estados_de_aceptacion]
        new_stt = [new_names[stt] for stt in self.estados]
        new_trans = {}
        for stt_i in self.transitions:
            trans = {}
            state_transitions = self.transitions[stt_i]
            for symbol in state_transitions:
                trans[symbol] = new_names[state_transitions[symbol]]
            new_trans[new_names[stt_i]] = trans

        self.transitions = new_trans
        self.estados = new_stt
        self.estados_de_aceptacion = new_acc
        self.estado_inicial = new_names[self.estado_inicial]
        if self.estado_final:
            self.estado_final = new_names[self.estado_final]
