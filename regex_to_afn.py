from AFN import AFN
from math import floor

def __get_available_name_states(total_states: int, count_new_states: list):
    
    new_states = []
    for _ in range(1, count_new_states+1):
        letter = total_states%26
        letter  = 65 + letter 
        coef = str(floor(total_states/26)) if total_states>=26 else ""
        total_states += 1
        new_states.append(f"{chr(letter)}{coef}")
            
    return total_states, new_states
        
def __replicate_afn(states_replica: dict, afn_original: AFN) -> AFN:
    states = [states_replica.get(stt) for stt in states_replica]
    alphabet = afn_original.alfabeto
    estado_inicial = states_replica.get(afn_original.estado_inicial)
    estado_final = states_replica.get(afn_original.estado_final)
    estados_de_aceptacion = [states_replica.get(stt) for stt in afn_original.estados_de_aceptacion]
    transitions = {}
    for tran in afn_original.transitions:
        new_state = states_replica.get(tran)
        transt = afn_original.transitions.get(tran)
        each_transitions = {}
        for symbols in transt:
            actual = transt.get(symbols)
            if not actual:
                each_transitions[symbols] = []
            else:
                new_actual = [states_replica.get(state) for state in actual]
                each_transitions[symbols] = new_actual

        transitions[new_state] = each_transitions
    afn = AFN(estado_inicial, alphabet, states, estados_de_aceptacion, transitions, estado_final)
    return afn
    
def generate_afn_from_posfix(posfix: str, alphabet: set)-> AFN:
    alphabet.add('ε')
    total_states = 0
    expr_afn = {}
    existing_op = [ "*", "?", "+", ".", "|" ]
    posfix_list = list(posfix)
    total_states = 0
    if len(posfix_list)==1:
        total_states ,states = __get_available_name_states(total_states, 2)
        return __build_symbol(posfix[0], states, alphabet)
    while len(posfix_list)>1:
        j = 0
        original_len = len(posfix_list)
        while len(posfix_list) == original_len:
            expr = posfix_list[j] 
            if expr in existing_op:
                if expr=="*":
                    if j<1: raise Exception(f"Expects at least one expression before operator {expr}")
                    new_expr = f"{posfix_list[j-1]}*"
                    afn1 = expr_afn.get((posfix_list[j-1], j-1))
                    total_states, states = __get_available_name_states(total_states, 2)
                    new_afn = __build_star(afn1, states, alphabet)
                    expr_afn[(new_expr, j-1)] = new_afn
                    posfix_list[j] = new_expr
                    del expr_afn[(posfix_list[j-1], j-1)]
                    posfix_list.pop(j-1)
                elif expr=="?":
                    if j<1: raise Exception(f"Expects at least one expression before operator {expr}")
                    new_expr = f"{posfix_list[j-1]}?"
                    afn1 = expr_afn.get((posfix_list[j-1], j-1))
                    total_states, states = __get_available_name_states(total_states, 2)
                    new_afn = __build_interrogation(afn1, states, alphabet)
                    expr_afn[(new_expr, j-1)] = new_afn
                    posfix_list[j] = new_expr
                    del expr_afn[(posfix_list[j-1], j-1)]
                    posfix_list.pop(j-1)
                elif expr=="+":
                    if j<1: raise Exception(f"Expects at least one expression before operator {expr}")
                    new_expr = f"{posfix_list[j-1]}+"
                    afn1: AFN = expr_afn.get((posfix_list[j-1], j-1))
                    # Replication of afn
                    states_replica = {}
                    for state in afn1.estados:
                        total_states, states = __get_available_name_states(total_states, 1)
                        states_replica[state] = states[0]
                    afn_replica = __replicate_afn(states_replica, afn1)

                    total_states, states = __get_available_name_states(total_states, 2)
                    new_afn = __build_plus(afn1, afn_replica, states, alphabet)
                    expr_afn[(new_expr, j-1)] = new_afn
                    posfix_list[j] = new_expr
                    del expr_afn[(posfix_list[j-1], j-1)]
                    posfix_list.pop(j-1)

                elif expr=="|":
                    if j<2: raise Exception(f"Expects at least two expression before operator {expr}")
                    new_expr = f"{posfix_list[j-2]}{posfix_list[j-1]}|"
                    afn2: AFN = expr_afn.get((posfix_list[j-1], j-1))
                    afn1: AFN = expr_afn.get((posfix_list[j-2], j-2))
                    total_states, states = __get_available_name_states(total_states, 2)
                    new_afn = __build_union(afn1, afn2, states, alphabet)
                    expr_afn[(new_expr, j-2)] = new_afn
                    posfix_list[j] = new_expr
                    del expr_afn[(posfix_list[j-1], j-1)]
                    del expr_afn[(posfix_list[j-2], j-2)]
                    posfix_list.pop(j-2)
                    posfix_list.pop(j-2)
                elif expr==".":
                    if j<2: raise Exception(f"Expects at least two expression before operator {expr}")
                    new_expr = f"{posfix_list[j-2]}{posfix_list[j-1]}."
                    afn2: AFN = expr_afn.get((posfix_list[j-1], j-1))
                    afn1: AFN = expr_afn.get((posfix_list[j-2], j-2))
                    new_afn = __build_concat(afn1, afn2, alphabet)
                    expr_afn[(new_expr, j-2)] = new_afn
                    posfix_list[j] = new_expr
                    del expr_afn[(posfix_list[j-1], j-1)]
                    del expr_afn[(posfix_list[j-2], j-2)]
                    posfix_list.pop(j-2)
                    posfix_list.pop(j-2)
            elif (expr, j) not in expr_afn: # Se lo salta y sigue la busqueda para ver si este se opera con otro
                if len(expr)>1:
                    raise Exception("Unexpected expression not defined")
                total_states, states = __get_available_name_states(total_states, 2)
                afn = __build_symbol(expr, states, alphabet)
                expr_afn[(expr, j)] = afn
                j += 1
            else: #Crea maquina AFN de simbolo simple
                j += 1

    afn =  expr_afn.get((posfix_list[0], 0))
    return afn

def __add_destiny_transition_to_state(transition, origin, destiny, symbol):
    actual = transition.get(origin).get(symbol)
    if actual:
        if destiny not in actual: actual.append(destiny)
        transition[origin][symbol] = actual
    else:
        transition[origin][symbol] = [destiny]
    return transition

def __build_concat(afn1:AFN, afn2: AFN, alphabet)-> AFN:
    states = afn1.estados
    states.extend(afn2.estados)
    afn1_start = afn1.estado_inicial
    afn1_end = afn1.estado_final
    afn2_start = afn2.estado_inicial
    afn2_end = afn2.estado_final
    transitions = {**afn1.transitions, **afn2.transitions}
    __add_destiny_transition_to_state(transitions, afn1_end, afn2_start, 'ε')
    return AFN(afn1_start, alphabet, states, afn2.estados_de_aceptacion, transitions, afn2_end)

def __build_union(afn1:AFN, afn2: AFN, states, alphabet)-> AFN:
    
    new_start = states[0]
    new_end = states[1]
    afn1_start = afn1.estado_inicial
    afn1_end = afn1.estado_final
    afn2_start = afn2.estado_inicial
    afn2_end = afn2.estado_final
    transitions = {**afn1.transitions, **afn2.transitions, **{state: {symbol: [] for symbol in alphabet} for state in states}}
    __add_destiny_transition_to_state(transitions, new_start, afn1_start, 'ε')
    __add_destiny_transition_to_state(transitions, new_start, afn2_start, 'ε')

    __add_destiny_transition_to_state(transitions, afn1_end, new_end, 'ε')
    __add_destiny_transition_to_state(transitions, afn2_end, new_end, 'ε')
    
    states.extend(afn1.estados)
    states.extend(afn2.estados)
    return AFN(new_start, alphabet, states, [new_end], transitions, new_end)

def __build_star(afn1:AFN, states, alphabet)-> AFN:
    new_start = states[0]
    new_end = states[1]
    afn1_final = afn1.estado_final
    afn1_start = afn1.estado_inicial

    transitions = {**afn1.transitions,**{state: {symbol: [] for symbol in alphabet} for state in states} }
    __add_destiny_transition_to_state(transitions, new_start, afn1_start, 'ε')
    __add_destiny_transition_to_state(transitions, afn1_final, new_end, 'ε')
    __add_destiny_transition_to_state(transitions, afn1_final, afn1_start, 'ε')
    __add_destiny_transition_to_state(transitions, new_start, new_end, 'ε')
    states.extend(afn1.estados)
    
    return AFN(new_start, alphabet, states, [new_end], transitions, new_end)

def __build_plus(afn1:AFN, afn1_clone: AFN, states,  alphabet)-> AFN:
    return __build_concat(afn1_clone, __build_star(afn1, states, alphabet),  alphabet)

def __build_interrogation(afn1:AFN, states, alphabet)-> AFN:
    new_start = states[0]
    new_end = states[1]
    afn1_final = afn1.estado_final
    afn1_start = afn1.estado_inicial

    transitions = {**afn1.transitions,**{state: {symbol: [] for symbol in alphabet} for state in states} }
    __add_destiny_transition_to_state(transitions, new_start, afn1_start, 'ε')
    __add_destiny_transition_to_state(transitions, new_start, new_end, 'ε')
    __add_destiny_transition_to_state(transitions, afn1_final, new_end, 'ε')
    states.extend(afn1.estados)
    
    return AFN(new_start, alphabet, states, [new_end], transitions, new_end)

def __build_symbol(symbol: str, states, alphabet):
    initial_state = states[0]
    final_state = states[1]
    transitions = {}

    for state in states:
        state_trans = {}
        for smbl in alphabet:
            if state==initial_state and smbl==symbol:
                state_trans[smbl] = [final_state]
            else:
                state_trans[smbl] = []
        transitions[state] = state_trans
    return AFN(initial_state, list(alphabet), states, [final_state], transitions, final_state)

def main():
    """ 
    count_states = 0
    i = 0
    states = []
    while i<100:
        count_states, n_states= __get_available_name_states(count_states, 2)
        states.extend(n_states)
        print(states)
        i += 1 


    print('a') 
    """
    total_states = 0
    total_states, states = __get_available_name_states(total_states, 2)
    alphabet = {'a', 'b', 'ε'}
    afn1 = __build_symbol('a', states, alphabet )
    total_states, states = __get_available_name_states(total_states, 2)
    afn2 = __build_symbol('b', states, alphabet )
    total_states, states = __get_available_name_states(total_states, 2)
    __build_union(afn1, afn2, states, alphabet).draw_afn()
    print('a')
    afn1.draw_afn()
    total_states, states = __get_available_name_states(total_states, 2)
    __build_interrogation(afn1, states, alphabet).draw_afn()

if __name__ == "__main__":
    from regex_to_posfix import infix_to_posfix
    from AFN import AFN
    from regex_to_afn import generate_afn_from_posfix
    regex = "a|b*+c?(de)"
    postfix, err, alph = infix_to_posfix(regex)
    print(postfix)

    afn: AFN = generate_afn_from_posfix(postfix, alph)
    # afn.draw_afn()
    afd = afn.to_afd()
    afd.draw_afd()