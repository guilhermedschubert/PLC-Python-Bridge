from snap7.type import Areas


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

class TAG():
    def __init__(self, name: str, data_type: str, start: int, size: int, area: Areas = Areas.DB, db: int = 0):
        self.name           = name
        self.data_type      = data_type
        self.area           = area
        self.db             = db
        self.start          = start
        self.size           = size