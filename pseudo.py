#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from re import match, sub
from tkinter import Tk, Text, Scrollbar, Menu, messagebox, filedialog, BooleanVar, Checkbutton, Label, Entry, StringVar, Grid, Frame, Button, END
import os, subprocess, json, string

MEMORY_START = 1000
WORD_LENGTH = 4

ORDERS = ['^J[PNZ]?\s+.+', '^[A-Z_]+\s+D[CS]\s+([0-9]+\*)?INTEGER', '^(L[AR]?|ST)\s+[0-9]+\s*,\s*.+', '^[ASMDC]R?\s+[0-9]+\s*,\s*.+']
LABELS = dict()
REGISTER = [None] * 14 + [MEMORY_START,0]
MEMORY = []
MEMORY_LABELS = dict()
STATE = 0b00

BY_LINE_MODE = False
CURRENT_LINE = 1.0

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
        if adress == input_adress: return label
    return ""

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
            elif target > source: STATE = 0b01
            elif target < source: STATE = 0b10
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
    # DRUKOWANIE ZAWARTOSCI REJESTRÓW
    registers_text = "REGISTERS:\n"
    for x in range(len(REGISTER)):
        registers_text = registers_text + str(x) + ":" + str(REGISTER[x]) + "\n"
    registers.print_output(registers_text)
    # DRUKOWANIE ZAWARTOSCI PAMIĘCI
    memory_text = "MEMORY:\n"
    for x in range(len(MEMORY)):
        memory_text = memory_text + str(x * WORD_LENGTH + MEMORY_START) + ":" + str(MEMORY[x]) + "  <" + get_label(x * WORD_LENGTH + MEMORY_START) + ">\n"
    memory.print_output(memory_text)

class Editor():
    def __init__(self, root):
        self.root = root        
        self.TITLE = "Pseudoassembler IDE"
        self.file_path = None
        self.set_title()
        
        frame = Frame(root)
        self.yscrollbar = Scrollbar(frame, orient="vertical")
        self.editor = Text(frame, yscrollcommand=self.yscrollbar.set)
        self.editor.pack(side="left", fill="y", expand=1)
        self.editor.config( wrap = "word", # use word wrapping
               undo = True, # Tk 8.4 
               width = 80 )        
        self.editor.focus()     
        frame.pack(side="left", fill="y", expand=1)

        #instead of closing the window, execute a function
        root.protocol("WM_DELETE_WINDOW", self.file_quit) 

        #create a top level menu
        self.menubar = Menu(root)
        #Menu item File
        filemenu = Menu(self.menubar, tearoff=0)# tearoff = 0 => can't be seperated from window
        filemenu.add_command(label="New", underline=1, command=self.file_new, accelerator="Ctrl+N")
        filemenu.add_command(label="Open...", underline=1, command=self.file_open, accelerator="Ctrl+O")
        filemenu.add_command(label="Save", underline=1, command=self.file_save, accelerator="Ctrl+S")
        filemenu.add_command(label="Save As...", underline=5, command=self.file_save_as, accelerator="Ctrl+Alt+S")
        filemenu.add_separator()
        filemenu.add_command(label="Exit", underline=2, command=self.file_quit, accelerator="Alt+F4")
        self.menubar.add_cascade(label="File", underline=0, menu=filemenu)        
        # display the menu
        root.config(menu=self.menubar)
    def save_if_modified(self, event=None):
        if self.editor.edit_modified(): #modified
            response = messagebox.askyesnocancel("Save?", "This document has been modified. Do you want to save changes?") #yes = True, no = False, cancel = None
            if response: #yes/save
                result = self.file_save()
                if result == "saved": #saved
                    return True
                else: #save cancelled
                    return None
            else:
                return response #None = cancel/abort, False = no/discard
        else: #not modified
            return True
    
    def file_new(self, event=None):
        result = self.save_if_modified()
        if result != None: #None => Aborted or Save cancelled, False => Discarded, True = Saved or Not modified
            self.editor.delete(1.0, "end")
            self.editor.edit_modified(False)
            self.editor.edit_reset()
            self.file_path = None
            self.set_title()
            

    def file_open(self, event=None, filepath=None):
        result = self.save_if_modified()
        if result != None: #None => Aborted or Save cancelled, False => Discarded, True = Saved or Not modified
            if filepath == None:
                filepath = filedialog.askopenfilename()
            if filepath != None  and filepath != '':
                with open(filepath, encoding="utf-8") as f:
                    fileContents = f.read()# Get all the text from file.           
                # Set current text to file contents
                self.editor.delete(1.0, "end")
                self.editor.insert(1.0, fileContents)
                self.editor.edit_modified(False)
                self.file_path = filepath

    def file_save(self, event=None):
        if self.file_path == None:
            result = self.file_save_as()
        else:
            result = self.file_save_as(filepath=self.file_path)
        return result

    def file_save_as(self, event=None, filepath=None):
        if filepath == None:
            filepath = filedialog.asksaveasfilename(filetypes=(('Text files', '*.txt'), ('Python files', '*.py *.pyw'), ('All files', '*.*'))) #defaultextension='.txt'
        try:
            with open(filepath, 'wb') as f:
                text = self.editor.get(1.0, "end-1c")
                f.write(bytes(text, 'UTF-8'))
                self.editor.edit_modified(False)
                self.file_path = filepath
                self.set_title()
                return "saved"
        except FileNotFoundError:
            print('FileNotFoundError')
            return "cancelled"

    def file_quit(self, event=None):
        result = self.save_if_modified()
        if result != None: #None => Aborted or Save cancelled, False => Discarded, True = Saved or Not modified
            self.root.destroy() #sys.exit(0)

    def set_title(self, event=None):
        if self.file_path != None:
            title = os.path.basename(self.file_path)
        else:
            title = "Untitled"
        self.root.title(title + " - " + self.TITLE)
        
    def undo(self, event=None):
        self.editor.edit_undo()
        
    def redo(self, event=None):
        self.editor.edit_redo()   
            
    def main(self, event=None):          
        self.editor.bind("<Command-o>", self.file_open)
        self.editor.bind("<Command-O>", self.file_open)
        self.editor.bind("<Command-S>", self.file_save)
        self.editor.bind("<Command-s>", self.file_save)
        self.editor.bind("<Command-y>", self.redo)
        self.editor.bind("<Command-Y>", self.redo)
        self.editor.bind("<Command-Z>", self.undo)
        self.editor.bind("<Command-z>", self.undo)
        self.editor.bind("<Command-b>", run_code)
class Output():
    def __init__(self, root, side, height = 20):
        self.root = root
        self.yscroll = Scrollbar(self.root, orient="vertical")
        self.field = Text(self.root, height = height, width = 50, yscrollcommand=self.yscroll.set)
        self.field.config(state = "disabled")
        self.field.pack(side=side)
    def print_output(self, text):
        self.field.config(state = "normal")
        self.field.delete("1.0", END)
        self.field.insert("1.0", text)
        self.field.config(state = "disabled")

def run_code(event=None):
    global program
    editor.save_if_modified()
    program = open(editor.file_path, mode='r')
    # ZEROWANIE STANU KOMPUTERA
    global REGISTER, MEMORY, STATE, MEMORY_LABELS, LABELS
    LABELS = dict()
    REGISTER = [None] * 14 + [MEMORY_START,0]
    MEMORY = []
    MEMORY_LABELS = dict()
    STATE = 0b00
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
    program.close()

def run_by_line(event=None):
    global BY_LINE_MODE, CURRENT_LINE
    if not BY_LINE_MODE:
        BY_LINE_MODE = True
        run_by_line_button.config(text="EXIT BY LINE MODE")
        next_line_button.config(state="normal")
        next_line()
    else:
        BY_LINE_MODE = False
        CURRENT_LINE = 1.0
        run_by_line_button.config(text="RUN BY LINE")
        next_line_button.config(state="disabled")


def next_line(event=None):
    # HIGHLIGHT CURRENT LINE AND REMOVE HIGHLIGHT FROM THE PREVIOUS ONE
    global CURRENT_LINE
    if CURRENT_LINE > 1:
        editor.editor.tag_add("previous_line", str(CURRENT_LINE-1), str(CURRENT_LINE-1 + 0.71))
        editor.editor.tag_config("previous_line", background="white", foreground="black")
    editor.editor.tag_add("current_line", str(CURRENT_LINE), str(CURRENT_LINE + 0.71))
    editor.editor.tag_config("current_line", background="black", foreground="white")
    CURRENT_LINE += 1.0

if __name__ == "__main__":
    # INICJALIZACJA OKNA
    global root
    root = Tk("IDE Window")
    # PRZYCISKI
    def donothing():
        pass 
    buttons = Frame(root)
    run_button = Button(buttons, text ="RUN CODE", command = run_code)
    run_by_line_button = Button(buttons, text="RUN BY LINE", command = run_by_line)
    next_line_button = Button(buttons, text ="NEXT LINE", command = next_line, state="disabled")
    run_button.pack(side="left")
    run_by_line_button.pack(side="left")
    next_line_button.pack(side="left")
    buttons.pack(side="top", fill="x")
    # POLA TEKSTOWE
    editor = Editor(root)
    editor.main()
    registers = Output(root, "top")
    memory = Output(root, "bottom")
    registers.print_output("REGISTERS:")
    memory.print_output("MEMORY_DUMP:")
    # GŁÓWNA PĘTLA PROGRAMU
    dump_all()
    root.mainloop()