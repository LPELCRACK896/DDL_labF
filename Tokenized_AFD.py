from dataclasses import dataclass
from stack import Stack
from yalex_to_regex import read_yalex
import re
from constants import ALPHABET, OPERATORS, ANCIENT_SYMBOLS
from AFD import AFD
from AFN import AFN
from regex_to_afn import generate_afn_from_posfix
from regex_to_posfix import infix_to_posfix
import graphviz

def file_into_list(filename):
    content = None
    with open(filename, 'r') as file:
        lines = file.readlines()
        content = []
        for line in lines:
            if len(line)>1:
                line_content, endline = line[:-1], line[-1:]
                if endline=="\n":
                    content.append(line_content)
                else:
                    content.append(line)
            else:
                content.append(line)
    return content

def render_super_afn(afds: dict):
    
    g = graphviz.Digraph(format='pdf')
    g.graph_attr['rankdir'] = 'LR'
    g.node('start', shape='plaintext', label='start')
    for token, afd in afds.items():
        for state in afd.estados:
            if state == afd.estado_inicial:
                g.node(f"({token})_{state}", shape='diamond', color='red')
            elif state not in afd.estados_de_aceptacion:
                g.node(f"({token})_{state}")
            else:
                g.node(f"({token})_{state}", shape='doublecircle')

            if state == afd.estado_inicial:
                g.edge('start', f"({token})_{state}", label='ε')
        edge_labels = {}
        for state in afd.transitions:
            trans = afd.transitions.get(state)
            for symbol in trans:
                if symbol != 'ε':
                    next_state = trans.get(symbol)
                    edge_key = (f"({token})_{state}", f"({token})_{next_state}")
                    label = symbol.replace(' ', 'BS').replace('\t', '/t').replace('\n', '/n')
                    if edge_key in edge_labels:
                        edge_labels[edge_key].append(label)
                    else:
                        edge_labels[edge_key] = [label]

        for edge_key, labels in edge_labels.items():
            g.edge(edge_key[0], edge_key[1], label=', '.join(labels))

    g.render('super_automate', view=True)

@dataclass
class ExpressionComponent:
    type: str
    content: str
    components: list
    state: str

def decompose_ExpressionComponent_into_list(component: ExpressionComponent):
    if component.content:
        clone = ExpressionComponent(type= component.type, content = component.content, components=None, state=component.state)
        my_components = [clone]
    else:
        my_components = []
    if component.components:
        for comp in component.components:
            my_components.extend(decompose_ExpressionComponent_into_list(comp))

    return my_components

@dataclass
class Token:
    name: str
    dependencies: list
    expressionC: list

class SuperAFN:
    def __init__(self, lets, rules) -> None:
        self.lets = lets
        self.rules = rules
        self.alfabeto = None
        self.lets_regex = None
        self.token_afds = {}
        self.afds = []
        self.character_tokens = []
        self.__clean_token_rule()


    def __clean_token_rule(self):
        new_tokens = {}
        old_tokens: dict = self.rules["tokens"]
        for token, instruction in old_tokens.items():
            n_token = token.replace("\'", "").replace("\"", "")
            if n_token != token:
                self.character_tokens.append(n_token)
            n_intruction = ""
            reading_state = "not_yet"
            i = 0
            while reading_state!="end" and i<len(instruction):
                chr = instruction[i]
                if reading_state == "not_yet":
                    if chr == "{":
                        reading_state = "on_reading"
                else: ## reading_state == "on_reading":
                    if chr!="}":
                        n_intruction += chr
                    else:
                        reading_state = "end"
                i += 1
            if reading_state!="end":
                print(f"Unable to interpretate token ({token}) value: {instruction}")
                n_intruction = instruction
            new_tokens[n_token] = n_intruction
        
        self.rules["tokens"] = new_tokens
        return new_tokens

        
        
    def rebuild_expression(self, expression):
        i = 0
        error = None
        reading_target = None
        build_expression: Stack = Stack()
        while i<len(expression):
            char = expression[i]
            if not reading_target:
                if char == '\'':
                    reading_target = "string"
                    build_expression.push(ExpressionComponent("string", "", None, "open"))
                elif char == "[":
                    reading_target  = "interval"
                    build_expression.push(ExpressionComponent("interval", None, [], "open"))
                elif char == "]":
                    max_pops = build_expression.size()
                    if max_pops<1:
                        return "Cannot close unstarted interval"
                    last: ExpressionComponent = build_expression.pop()
                    max_pops -= 1
                    interval_content = []
                    while last.type != "interval":
                        if max_pops<1:
                            return "Couldnt find the start of the interval closing"
                        interval_content.append(last)
                        last:ExpressionComponent = build_expression.pop()
                        max_pops -= 1
                    if last.state=="closed":
                        return "Couldnt find the start of the inverval. Found a contained interval first, invalid syntaxis."
                    interval_content.reverse()
                    reorganized_content = []
                    while interval_content:
                        element: ExpressionComponent = interval_content.pop(0)
                        if element.type == "operation":
                            if element.content!="-": 
                                return "Not operation allowed in interval. Only allowed is \'-\'"
                            if not reorganized_content: #Debe haber algo antes
                                return "Cannot start interval with \'-\'"
                            if not interval_content: # Debe haber algo despues
                                return "Cannot create interval with no end."
                            last_e: ExpressionComponent = interval_content.pop(0)
                            first_e: ExpressionComponent = reorganized_content.pop()
                            if type(first_e)==tuple:
                                return "Interval start should be defined, found other interval instead"
                                    
                            if first_e.type != "string":
                                return f"Interval start should be string type. Found \'{first_e.type}\' instead."
                            if last_e.type != "string":
                                return f"Interval end should be string type. Found \'{first_e.type}\' instead."
                            reorganized_content.append((first_e, last_e))
                        else:
                            reorganized_content.append(element)
                    last.components = reorganized_content
                    last.state = "closed"
                    error, last = self.redefine_intervals(last)
                    if error: 
                        return error
                    
                    build_expression.push(last)
                elif char == "+":
                    build_expression.push(ExpressionComponent("operation", "+", None, "closed"))
                elif char == "|":
                    build_expression.push(ExpressionComponent("operation", "|", None, "closed"))
                elif char == "*":
                    build_expression.push(ExpressionComponent("operation", "*", None, "closed"))
                elif char == "?":
                    build_expression.push(ExpressionComponent("operation", "?", None, "closed"))
                elif char == "-":
                    build_expression.push(ExpressionComponent("operation", "-", None, "closed"))
                elif char == "(":
                    build_expression.push(ExpressionComponent("operation", "(", None, "closed"))
                elif char == ")":
                    build_expression.push(ExpressionComponent("operation", ")", None, "closed"))
                else:
                    reading_target = "variable"
                    build_expression.push(ExpressionComponent("variable", char, None, "open"))
            elif reading_target == "string":
                if char == '\'':
                    exp: ExpressionComponent = build_expression.peek()
                    exp.state = "closed"
                    reading_target = None
                else:
                    exp: ExpressionComponent = build_expression.peek()
                    exp.content +=  char
            elif reading_target=="interval":
                if char == '\'':
                    reading_target = "string"
                    build_expression.push(ExpressionComponent("string", "", None, "open"))
                elif char == "[":
                    return "Cannot create an interval inside an interval"
                elif char == "]":
                    return "Cannot set an empty interval"
                else:
                    return f"Cannot start interval with {char}"
            elif reading_target == "variable":
                if char == '\'':
                    exp: ExpressionComponent = build_expression.peek()
                    exp.state = "closed"
                    reading_target = "string"
                    build_expression.push(ExpressionComponent("string", "", None, "open"))
                elif char == "[":
                    exp: ExpressionComponent = build_expression.peek()
                    exp.state = "closed"
                    reading_target  = "interval"
                    build_expression.push(ExpressionComponent("interval", None, [], "open"))
                elif char == "]":
                    return "Cannot use ] in a variable name"
                elif char == "+":
                    exp: ExpressionComponent = build_expression.peek()
                    exp.state = "closed"
                    reading_target = None
                    build_expression.push(ExpressionComponent("operation", "+", None, "closed"))
                elif char == "|":
                    exp: ExpressionComponent = build_expression.peek()
                    exp.state = "closed"
                    reading_target = None
                    build_expression.push(ExpressionComponent("operation", "|", None, "closed"))
                elif char == "*":
                    exp: ExpressionComponent = build_expression.peek()
                    exp.state = "closed"
                    reading_target = None
                    build_expression.push(ExpressionComponent("operation", "*", None, "closed"))
                elif char == "?":
                    exp: ExpressionComponent = build_expression.peek()
                    exp.state = "closed"
                    build_expression.push(ExpressionComponent("operation", "?", None, "closed"))
                elif char == "-":
                    exp: ExpressionComponent = build_expression.peek()
                    exp.state = "closed"
                    reading_target = None
                    build_expression.push(ExpressionComponent("operation", "-", None, "closed"))
                elif char == "(":
                    exp: ExpressionComponent = build_expression.peek()
                    exp.state = "closed"
                    reading_target = None
                    build_expression.push(ExpressionComponent("operation", "(", None, "closed"))
                elif char == ")":
                    exp: ExpressionComponent = build_expression.peek()
                    exp.state = "closed"
                    reading_target = None
                    build_expression.push(ExpressionComponent("operation", ")", None, "closed"))
                else:
                    exp: ExpressionComponent = build_expression.peek()
                    exp.content +=  char


            i += 1

        return error, build_expression

    def __minimum_exclusive_interval(self, sets):
        sorted_sets = sorted(sets, key=lambda s: s[0])
        result = []
        min_exclusive_interval = None
        for s in sorted_sets:
            if min_exclusive_interval and s[0] <= min_exclusive_interval[1]:
                # Case b: Update the upper bound of the interval.
                min_exclusive_interval = (min_exclusive_interval[0], max(min_exclusive_interval[1], s[1]))
            elif result and s[0] == result[-1][1]:
                # Merge with previous interval if contiguous.
                result[-1] = (result[-1][0], s[1])
            else:
                if min_exclusive_interval:
                    # Case a: Add the current minimum exclusive interval to the result list.
                    result.append(min_exclusive_interval)
                # Case c: Set the current minimum exclusive interval to the set.
                min_exclusive_interval = s
        # Add the final minimum exclusive interval to the result list.
        if min_exclusive_interval:
            result.append(min_exclusive_interval)
        return result

    def redefine_intervals(self, component: ExpressionComponent):

        error = None
        other_intervals_i = []
        alph_intervals = []
        num_intervals = []
        for intervals in component.components:
            if type(intervals) is ExpressionComponent:
                other_intervals_i.append(intervals)
            else: 
                start:ExpressionComponent = intervals[0]
                end:ExpressionComponent = intervals[1]
                if start.type != "string":
                    return "Cannot create interval with a starting point other than a string. Use digits or letters", component
                elif end.type != "string":
                    return "Cannot create interval with a starting point other than a string. Use digits or letters", component

                if start.content.isdigit():
                    if not end.content.isdigit():
                        return "Canot define a interval that starts with a digit and ends with some other type", component
                    start_num = int(start.content)
                    end_num = int(end.content)
                    if end_num<start_num:
                        return "Cannot define an interval in which the end is lower than the end", component
                    num_intervals.append((start_num, end_num))  
                else:
                    if end.content.isdigit():
                        return "Cannot define an interval that starts with a regular string and end with ", component
                    
                    start_str = start.content
                    end_str = end.content
                    
                    alph_start = -1
                    alph_end = -1
                    if start_str in ALPHABET:
                        alph_start = ALPHABET.index(start_str)
                    else:
                        return f"Cannot create interval starting with a character other than a alphabet element {start_str}", component
                    if end_str in ALPHABET:
                        alph_end = ALPHABET.index(end_str)
                    else:
                        return f"Cannot create interval ending with a character other than a alphabet element {end_str}", component
                    alph_intervals.append((alph_start, alph_end))
        
        new_alph_intervals = []
        if alph_intervals:
            alph_intervals = self.__minimum_exclusive_interval(list(alph_intervals))
            for a_intv in alph_intervals:
                for i in range(a_intv[0],  a_intv[1]+1):
                    element = ALPHABET[i]
                    new_alph_intervals.append(ExpressionComponent(type="string", content=element, components=None, state="closed"))
                    new_alph_intervals.append(ExpressionComponent(type = "operation", content ="|", components = None, state = "closed"))
            new_alph_intervals.pop()

        new_num_intervals = []
        if num_intervals:
            if new_alph_intervals:
                new_num_intervals.append(ExpressionComponent(type = "operation", content ="|", components = None, state = "closed"))
            num_intervals = self.__minimum_exclusive_interval(num_intervals)
            for n_intv in num_intervals:
                for i in range(n_intv[0], n_intv[1]+1):
                    element = str(i)
                    if len(element)>1:
                        element = f"({element})"
                    new_num_intervals.append(ExpressionComponent(type="string", content=element, components=None, state="closed"))
                    new_num_intervals.append(ExpressionComponent(type = "operation", content ="|", components = None, state = "closed"))
            new_num_intervals.pop()

        new_other_items = []
        if other_intervals_i:
            if new_num_intervals or new_alph_intervals:
                new_other_items.append(ExpressionComponent(type = "operation", content ="|", components = None, state = "closed"))
            for n_i in other_intervals_i:
                new_other_items.append(n_i)
                new_other_items.append(ExpressionComponent(type = "operation", content ="|", components = None, state = "closed"))
            new_other_items.pop()

        component.components = new_alph_intervals + new_num_intervals + new_other_items
        return error, component  

    def __proccess_string_regex(self, string: str):  
        regex_pattern = r"\\t|\\n"
        new_string = re.sub(regex_pattern, lambda m: "\t" if m.group(0) == "\\t" else "\n", string)
        for i in range(len(OPERATORS)):
            if OPERATORS[i] in new_string:
                new_string = new_string.replace(OPERATORS[i], ANCIENT_SYMBOLS[i])
        return new_string

    def __build_regex_from_string_stack(self, stack):
        regex = ""
        for element in stack.items:
            if element.type == "string":
                new = self.__proccess_string_regex(element.content)
            else:
                new = element.content #operador
            regex += f"{new}"
        return regex

    def build_lets_regex(self):

        def __replace_variable_for_regex_in_stack(stack, variable_name, token_stack):
            n_stack = Stack()
            var_content = token_stack[variable_name]
            for element in stack.items:
                if element.type == "variable" and element.content == variable_name:
                    n_stack.push(ExpressionComponent(type="operation", content ="(", components=None, state="closed"))
                    n_stack.items += var_content.items
                    n_stack.push(ExpressionComponent(type="operation", content =")", components=None, state="closed"))
                else:
                    n_stack.push(element)
            return n_stack
                    
        
        token_regex = {}
        token_dependencies = {} 
        tokens = []
        
        token_stack = {}
        for token, expression in self.lets.items():
            error, stack = self.rebuild_expression(expression=expression)
            if error:
                return error
            tk_stck =Stack()
            for item in stack.items:
                tk_stck.items += decompose_ExpressionComponent_into_list(item)
            token_stack[token] = tk_stck
            tokens.append(token)
            token_regex[token] = None
        
        for token in tokens:
            info = token_stack.get(token)
            for part in info.items:
                if part.type =="variable":
                    if part.content == token:
                        return f"Circular reference on token {token}"
                    if part.content not in tokens:
                        return f"Unexsting reference on token definition {token}"
                    
                    if token in token_dependencies: #Revisa si ya existe en el diccionario
                        current_dependencies = token_dependencies[token]
                        if part.content not in current_dependencies:
                            token_dependencies[token].append(part.content)
                    else: #Crea un nuevo espacio en caso no se haya registrado anterior una dependencia
                        token_dependencies[token] = [part.content]
            if token not in token_dependencies:
                token_dependencies[token] = []
                token_regex[token] = self.__build_regex_from_string_stack(token_stack[token])

        definings_stack = Stack()
        while tokens:
            if definings_stack.isEmpty():
                definings_stack.push(tokens[0])
            else:
                actual_token = definings_stack.peek()
                dependencies = token_dependencies[actual_token]
                if dependencies:
                    for token_d in dependencies:
                        if token_dependencies[token_d]:
                            definings_stack.push(token_d)
                        else:
                            token_stack[actual_token]= __replace_variable_for_regex_in_stack(token_stack[actual_token], token_d, token_stack)
                            token_dependencies[actual_token].remove(token_d)
                    
                    if not token_dependencies[actual_token]:
                        token_regex[actual_token] = self.__build_regex_from_string_stack(token_stack[actual_token])
                        definings_stack.pop()
                        tokens.remove(actual_token)
                else:
                    token_regex[actual_token] = self.__build_regex_from_string_stack(token_stack[actual_token])
                    definings_stack.pop()
                    tokens.remove(actual_token)

        self.lets_regex = token_regex
                 
    def build_afds(self):
        if not self.lets_regex:
            print("Must have created token_regex by using build_lets_regex()")
            return
        token_afds = {}
        for token, expression in  self.lets_regex.items():
            posfix, err, alph = infix_to_posfix(expression)
            afn: AFN = generate_afn_from_posfix(posfix, alph)
            afn.find_cerradura()
            afd:AFD = afn.to_afd()
            afd.rename_states()
            # afd.draw_afd()
            afd.minimize()
            afd.rename_states()
            # afd.draw_afd()
            token_afds[token] = afd
        self.token_afds = token_afds

    def complie_tokens(self):
        pass

    def token_results_into_file(self, f_list, token_or_err, filename = "token_results.txt"):
        with open(filename, 'w') as file:
            file.write(str("STATE\t> Line\t> Token\n"))
            for line, token in zip(f_list, token_or_err):
                prefix = "SUCCESS" if token else "ERROR"
                file.write(f"{prefix}>{line}>{token}" + '\n')


    def tokenize_file(self, f_list):
        token_or_err = []

        for line in f_list:
            f_token = False
            for token, afd in self.token_afds.items():
                if f_token:
                    break
                if afd.simulacion(line):
                    f_token = token
            
            if not f_token:
                for special_token in self.character_tokens:
                    if f_token:
                        break
                    if line == special_token:
                        f_token = special_token
            token_or_err.append(f_token)
        return f_list, token_or_err

def main():
    filename = "ya.lex"
    error, lets, rules, r_priority = read_yalex(filename)
    if error:
        print(f"Error: {error}")
        return
    sup = SuperAFN(lets, rules)
    sup.build_lets_regex()
    sup.build_afds()
    # render_super_afn(sup.token_afds)
    input = "input" #File input
    f_list = file_into_list(input) 
    f_list, token_or_err = sup.tokenize_file(f_list)
    sup.token_results_into_file(f_list, token_or_err,)

    print('a')

if __name__ == "__main__":
    main()

