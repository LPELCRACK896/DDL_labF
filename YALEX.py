import os
import re
import c_styles as cs
from data_classes import Error
from stack import Stack
from patrones import SIMPLE_P, COMPOUND_P, REGEX_P, SPACES_P
from constants import LETTERS, UPPER_LETTERS, NUMBERS
from functools import reduce

class Yalex():
    def __new__(cls, yalex_file):
        if not cls.check_file(yalex_file):
            raise ValueError(f"Failed to create Yalex object with file {yalex_file}")
        return super(Yalex, cls).__new__(cls)

    def __init__(self, yalex_file) -> None:
        self.filename = yalex_file
        self.errors = Stack()
        self.contenido_crudo: str = self.__read()
        self.body, self.start_regex = self.__body_extractor()
        self.regex: dict = self.__extract_regex()
        self.tokens = self.__extract_tokens()

    @staticmethod
    def check_file(filename:str):
        only_filename, extension = filename.rsplit('.', 1)
        if not extension=="lex":
            print(cs.s_red("Invalid extension"))
            return False
        current_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(current_dir, filename) 
        if not os.path.exists(file_path):
            print(cs.s_red("File doesn't exist in directory"))
            return False
        return True

    def __body_extractor(self):
        contenido = (self.contenido_crudo).split("\n")
        c_head = (lambda contenido: any('{' in line.strip() and 'let' not in line and 'rule' not in line for line in contenido)) (contenido)
        c_footer = self.__c_footer(contenido)
        indice_fin_contenido = self.__footer_extractor(contenido)[1] if c_footer else len(contenido) 
        indice_inicio_contenido = self.__head_extractor(contenido)[2] if c_head else 0
        comentarios_re = re.compile(r'\(\*.*?\*\)', re.DOTALL)
        body =  "\n".join(contenido[:indice_fin_contenido])
        body = (lambda body: (re.sub(comentarios_re, '', body)).replace("\'\"\'","(' ハ ')").replace("\"\'\"","(' ワ ')").replace("\'`\'","(' カ ')").replace('"', " ' ").replace("'", " ' "))(body)        
        return body, indice_inicio_contenido

    def __extract_regex(self):
        self.regex = {}
        contenido = self.body.split("\n")
        clauses = {"}": "{", ")": "("}
        reg_stack = Stack()
        start_rules = False
        i = 1
        while not start_rules and i<len(contenido):
            linea = contenido[i]
            desbalance = False
            j = 0
            while not desbalance and j<len(linea):
                char = linea[j]
                if char in clauses.values(): reg_stack.push((char, i))
                elif char in clauses:
                    if reg_stack.isEmpty() or reg_stack.peek()[0]!= clauses.get(char):
                        self.errors.push(Error(1,f"Desbalance de parentesis en ln: \"{linea}\"","LABD"))
                        desbalance = True
                    else: reg_stack.pop()
                j += 1
            linea = linea.strip()
            if linea:
                if re.match(REGEX_P, linea):
                    self.regex = self.__add_regex(linea)
                elif linea.startswith("let"): self.errors.push(Error(3, "Regex no puede incluir el termino let", "LABD"))
                elif linea.startswith("rule tokens"): start_rules = True
            i += 1      
        self.end_reg = i + self.start_regex
        if not reg_stack.isEmpty(): self.errors.add_stack_on_top([Error(2, f"Desbalance de apertura en linea {linea_parentesis[1]}", "LABD") for linea_parentesis in reg_stack.items])
        return self.regex
    
    def __add_regex(self, linea):
        linea = self.__trim_quotes((lambda line: reduce(lambda x, y: x.replace(y, ' ' + y + ' '), '*+|?()', line))(linea)).replace('" "', '"ε"').replace("' '", "'ε'").split(" ")
        name = linea[1]
        linea_regex =  linea[3:]
        content = ""
        for item in linea_regex:
            if any(char in item for char in ["'", '"', '`']):
                if item == "''" : content += "\\s"
                else: content += item.replace('"', '').replace("'", "").replace('+', '\+').replace('.', '\.').replace('*', '\*').replace('(', '\(').replace(')', '\)')
            elif not any(operator in item for operator in "*+|?") and len(item)>1:
                if item in self.regex: content += self.regex[item]
                else: self.errors.push(Error(5, f"En la defincion del token {name} se hace referencia a un token no definidio {item}", "LABD"))
            else: content += item
        linea_regex = content.replace('ε', ' ')
        if re.search(COMPOUND_P, linea_regex):
            results = re.search(COMPOUND_P, linea_regex)
            f_inicial, f_final, l_inicial, l_final = results.group(1), results.group(2), results.group(3), results.group(4)
            f_range, l_range = self.__re_range(f_inicial, f_final), self.__re_range(l_inicial, l_final) 
            reg = f'({f_range}|{l_range})'
            repl = ""
            finish = False
            i = 0
            while not finish and i<len(linea_regex):
                finish = linea_regex[i] == ']'
                repl += linea_regex[i]
                i += 1
            linea_regex = linea_regex.replace(repl, reg)
        elif re.search(SIMPLE_P, linea_regex):
            results = re.search(SIMPLE_P, linea_regex)
            inicial, final = results.group(1), results.group(2)
            res = "("+ self.__re_range(inicial, final)+")"
            linea_regex = linea_regex.replace(f"[{inicial}-{final}]", res)
        elif re.search(SPACES_P, linea_regex):
            results = re.search(SPACES_P, linea_regex)
            replacment_mapping = { '\\s': r'\サ', '\\t': r'\ラ', '\\n': r'\ナ', '"': r'\"',}
            replac_search = re.findall(r"(\\s|\\t|\\n)", results.group(0))
            replac_reg = '|'.join([replacment_mapping[st] for st in replac_search])
            linea_regex = re.sub(r"\[(\\s|\\t|\\n|,|\s)+\]", f'({replac_reg})', linea_regex)
        linea_regex = linea_regex.strip()
        
        self.regex[name] = linea_regex
        return self.regex
    
    def __re_range(self, incial, final):
        range_numbers_to_or = lambda initial, final: '|'.join([str(i) for i in range(int(initial) + 1, int(final)+1)])
        replacment = str(incial)+"|"
        if final.lower() in LETTERS and incial.lower() in NUMBERS:
            replacment += range_numbers_to_or(incial, str(9))+'|'
            letra_i = 'A' if final in UPPER_LETTERS else 'a'
            replacment += letra_i + '|' + self.__get_range_letters_to_or(letra_i, final)
        elif incial.lower() in LETTERS:
            final_letter = 'Z' if incial in UPPER_LETTERS else 'z'
            if final in NUMBERS: replacment += self.__get_range_letters_to_or(incial, final_letter) + '|0|' + range_numbers_to_or('0', final)
            else: replacment += self.__get_range_letters_to_or(incial, final)
        elif incial in NUMBERS: replacment += range_numbers_to_or(incial, final)
        return replacment
    
    def __get_range_letters_to_or(self, inicial, final, is_upper = False):
        letters = UPPER_LETTERS if is_upper else LETTERS
        if ord(inicial)>ord(final) and final.lower() in letters:
            return self.__get_range_letters_to_or(inicial, 'z') + '|' + self.__get_range_letters_to_or(chr(ord(inicial.upper())-1), final)
        return ("|".join([chr(i) for i in range(ord(inicial) + 1, ord(final))])) +'|'+ final
    
    def __head_extractor(self, contenido):
        i = 0
        end_comment = False
        start_comment = False
        contenido_header = ""
        while not end_comment and i<len(contenido):
            linea  = contenido[i]
            j = 0
            while not end_comment and  j<len(linea):
                char = linea[j]
                if char == "{" :
                    start_comment = True 
                elif char!='}':
                    if start_comment: contenido_header += char
                else:
                    end_comment = True
                j += 1
            contenido_header += "\n"
            i += 1
        return contenido_header.rstrip(), 0, i

    def __footer_extractor(self, contenido):
        no_longer_footer = False
        i  = len(contenido)
        contenido_footer = ""
        while not no_longer_footer and i>-1:
            linea = contenido[i]
            foot_cont = ""
            for char in linea:
                if char == '{':
                    no_longer_footer = True
                    foot_cont = foot_cont.rstrip()         
                elif char != '}':
                    foot_cont = char + foot_cont
            contenido_footer = foot_cont + contenido_footer
            i -= 1
        no_longer_footer: contenido_footer = "\n" + contenido_footer
        fixed_contenido_footer = ""
        for i_lineas_footer in range(i, len(contenido)):
            linea = contenido[i_lineas_footer]
            finish_this_line_footer = False
            j = 0
            while not finish_this_line_footer and j<len(linea):
                char = linea[j]
                if char!='{' and char != '}':
                    fixed_contenido_footer += char
                elif char == '}':
                    finish_this_line_footer = True
                    fixed_contenido_footer = fixed_contenido_footer.rstrip()
            fixed_contenido_footer = fixed_contenido_footer + "\n"

        return fixed_contenido_footer, i+1, len(contenido)

    def __extract_tokens(self):
        update_regex = lambda expressions: [element + [self.regex[element[0]]] if element[0] in self.regex else element for element in expressions]
        rework_string = lambda expression: expression.replace('.', '\.').replace('+', '\+').replace('*', '\*').replace('"', '').replace("'", "")

        text_tokens_separated = (lambda expressions: [item.replace('\n', '').strip() for item in expressions])(self.__trim_quotes(self.body.split("rule tokens =")[1]).strip().split('|'))
        tokens = (lambda expressions: [[rework_string(element[0]).replace("\\", "") if "'" in element[0] or '"' in element[0] else element[0].replace("\\", "")] + element[1:] for element in expressions])(self.__cast_text_token(text_tokens_separated))
        self.tokens = update_regex(tokens)
        return self.tokens
    
    def __read(self):
        contenido  = ""
        with open(self.filename, 'r') as f:
            contenido = f.read()
        return contenido
    
    def build(self):
        pass

    def __trim_quotes(self, line): return re.sub(r"'([^']+)'", lambda m: "'" + m.group(1).strip() + "'", line) 

    def __cast_text_token(self, text_tokens):
        list_tokens = []
        for linea_token in text_tokens:
            splitt = re.split(r"\s+", linea_token, 1)
            if len(splitt)==2:
                name, valor = splitt[0], splitt[1]
                valor = valor.replace("\t", '').replace('{' , '').replace('}', '').strip()
                if not name in self.regex.keys(): 
                    linea_regex = name.split(" ")
                    content = ""
                    for item in linea_regex:
                        if any(char in item for char in ["'", '"', '`']):
                            if item == "''" : content += "\\s"
                            else: content += item.replace('"', '').replace("'", "").replace('+', '\+').replace('.', '\.').replace('*', '\*').replace('(', '\(').replace(')', '\)')
                        elif not any(operator in item for operator in "*+|?") and len(item)>1:
                            if item in self.regex: content += self.regex[item]
                            else: self.errors.push(Error(5, f"En la defincion del token {name} se hace referencia a un token no definidio {item}", "LABD"))
                        else: content += item
                    linea_regex = content.replace('ε', ' ')
                    if re.search(COMPOUND_P, linea_regex):
                        results = re.search(COMPOUND_P, linea_regex)
                        f_inicial, f_final, l_inicial, l_final = results.group(1), results.group(2), results.group(3), results.group(4)
                        f_range, l_range = self.__re_range(f_inicial, f_final), self.__re_range(l_inicial, l_final) 
                        reg = f'({f_range}|{l_range})'
                        repl = ""
                        finish = False
                        i = 0
                        while not finish and i<len(linea_regex):
                            finish = linea_regex[i] == ']'
                            repl += linea_regex[i]
                            i += 1
                        linea_regex = linea_regex.replace(repl, reg)
                    elif re.search(SIMPLE_P, linea_regex):
                        results = re.search(SIMPLE_P, linea_regex)
                        inicial, final = results.group(1), results.group(2)
                        res = "("+ self.__re_range(inicial, final)+")"
                        linea_regex = linea_regex.replace(f"[{inicial}-{final}]", res)
                    elif re.search(SPACES_P, linea_regex):
                        results = re.search(SPACES_P, linea_regex)
                        replacment_mapping = { '\\s': r'\サ', '\\t': r'\ラ', '\\n': r'\ナ', '"': r'\"',}
                        replac_search = re.findall(r"(\\s|\\t|\\n)", results.group(0))
                        replac_reg = '|'.join([replacment_mapping[st] for st in replac_search])
                        linea_regex = re.sub(r"\[(\\s|\\t|\\n|,|\s)+\]", f'({replac_reg})', linea_regex)
                    name = linea_regex.strip()
                list_tokens.append([name, valor])
            else:
                self.errors.push(Error(500 ,f"Error en {linea_token}. Falta parametros en definicion de token", "SYNTAXIS"))
                name = splitt[0]
        return list_tokens

    def __c_footer(self, contenido):
        j = len(contenido) - 1
        while not j==-1:
            line = contenido[j].strip()
            if line:
                if 'return' in line or '|' in line:return False
                if line == "}" or "}" in line:return True
            j -= 1
        return False
    
""" def file_into_list(filename):
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
    return content """