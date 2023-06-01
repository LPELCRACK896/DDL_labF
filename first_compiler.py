from dataclasses import dataclass
from stack import Stack
from yalex_to_regex import read_yalex
import re
from AFD import AFD
from AFN import AFN
from Tokenized_AFD import union_afds, SuperAFN

