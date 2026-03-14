from snap7.type import Areas
import re
import snap7
from dataclasses import dataclass
from typing import Optional


def DataVerify(tag, value) -> bool:

    TYPE_RULES = {
        "Bool"  : {"py_type": bool,  "min": 0,            "max": 1},
        "Int"   : {"py_type": int,   "min": -32768,        "max": 32767},
        "DInt"  : {"py_type": int,   "min": -2147483648,   "max": 2147483647},
        "Real"  : {"py_type": float, "min": -3.4028235e38, "max": 3.4028235e38},
        "LReal" : {"py_type": float, "min": -1.7976931e308,"max": 1.7976931e308},
        "String": {"py_type": str,   "min": 0,             "max": 254},
    }

    if tag.data_type not in TYPE_RULES:
        raise ValueError(f"Tipo '{tag.data_type}' não suportado na validação!")

    rules = TYPE_RULES[tag.data_type]

    # Verifica tipo Python
    if not isinstance(value, rules["py_type"]):
        raise TypeError(f"Valor '{value}' inválido para o tipo {tag.data_type}. Esperado: {rules['py_type'].__name__}")

    # String valida tamanho
    if tag.data_type == "String":
        if len(value) > rules["max"]:
            raise ValueError(f"String muito longa: {len(value)} chars. Máximo: {rules['max']}")
        return True

    # Numéricos validam range
    if not (rules["min"] <= value <= rules["max"]):
        raise ValueError(f"Valor {value} fora do range para {tag.data_type}. Range: [{rules['min']}, {rules['max']}]")

    return True



@dataclass
class Snap7Tag:
    data_type: str   # "bool", "byte", "int", "word", "dword", "real"
    area: Areas
    db: int
    start: int
    size: int
    bits: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "data_type": self.data_type,
            "area":      self.area,
            "db":        self.db,
            "start":     self.start,
            "size":      self.size,
            "bits":      self.bits,
        }


# Sufixo TIA → (data_type, size_bytes)
_DB_SUFFIX = {
    "X": ("bool",  1),
    "B": ("byte",  1),
    "W": ("word",  2),
    "D": ("dword", 4),
    "R": ("real",  4),
    "I": ("int",   2),
}

# Prefixo de área fora de DB
_AREA_PREFIX = {
    "M": Areas.MK,  # Merker
    "I": Areas.PE,  # Inputs
    "E": Areas.PE,  # Inputs (notação alemã)
    "Q": Areas.PA,  # Outputs
    "A": Areas.PA,  # Outputs (notação alemã)
}

# Sufixo de tipo fora de DB → (data_type, size)
_MEM_SUFFIX = {
    "X": ("bool",  1),
    "B": ("byte",  1),
    "W": ("word",  2),
    "D": ("dword", 4),
    "R": ("real",  4),
}


def parse_tag(address: str) -> Snap7Tag:
    """
    Interpreta um endereço no estilo TIA Portal e retorna um Snap7Tag.

    Formatos aceitos
    ----------------
    DB dentro de Data Block:
      DB<n>.DBX<byte>.<bit>   → bool   ex: DB10.DBX0.3
      DB<n>.DBB<byte>         → byte   ex: DB10.DBB4
      DB<n>.DBW<byte>         → word   ex: DB10.DBW2
      DB<n>.DBD<byte>         → dword  ex: DB10.DBD8
      DB<n>.DBR<byte>         → real   ex: DB10.DBR12
      DB<n>.DBI<byte>         → int    ex: DB10.DBI6

    Memória, Entradas, Saídas:
      M<byte>.<bit>           → bool   ex: M0.3
      MB<byte>                → byte   ex: MB10
      MW<byte>                → word   ex: MW10
      MD<byte>                → dword  ex: MD10
      I<byte>.<bit>  / E...   → bool   ex: I0.0
      IB<byte>       / EB...  → byte   ex: IB0
      Q<byte>.<bit>  / A...   → bool   ex: Q1.5
      QB<byte>       / AB...  → byte   ex: QB0
    """
    address = address.strip().upper()

    # ── DB<n>.DB<sufixo><byte>[.<bit>] ──────────────────────────────────────
    m = re.fullmatch(
        r"DB(\d+)\.DB([XBWDRI])(\d+)(?:\.(\d+))?",
        address
    )
    if m:
        db_num   = int(m.group(1))
        suffix   = m.group(2)          # X B W D R I
        byte_idx = int(m.group(3))
        bit_idx  = int(m.group(4)) if m.group(4) is not None else None

        dtype, size = _DB_SUFFIX[suffix]

        if dtype == "bool":
            if bit_idx is None:
                raise ValueError(f"Endereço BOOL requer o bit. Ex: DB{db_num}.DBX{byte_idx}.3")
            if not (0 <= bit_idx <= 7):
                raise ValueError(f"Bit inválido: {bit_idx}. Deve ser 0–7.")
        else:
            if bit_idx is not None:
                raise ValueError(f"Tipo '{dtype}' não usa notação de bit.")

        return Snap7Tag(
            data_type=dtype,
            area=Areas.DB,
            db=db_num,
            start=byte_idx,
            size=size,
            bits=bit_idx,
        )

    # ── Área de memória / IO sem DB ─────────────────────────────────────────
    # Casos: M0.3  MB10  MW10  MD10  I0.0  IB0  Q1.5  QB0  (e variantes E/A)
    m = re.fullmatch(
        r"([MIEQA])(B|W|D|R)?(\d+)(?:\.(\d+))?",
        address
    )
    if m:
        prefix   = m.group(1)           # M I E Q A
        type_mod = m.group(2)           # B W D R  (ausente = X quando tem .<bit>)
        byte_idx = int(m.group(3))
        bit_idx  = int(m.group(4)) if m.group(4) is not None else None

        area = _AREA_PREFIX[prefix]

        # sem modificador de tipo
        if type_mod is None:
            # M0.3 → BOOL   /   M10 sem bit → ambíguo, trata como byte
            if bit_idx is not None:
                dtype, size = "bool", 1
            else:
                dtype, size = "byte", 1
        else:
            dtype, size = _MEM_SUFFIX[type_mod]
            if bit_idx is not None:
                raise ValueError(f"Tipo '{dtype}' não usa notação de bit.")

        if dtype == "bool" and bit_idx is not None and not (0 <= bit_idx <= 7):
            raise ValueError(f"Bit inválido: {bit_idx}. Deve ser 0–7.")

        return Snap7Tag(
            data_type=dtype,
            area=area,
            db=0,
            start=byte_idx,
            size=size,
            bits=bit_idx,
        )

    raise ValueError(
        f"Endereço '{address}' não reconhecido.\n"
        "Exemplos válidos: DB10.DBX0.3 | DB5.DBW4 | M0.3 | MW10 | I0.0 | Q1.5"
    )


class TAG():
    def __init__(self, name: str, data_type: str, start: int, size: int, area: Areas = Areas.DB, db: int = 0):
        self.name           = name
        self.data_type      = data_type
        self.area           = area
        self.db             = db
        self.start          = start
        self.size           = size


class S7DataTypes():
     def __init__(self):
        self.bool = 1
        self.int = 16
        self.dint = 32
        self.real = 64


