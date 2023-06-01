from grammatics_elements import *

with open('yalex/lex2.yal', 'r') as f:
    yalex_content = f.read()

header_result = ''
regex = {}

file_content = yalex_content

header_result, trailer_result, file_content,i = build_header_and_trailer(file_content)
file_content = replace_quotation_mark(file_content)
regex,errorStack,fin = build_regex(file_content,i)
LEXtokens,errorStack = build_tokens(file_content, regex,errorStack,fin+1)

tokens, productions_dict,errorStack = parse_yalp_file('yapar/lex2.yalp',errorStack)

if errorStack:
    print("Error stack:")
    for error in errorStack:
        print(error)
    exit()

gooTokens = []

for token in tokens:
    for lex_token in LEXtokens:
        evald = evalToken(lex_token)
        if token == evald:
            gooTokens.append(token)
    if token not in gooTokens:
        errorStack.append(f"Token {token} no definido en el YALEX")

if len(gooTokens) < len(LEXtokens):
    errorStack.append("Faltaron Definir tokens en el YAPAR")

if errorStack:
    print("Error stack:")
    for error in errorStack:
        print(error)
    exit()

converted_productions = convert_productions(productions_dict)

states, transitions = canonical_collection(converted_productions)

print('Estados:')
for i, state in enumerate(states):
    print(f'{i}: {state}')

print('Transiciones:')
for transition in transitions:
    print(transition)

lr0_renderer(states, transitions)

print("\n------------LL----------\n\n")

def convert_productions(productions):
    converted_productions = {}
    for key, value in productions.items():
        converted_productions[key] = [prod.split() for prod in value]
    return converted_productions

print(productions_dict)
converted_prod = convert_productions(productions_dict)
first = LL_first_sets(converted_prod)
follow = LL_follow_sets(converted_prod, first)

print("First sets:")
for non_terminal, first_set in first.items():
    print(f"{non_terminal}: {first_set}")

print("\nFollow sets:")
for non_terminal, follow_set in follow.items():
    print(f"{non_terminal}: {follow_set}")
