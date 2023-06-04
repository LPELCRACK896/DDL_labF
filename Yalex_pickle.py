from dataclasses import dataclass
from Tokenized_AFD import render_super_afn, SuperAFN, file_into_list

@dataclass
class YalexPickle:
    filename: str
    yalex_reference: str
    state: str = "non-defined"
    super_afn: SuperAFN = None