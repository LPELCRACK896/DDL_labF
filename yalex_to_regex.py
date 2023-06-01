import re


def read_yalex(yalex_file):

    waiting_first_rule = False 
    expects_rule = False
    last_rule = None
    lets = {}
    rules = {}
    r_priority = []

    with open(yalex_file, 'r') as file:
        i = 0
        lines = file.readlines()
        error = None
        while not error and i<len(lines):
            line = lines[i]
            line = re.sub(r'(?<!["\'])[\t\n](?!["\'])', '', line)
            line_split = re.findall(r'''(?:[^ "']|"[^"]*"|'[^']*')+''', line)
            if len(line_split)>0:
                pref = line_split[0]
                accepted_pref = False
                pref_disp = None
                j = 0
                while not accepted_pref and j<len(line_split) and not error:
                    pref = line_split[j]
                    if not (pref==" " or pref==" " or pref=="\t"):
                        if pref=="\n":
                            accepted_pref = True
                            pref_disp = "skip"
                        elif pref=="let" or pref=="rule":
                            accepted_pref = True
                            pref_disp = pref
                        else:
                            if waiting_first_rule:
                                accepted_pref = True
                                pref_disp = "first_rule"
                            elif expects_rule:
                                if pref=="|":
                                    accepted_pref = True
                                    pref_disp = "extra_rule"
                    j += 1
            else:
                accepted_pref = True
                pref_disp = "skip"

            if not error:
                if accepted_pref:
                    if pref_disp != "skip":
                        rest_line = line_split[j:]
                        if pref_disp == "let":
                            if not waiting_first_rule:
                                expects_rule = False
                                r_line = "".join(rest_line)
                                if "=" in r_line:
                                    line_items = r_line.split("=")
                                    if len(line_items)==2:
                                        lets[line_items[0]] = line_items[1]
                                        r_priority.append(line_items[0])
                                    else:
                                        error = f"Syntax error: Expects proper assignation in let line {i+1}: {line}"
                                else:
                                    error = f"Syntax error: Expects asignation on let line {i+1}: {line} "
                            else:
                                error = f"Syntax error: Was expecting rule on ln {i+1} but got let statment instead: {line}"
                        elif pref_disp == "rule":
                            waiting_first_rule = True
                            expects_rule = True
                            if len(rest_line)==2:
                                waiting_first_rule = True
                                name = rest_line[0]
                                if rest_line[1].replace(" ", "")!="=":
                                    error = f"Syntax error: On rule line expected \"=\" right after rule variable name ln {i+1}. Got {rest_line[1]} instead"
                                else:
                                    rules[name] = {}
                                    last_rule = name

                            elif len(rest_line)==3:
                                waiting_first_rule = False
                                name = rest_line[0]
                                if rest_line[1].replace(" ", "")!="=":
                                    error = f"Syntax error: On rule line expected \"=\" right after rule variable name ln {i+1}. Got {rest_line[1]} instead"
                                else:
                                    last_rule = name
                                    rules[name] = {}
                                    rule_spl = rest_line[2]
                                    name, rule = rule_spl.split("{")
                                    rule = "{"+rule
                                    rules[name][rule_name] = actual_rule
                            elif len(rest_line)==4:
                                waiting_first_rule = False
                                name = rest_line[0]
                                if rest_line[1].replace(" ", "")!="=":
                                    error = f"Syntax error: On rule line expected \"=\" right after rule variable name ln {i+1}. Got {rest_line[1]} instead"
                                else:
                                    rules[name] = {}
                                    last_rule = name
                                    rule_name = rest_line[2]
                                    actual_rule = rest_line[3]
                                    if "{" in rule_name:
                                        rule_spl = rule_name.split("{") 
                                        rule_name = rule_spl[0]
                                        actual_rule = "{"+rule_spl[1]+actual_rule
                                    rules[name][rule_name] = actual_rule
                            else:
                                error = f"Syntax error: Unexepcted number of arguments on ln {i+1} (expected 2 or 3), line: {line}"
                        elif pref_disp == "first_rule":
                            waiting_first_rule = False
                            if rest_line:
                                content = "".join(rest_line)
                                pref = pref.replace("\t", "")
                                rules[last_rule][pref] = content
                            else:
                                error = f"Syntax error: Expected content between curly braces on ln {i+1}"
                        elif pref_disp == "extra_rule":
                            if rest_line:
                                r_line = "".join(rest_line)
                                name, content = r_line.split("{")
                                name = name.replace("\t", "")
                                content = "{"+content
                                if name and content:
                                    rules[last_rule][name] = content
                                else:
                                    error = f"Syntax error on ln {i+1}, expects rule name and output afterwards surronded by curly braces. Got {line} "
                else: 
                    error = f"Syntax error: Unexpected line format ln: {i+1}. \"{line}\""
            i += 1
        if not error:
            return None, lets, rules, r_priority
        return error, None, None, None

if __name__ == "__main__":
    filename = "ya.lex"
    error, lets, rules = read_yalex(filename)
    if not error:
        print("Valid")
    else:
        print(f"Error: {error}")
