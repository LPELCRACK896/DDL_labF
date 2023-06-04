let delim = [' ''\t''\n']
let ws = delim+
let letter = ['A'-'Z''a'-'z']
let digit = ['0'-'9']

rule tokens = 
    ws        { "WS" }
  | '+'       { "PLUS" }
  | '*'       { "TIMES" }
  | '('       { "LPAREN" }
  | ')'       { "RPAREN" }