from re import match, sub

MEMORY_START = 1000
WORD_LENGTH = 4

ORDERS = ['^J[PNZ]?\s+.+', '^[A-Z_]+\s+D[CS]\s+([0-9]+\*)?INTEGER', '^(L[AR]?|ST)\s+[0-9]+\s*,\s*.+', '^[ASMDC]R?\s+[0-9]+\s*,\s*.+']
LABELS = dict()
REGISTER = [None] * 14 + [MEMORY_START,0]
MEMORY = []
MEMORY_LABELS = dict()
STATE = 0

def set_state(target):
    global STATE
    if REGISTER[int(target)] == 0: STATE = 0b00
    elif REGISTER[int(target)] > 0: STATE = 0b01
    elif REGISTER[int(target)] < 0: STATE = 0b10
    else: STATE = 0b11

def get_short_adress(label):
    if match('^[A-Z_]+$', label): return (MEMORY_LABELS[label] - MEMORY_START) // WORD_LENGTH # ETYKIETA
    elif match('^[0-9]+$', label): return (int(label) - MEMORY_START) // WORD_LENGTH # ADRES
    elif match('^[0-9]+\([0-9]+\)$', label): # REJESTR ADRESOWY
        label = sub('\)', '', label).split('(')
        delta = int(label[0])
        register = int(label[1])
        return get_short_adress(str(REGISTER[register] + delta))

def store_label(label):
    global MEMORY, MEMORY_LABELS, MEMORY_START
    MEMORY_LABELS[label] = len(MEMORY) * WORD_LENGTH + MEMORY_START

def get_label(input_adress):
    for label, adress in MEMORY_LABELS.items():
        if adress == input_adress: return adress

def interpret(line):
    global STATE, REGISTER, MEMORY, LABELS, ORDERS
    # IGNORUJ ETYKIETY
    has_label = True
    line = line.lstrip().rstrip() # OBETNIJ Z BIAŁYCH ZNAKÓW
    print("Line before: ", line)
    for regex in ORDERS:
        if match(regex, line): 
            has_label = False
            break
    if has_label:
        line = line.split()
        line.pop(0)
        line = ' '.join(line).lstrip()
        print("Line after: ", line)
    # WŁASCIWE INSTRUKCJE
    if match('^[A-Z_]+\s+D[CS]\s+([0-9]+\*)?INTEGER', line): # DYREKTYWY DEKLARACJI ZMIENNYCH
        if match('^[A-Z_]+\s+D[CS]\s+INTEGER', line): # POJEDYŃCZE ZMIENNE
            line = sub('[\(\)\n]',' ', line).split()
            label = line[0]
            order = line[1]   
            if order == "DC":
                value = int(line[3])
                store_label(label)
                MEMORY.append(value)
            elif order == "DS":
                store_label(label)
                MEMORY.append(None)
        elif match('^[A-Z_]+\s+D[CS]\s+[0-9]+\*INTEGER', line): #  TABLICE ZMIENNYCH
            line = sub('[\(\)\n]','', line).split()
            line[2] = line[2].split('*')
            label = line[0]
            order = line[1]
            count = int(line[2][0])
            if order == "DC": # WARTOSCI OKRESLONE
                number = int(line[3])
                store_label(label)
                for _ in range(count): MEMORY.append(number)
            elif order == "DS": # ALOKACJA PAMIĘCI BEZ WARTOSCI
                store_label(label)
                for _ in range(count): MEMORY.append(None)

    elif match('^(L[AR]?|ST)\s+[0-9]+,\s+.+', line): # OPERACJE ŁADOWANIA Z I DO PAMIĘCI
        line = sub('[,\n]','', line).split()
        order = line[0]
        target = line[1]
        source = get_short_adress(line[2])
        if order == 'L': REGISTER[int(target)] = MEMORY[source]
        elif order == 'LA': REGISTER[int(target)] = source * WORD_LENGTH + MEMORY_START # ADRES OD POCZĄTKU W SŁOWACH
        elif order == 'LR': REGISTER[int(target)] = REGISTER[int(line[2])]
        elif order == 'ST': MEMORY[source] = REGISTER[int(target)]
    elif match('^[ASMDC]R?\s+[0-9]+,\s+.+', line): # OPERACJE ARYTMETYCZNE I PORÓWNANIA
        line = sub('[,\n]','', line).split()
        order = line[0]
        target = line[1]
        source = line[2]
        # SPRAWDZANIE CZY OPERACJA TYPU REJESTR - REJESTR
        if match('.R', order): source = REGISTER[int(source)]
        else: source = MEMORY[get_short_adress(line[2])]
        # ADD, SUBTRACT, MULTIPLY, DIVIDE
        if match('^A', order): REGISTER[int(target)] += source
        elif match('^S', order): REGISTER[int(target)] -= source
        elif match('^M', order): REGISTER[int(target)] *= source
        elif match('^D', order): REGISTER[int(target)] //= source
        set_state(target)
        # COMPARE
        if match('^C', order):
            target = REGISTER[int(target)]
            if target == source: STATE = 0b00
            elif target > source: STATE = 0b10
            elif target < source: STATE = 0b01
            else: STATE = 0b11
    elif match('^J[PNZ]?\s+[A-Z_]+', line): # OPERACJE SKOKU
        line = line.split()
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
    print("MEMORY LABELS:")
    print(MEMORY_LABELS)
    print("MEMORY:")
    print(MEMORY)
    print("STATE: ", STATE)
    print("-" * 30)

def main():
    global program
    program = open("nwd.txt", mode='r')
    # PREPROCESSING ETYKIET SKOKU
    while True:
        location = program.tell()
        line = program.readline().lstrip()
        line = sub('\#.*', '', line)
        if match('^\s*$', line): continue
        is_label = True
        for regex in ORDERS:
            if match(regex, line): 
                is_label = False
                break
        print(line, is_label)
        if is_label: LABELS[line.split()[0]] = location
        if match('^\s*KONIEC\s*$', line): break
    # WYZEROWANIE POZYCJI WSKAŹNIKA STRUMIENIA
    program.seek(0)
    # GŁÓWNA PĘTLA
    while True:
        line = program.readline()
        # USUWANIE KOMENTARZY
        line = sub('\#.+', '', line)
        if match('^\s*$', line): continue
        if match('^\s*KONIEC\s*$', line): break
        print(line)
        interpret(line)
        dump_all()
    dump_all()
    program.close()

main()