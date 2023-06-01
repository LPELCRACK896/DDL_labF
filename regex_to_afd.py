from AFD import AFD 
class SyntaxTree:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def parse_regex(regex):
    precedence = {'?': 0, '|': 1, '.': 2, '*': 3, '+': 3}
    output = []
    operators = []

    def pop_operators(predicate):
        while operators and predicate(operators[-1]):
            op = operators.pop()
            if op in ('*', '+', '?'):
                node = SyntaxTree(op, output.pop())
            else:
                right = output.pop()
                left = output.pop()
                node = SyntaxTree(op, left, right)
            output.append(node)

    for char in regex:
        if char == '(':
            operators.append(char)
        elif char == ')':
            pop_operators(lambda op: op != '(')
            operators.pop()  
        elif char in precedence:
            pop_operators(lambda op: op != '(' and precedence[char] <= precedence[op])
            operators.append(char)
        else:
            output.append(SyntaxTree(char))

    pop_operators(lambda _: True)

    return output.pop()

def compute_functions(node):
    if node is None:
        return (False, set(), set(), {})

    if node.value in ('a', 'b'):
        nullable = False
        first_pos = {node}
        last_pos = {node}
        next_pos = {}
    else:
        nullable_left, first_pos_left, last_pos_left, next_pos_left = compute_functions(node.left)
        nullable_right, first_pos_right, last_pos_right, next_pos_right = compute_functions(node.right)

        if node.value == '.':
            nullable = nullable_left and nullable_right
            first_pos = first_pos_left if nullable_left else first_pos_left | first_pos_right
            last_pos = last_pos_right if nullable_right else last_pos_left | last_pos_right
            next_pos = {**next_pos_left, **next_pos_right}
            for p in last_pos_left:
                next_pos[p] = next_pos.get(p, set()) | first_pos_right
        elif node.value == '|':
            nullable = nullable_left or nullable_right
            first_pos = first_pos_left | first_pos_right
            last_pos = last_pos_left | last_pos_right
            next_pos = {**next_pos_left, **next_pos_right}
        elif node.value == '*':
            nullable = True
            first_pos = first_pos_left
            last_pos = last_pos_left
            next_pos = next_pos_left
            for p in last_pos:
                next_pos[p] = next_pos.get(p, set()) | first_pos
        elif node.value == '+':
            nullable = False
            first_pos = first_pos_left
            last_pos = last_pos_left
            next_pos = next_pos_left
            for p in last_pos:
                next_pos[p] = next_pos.get(p, set()) | first_pos
        elif node.value == '?':
            nullable = True
            first_pos = first_pos_left
            last_pos = last_pos_left
            next_pos = next_pos_left

    return (nullable, first_pos, last_pos, next_pos)

def regex_to_dfa(regex):
    tree = parse_regex(regex)
    nullable, first_pos, last_pos, next_pos = compute_functions(tree)

    state_num = 0
    marked_states = set()
    unmarked_states = {frozenset(first_pos)}
    state_mapping = {}
    transitions = {}

    while unmarked_states:
        curr_state = unmarked_states.pop()
        state_mapping[curr_state] = str(state_num)
        state_num += 1
        marked_states.add(curr_state)
        transitions[state_mapping[curr_state]] = {}

        for symbol in set(node.value for node in curr_state if node.value not in ('*', '+', '|', '.', '?')):
            next_states = set().union(*[next_pos[node] for node in curr_state if node.value == symbol])

            if next_states not in marked_states:
                unmarked_states.add(frozenset(next_states))

            if symbol not in transitions[state_mapping[curr_state]]:
                transitions[state_mapping[curr_state]][symbol] = state_mapping[frozenset(next_states)]

    accepting_states = [state_mapping[state] for state in state_mapping if any(node.value == '#' for node in state)]

    return AFD(state_mapping[frozenset(first_pos)], list(set(regex) - {'*', '+', '|', '.', '?', '(', ')'}), list(state_mapping.values()), accepting_states, transitions)

if __name__ == "__main__":
    regex = "a|b*+c?(de)"  
    dfa = regex_to_dfa(regex)
    dfa.draw_afd()
