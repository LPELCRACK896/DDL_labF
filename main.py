from yalex_to_regex import read_yalex
from YALEX import *
filename = "yalex.txt"
lets, rules = read_yalex(filename)
yalex = YALEX(lets, rules)