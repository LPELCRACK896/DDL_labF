

let delim = [' ''\t''\n']
let ws = delim+
let letter = ['A'-'Z''a'-'z']
let digit = ['0'-'9']
let id = letter(letter|digit)*

rule tokens = 
    ws        { "WS" }
  | id        { "ID" }               
  | '+'       { "PLUS" }
  | '*'       { "TIMES" }
  | '('       { "LPAREN" }
  | ')'       { "RPAREN" }