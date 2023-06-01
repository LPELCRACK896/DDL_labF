from stack import Stack
from collections import namedtuple

Error = namedtuple("Error", ["name", "details", "character", "data"])
errors_msgs = {
    "PHARENTESIS_UNMATCH": "Number of pharentesis does not match",
    "PHARENTESIS_UNCLOSED":  "Expects a close \")\" pharentesis after opening pharentesis \"(\"",
    "PHARENTESIS_EMPTY": "Found empty pharenthesis",
    "SYMBOL_FORBIDDEN": "Used forbidden symbol in string ",
    "REGEX_FORMAT": "Unproper regex infix submmited. ",
    "PHARENTESIS_CLOSES_UNOPENED": "Found closing pharentesis but no open pharentesis",
    "OPERATORS_2TOGETHER": "Unvalid operators one after the other.",
    "UNFINSHED_OPERATION": "Recived operator but not completed expression.",
    "NOTFOUND_OPERATION": "Expected operator between expression, couldnt be found"

}

def __is_valid_char(char):
    ascii_value = ord(char)
    return (65 <= ascii_value <= 90) or (97 <= ascii_value <= 122) or (48 <= ascii_value <= 57) or (char in "-?+|()")


def infix_to_posfix(regex: str) -> set:
    """Turns a regex in infix format into a posfix if formatted correctly. 

    Args:
        regex (str): Regex that might include both operators and simbols. 

    Returns:
        set: (str: Posfix, namedtuple: Error if any (name: str, character: str, data: str), str: Alphabet useful for generating automaton)
    """
    alphabet = set()
    posfix = regex
    operations_priority = {
        "*": 4,
        "?": 4,
        "+": 4,
        ".": 3,         
        "|": 2
    }
    forbidden_simbols = ["ε"]  
    other_symbols = ["(", ")"]
    if (any(map(lambda substring: substring in regex, forbidden_simbols))):
        name = "SYMBOL_FORBIDDEN"
        characters = ", ".join(forbidden_simbols)
        return posfix, Error(name=name, details=errors_msgs.get(name), character=characters, data=f"Fobidden characters are: {characters}"), alphabet
    if(any(map(lambda char: not (__is_valid_char(char) or char in other_symbols or char in operations_priority or char.isspace()), list(regex)))):
        name = "SYMBOL_FORBIDDEN"
        return posfix, Error(name=name, details=errors_msgs.get(name), character="", data=f"Must include only numbers or letters, (, ), *, |, +, ?, . in your regex"), alphabet
    def __rebuild_expression (stack: Stack):
        items = stack.items[:]
        if items[-1] in operations_priority:#Ultimo item es un operador
            name = "UNFINSHED_OPERATION"
            error = Error(name, errors_msgs.get(name), items[-1], stack)
            return None, error
        if len(items)==1: return items[0], None
        
        while len(items)!=1:
            i = 0
            j = 2
            last_i = len(items)-1
            found_simplification = False
            while not found_simplification:
                priority_i = i+1
                priority_j = priority_i
                if j!=last_i:
                    operation_i = items[priority_i]
                    operation_j = items[j+1]
                    if operation_i not in operations_priority or operation_j not in operations_priority:
                        name = "NOTFOUND_OPERATION" 
                        return None, Error(name, errors_msgs.get(name), "", "")
                    priority_j = priority_i if operations_priority.get(operation_i)>=operations_priority.get(operation_j) else j+1             
                found_simplification = priority_i == priority_j 
                if not found_simplification:
                    i = j
                    j += 2
            new_item = f"{items[i]}{items[j]}{items[i+1]}"
            items[i] = new_item
            items.pop(i+1)
            items.pop(i+1)

        return items[0], None
    i = 0
    error = None
    stack = Stack()
    pharentesis_lvl = 0
    last_was_expression = False
    expects_char = True
    while not error and i<len(regex):
        char = regex[i]
        if char in operations_priority: #Operadores
            if expects_char:
                name = "REGEX_FORMAT"
                error = Error(name, errors_msgs.get(name), char, regex)
            else: 
                last = stack.peek()
                if last in operations_priority:
                    name = "OPERATORS_2TOGETHER"
                    error = Error(name, errors_msgs.get(name), char, regex)
                else:
                    if operations_priority.get(char)==4: # Operadores unarios
                        expression = stack.pop()
                        stack.push(f"{expression}{char}")
                        last_was_expression = True
                    else:
                        stack.push(char)
                        last_was_expression = False
                
        elif char in other_symbols: #Parentesis
            if char=="(":
                if last_was_expression: # Concatenacion implicita
                    stack.push(".")
                expects_char = True # Para la siguiente iteracion
                pharentesis_lvl += 1
                stack.push(char)
                last_was_expression = False
            else: # char==")"
                if pharentesis_lvl==0:# error
                    name = "PHARENTESIS_CLOSES_UNOPENED"
                    error = Error(name, errors_msgs.get(name), ")", ")")
                else:
                    expression =  stack.pop()
                    if expression == "(":
                        name = "PHARENTESIS_EMPTY"
                        error = Error(name, errors_msgs.get(name), "()", "()")
                    else: 
                        
                        sub_expression_stk = Stack()
                        prev_char = expression
                        while  prev_char != "(":
                            sub_expression_stk.push(prev_char)
                            prev_char = stack.pop()   
                        sub_expression_stk.items.reverse()
                        expression, internal_error = __rebuild_expression(sub_expression_stk)
                        if internal_error:
                            error = internal_error
                        else:
                            stack.push(expression)
                            last_was_expression = True 
                            pharentesis_lvl -= 1                       
        else: #Caracteres
            if last_was_expression: # Concatenacion implicita
                stack.push(".")
            stack.push(char)
            alphabet.add(char)
            last_was_expression = True
            expects_char = False
        i += 1
    if error:
        return posfix, error, set()
    if pharentesis_lvl!=0:
        name = "PHARENTESIS_UNMATCH"
        return regex, Error(name, errors_msgs.get(name), "()", "()"), set()
    
    posfix, error = __rebuild_expression(stack=stack)
    if error:
        return regex, error, set()  
    return posfix, None, alphabet