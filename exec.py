from grammatics_elements import *

def main():
    
    regex = {}
    tokens_goo = []
    
    """     with open('ya.lex', 'r') as f:
        contenido_archivo = f.read() """

    with open('ya1.lex', 'r') as f:
        contenido_archivo = f.read()

    
    _, _, contenido_archivo, i = build_header_and_trailer(contenido_archivo)
    contenido_archivo = replace_quotation_mark(clean_comments(contenido_archivo))
    regex, errors, end = build_regex(contenido_archivo, i)
    tokens_LEX, errors = build_tokens(contenido_archivo, regex, errors, end+1)

    # tokens, diccionario_producciones, errors = parse_yapl_file('yapl.lex', errors)
    tokens, diccionario_producciones, errors = parse_yapl_file('yapl1.lex', errors)
    if errors:
        print("Errores durante lectura:")
        for error in errors:
            print(error)
        return 


    for token in tokens:
        for lex_token in tokens_LEX:
            evald = evalToken(lex_token)
            if token == evald:
                tokens_goo.append(token)
        if token not in tokens_goo:
            errors.append(f"Token {token} no definido en el YALEX")

    if len(tokens_goo) < len(tokens_LEX):
        errors.append("Faltaron definir tokens en el YAPAR")

    if errors:
        print("Errores durante lectura:")
        for error in errors:
            print(error)
        return

    producciones_convertidas = convert_productions(diccionario_producciones)
    estados, transiciones = LR_canonical_collection(producciones_convertidas)
    lr0_renderer(estados, transiciones)

    print("LL:")

    producciones_convertidas = convert_productions2(diccionario_producciones)
    primero = LL_first_sets(producciones_convertidas)
    siguiente = LL_follow_sets(producciones_convertidas, primero)

    print("-----First sets-----")
    for no_terminal, conjunto_primero in primero.items():
        print(f"{no_terminal}: {conjunto_primero}")

    print("-----Follow sets-----")
    for no_terminal, conjunto_siguiente in siguiente.items():
        print(f"{no_terminal}: {conjunto_siguiente}")
if __name__ == "__main__":
    main()