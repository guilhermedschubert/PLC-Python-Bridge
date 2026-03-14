from snap7.client import Client
from TAGS import TAG, DataVerify, ParseTag

class s7legacy():

    # Inicialização da classe

    # Minha ideia é trabalhar cada CLP sendo uma classe

    def __init__(self, ip: str, rack: int, slot: int, name: str, port: int = 102):
        self.ip         = ip
        self.rack       = rack
        self.slot       = slot
        self.name       = name
        self.port       = port
        self.plc        = None

    def __str__(self):

        # Retorna Informações do objeto ao printar ele
         
        return (
            f"Nome: {self.name}\n"
            f"IP: {self.ip}\n"
            f"Rack: {self.rack}\n"
            f"Slot: {self.slot}\n"
            f"Porta TCP: {self.port}\n"
        )
    
    def connect(self):

        # Faz o connecto do CLP

        if not self.ip:

            raise ValueError("IP não pode ser vazio!")
        
        if self.rack is None:

            raise ValueError("Rack não pode ser vazio!")
        
        if self.slot is None:

            raise ValueError("Slot não pode ser vazio!")
        
        
        self.plc = Client()
        self.plc.connect(self.ip, self.rack, self.slot, self.port)

    def read(self, tag: TAG):

        # Validação de tipo de dado
        if not isinstance(tag, TAG):
            raise TypeError("read() espera um objeto TAG")

        # Validação de clp iniciado
        if self.plc is None:
            raise RuntimeError("PLC não conectado! Execute connect() primeiro.")

        return self.plc.read_area(tag.area, tag.db, tag.start, tag.size)
    
    def write(self, tag: TAG, value):
        # Validação de tipo de dado
        if not isinstance(tag, TAG):
            raise TypeError("write() espera um objeto TAG")

        if not value:
            raise ValueError("value não pode ser vazio!")

        DataVerify(tag.data_type, value)
        
        # Validação de clp iniciado
        if self.plc is None:
            raise RuntimeError("PLC não conectado! Execute connect() primeiro.")
        

        return self.plc.write_area_area(tag.area, tag.db, tag.start, tag.size)

CLP = s7legacy('192.168.0.1',1,0,'CLP de Teste')
Tag = ParseTag('Tag_1', 'DB10.DBX0.3')
print(Tag)
print(CLP.read(Tag))