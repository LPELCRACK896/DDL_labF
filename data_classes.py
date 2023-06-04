from dataclasses import dataclass
from stack import Stack

@dataclass
class Error:
    code: int
    message: str
    type: str

    def __str__(self):
        return f"Error {self.type} {self.code}: {self.message}"

@dataclass
class Response:
    status: int
    success: bool
    errors: Stack = Stack()
    msg: str = ""

    def __str__(self) -> str:
        exito = "Proceso finalizado con exito" if self.success else "Proceso no finalizado correctamente."
        error = None
        if not self.errors.isEmpty():
            error = f"\n{self.errors}"
        return f"{self.status} - {exito} - {self.msg} {error}"    

@dataclass
class LR0Item:
    produccion: tuple
    posicion: int
    derivado: bool = False

    def __str__(self): 
        return f'{self.produccion[0]}→{" ".join(self.produccion[1][:self.posicion]) + "•" + " ".join(self.produccion[1][self.posicion:])}'

    def __repr__(self) -> str: 
        return self.__str__()
    
    def __eq__(self, item): 
        return self.produccion == item.produccion and self.posicion == item.posicion

    def __hash__(self): 
        return hash((self.produccion, self.posicion))




@dataclass
class ParserTable:
    producciones: dict
    estados: list
    transiciones: list


@dataclass
class LR1Item:
    produccion: tuple
    posicion: int
    anticipacion: set
    derivado: bool = False

    def __str__(self): 
        return f'{self.produccion[0]}→{" ".join(self.produccion[1][:self.posicion]) + "•" + " ".join(self.produccion[1][self.posicion:])}, {self.anticipacion}'

    def __repr__(self) -> str: 
        return self.__str__()

    def __eq__(self, item): 
        return self.produccion == item.produccion and self.posicion == item.posicion and self.anticipacion == item.anticipacion

    def __hash__(self): 
        return hash((self.produccion, self.posicion, frozenset(self.anticipacion)))
