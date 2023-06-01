/* Configuración del parser para gramática No.1 */
/* Sigue la gramática SLR: */
/* E → E + T | T */
/* T → T ∗ F | F */
/* F → ( E ) | id */

%token ID
%token PLUS
%token TIMES
%token LPAREN RPAREN
%token WS
IGNORE WS

%%

expression:
    expression PLUS term
  | term
;
term:
    term TIMES factor
  | factor
;
factor:
    LPAREN expression RPAREN
  | ID
;