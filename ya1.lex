(* Lexer para Gramática No. 2 - Expresiones aritméticas extendidas *)

(* Introducir cualquier header aqui *)

let delim = ["\s\t\n"]
let ws = delim+
let letter = ['A'-'Z''a'-'z']
let digit = ['0'-'9']
let digits = digit+
let id = letter(letter|digit)*
let number = digits("."digits)?('E'['+''-']?digits)?

rule tokens = 
    ws        { "WHITESPACE" }               (* Cambie por una acción válida, que devuelva el token *)
  | id        { "ID" }
  | number    { "NUMBER" }
  | '+'       { "PLUS" }
  | '-'       { "MINUS" }
  | '*'       { "TIMES" }
  | '/'       { "DIV" }
  | '('       { "LPAREN" }
  | ')'       { "RPAREN" }

(* Introducir cualquier trailer aqui *)