

let delim = [' ''\t''\n']
let ws = delim+
let letter = ['A'-'Z''a'-'z']
let digit = ['0'-'9']
let digits = digit+
let id = letter(letter|digit)*
let number = digits('.'digits)?('E'['+''-']?digits)?

rule tokens = 
    ws        { "WHITESPACE" }
  | id        { "ID" }
  | number    { "NUMBER" }
  | '+'       { "PLUS" }
  | '-'       { "MINUS" }
  | '*'       { "TIMES" }
  | '/'       { "DIV" }
  | '('       { "LPAREN" }
  | ')'       { "RPAREN" }

