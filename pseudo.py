from re import match, sub
from collections import OrderedDict

ORDERS = ['^J[PNZ]?\s+.+', '^[A-Z_]+\s+D[CS]\s+INTEGER.+', '^(L[AR]?|ST)\s+[0-9]+\s+,\s+.+', '^[ASMDC]R?\s+[0-9]+\s+,\s+.+']
LABELS = dict()
REGISTER = [0] * 16
MEMORY = OrderedDict()
STATE = 0

def set_state(target):
    global STATE
    if REGISTER[int(target)] == 0: STATE = 0b00
    elif REGISTER[int(target)] > 0: STATE = 0b01
    else: STATE = 0b10

def read_adress(cell):
    return list(MEMORY.keys()).index(cell)
def get_label(cell):
    return list(MEMORY.keys())[int(cell)]

def interpret(line):
    global STATE, REGISTER, MEMORY, LABELS
    if match('^[A-Z_]+\s+D[CS]\s+INTEGER', line): # DYREKTYWY DEKLARACJI ZMIENNYCH
        line = sub('[\(\)\n]','', line).split(' ')
        label = line[0]
        order = line[1]
        if order == "DC":
            value = int(line[3])
            MEMORY[label] = value
        elif order == "DS":
            MEMORY[label] = None
    elif match('^(L[AR]?|ST)\s+[0-9]+,\s+.+', line): # OPERACJE ŁADOWANIA Z I DO PAMIĘCI
        line = sub('[,\n]','', line).split(' ')
        order = line[0]
        target = line[1]
        source = line[2]
        if order == 'L': REGISTER[int(target)] = MEMORY[source]
        elif order == 'LA': REGISTER[int(target)] = read_adress(source)
        elif order == 'LR': REGISTER[int(target)] = REGISTER[int(source)]
        elif order == 'ST': 
            source = line[1]
            target = line[2]
            if match('^[A-Z_]+$', target): MEMORY[target] = REGISTER[int(source)]
            elif match('^[0-9]+$', target): MEMORY[get_label(target)] = REGISTER[int(source)]
    elif match('^[ASMDC]R?\s+[0-9]+,\s+.+', line): # OPERACJE ARYTMETYCZNE I PORÓWNANIA
        line = sub('[,\n]','', line).split(' ')
        order = line[0]
        target = line[1]
        source = line[2]
        # SPRAWDZANIE CZY OPERACJA TYPU REJESTR - REJESTR
        if match('.R', order): source = REGISTER[int(source)]
        else: source = MEMORY[source]
        # ADD, SUBTRACT, MULTIPLY, DIVIDE
        if match('^A', order): REGISTER[int(target)] += source
        elif match('^S', order): REGISTER[int(target)] -= source
        elif match('^M', order): REGISTER[int(target)] *= source
        elif match('^D', order): REGISTER[int(target)] /= source
        set_state(target)
        # COMPARE
        if match('^C', order):
            target = REGISTER[int(target)]
            if target == source: STATE = 0b00
            elif target < source: STATE = 0b01
            elif target > source: STATE = 0b10
            else: STATE = 0b11
    elif match('^J[PNZ]?\s+[A-Z_]+', line): # OPERACJE SKOKU
        line = line.split(' ')
        order = line[0]
        label = sub('\n','',line[1])
        if order == "J": program.seek(LABELS[label])
        elif order == "JP":
            if STATE == 0b01: program.seek(LABELS[label])
        elif order == "JN":
            if STATE == 0b10: program.seek(LABELS[label])
        elif order == "JZ":
            if STATE == 0b00: program.seek(LABELS[label])


def dump_all():
    print("-" * 30)
    print("LABELS:")
    print(LABELS)
    print("REGISTER:")
    print(REGISTER)
    print("MEMORY:")
    print(MEMORY)
    print("STATE: ", STATE)
    print("-" * 30)

def main():
    global program
    program = open("testowy_program.txt", mode='r')
    # PREPROCESSING ETYKIET SKOKU
    while True:
        location = program.tell()
        line = program.readline()
        if match('^[A-Z_]+$', line):
            LABELS[sub('\n','',line)] = location
        if line == "": break
    # WYZEROWANIE POZYCJI WSKAŹNIKA STRUMIENIA
    program.seek(0)
    # GŁÓWNA PĘTLA
    while True:
        line = program.readline()
        print(line)
        interpret(line)
        if line == "": break
    dump_all()
    program.close()
main()