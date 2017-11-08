#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from re import match, sub
from tkinter import Tk, Text, Scrollbar, Menu, messagebox, filedialog, BooleanVar, Checkbutton, Label, Entry, StringVar, Frame, Button, END
import os, subprocess, json, string
# MEMORY START ADRESS AND WORD LENGTH IN BYTES
MEMORY_START = 1000
PROGRAM_START = 2000
WORD_LENGTH = 4
# ORDER RECOGNITION REGULAR EXPRESSIONS
ORDERS = ['^J[PNZ]?\s+.+', '^[A-Z_]+\s+D[CS]\s+([0-9]+\*)?INTEGER', '^(L[AR]?|ST)\s+[0-9]+\s*,\s*.+', '^[ASMDC]R?\s+[0-9]+\s*,\s*.+']
# COMPUTER STATE CONTAINERS
LABELS = dict()
REGISTER = [None] * 14 + [MEMORY_START, PROGRAM_START]
MEMORY = []
MEMORY_LABELS = dict()
STATE = 0b00
# <BY_LINE_MODE> VARIABLES
BY_LINE_MODE = False
CURRENT_LINE = 1.0
EDITOR_WIDTH = 51
# RESET COMPUTER STATE
def reset_state():
    global REGISTER, MEMORY, STATE, MEMORY_LABELS, LABELS
    LABELS = dict()
    REGISTER = [None] * 14 + [MEMORY_START, PROGRAM_START]
    MEMORY = []
    MEMORY_LABELS = dict()
    STATE = 0b00
# GET ALL JUMP LABELS FROM THE CODE
def preprocess_labels():
    # PREPROCESSING ETYKIET SKOKU
    global ORDERS, LABELS, CURRENT_LINE
    CURRENT_LINE = 0.0
    while True:
        CURRENT_LINE += 1.0
        location = program.tell()
        line = program.readline().lstrip()
        line = sub('\#.*', '', line)
        if match('^\s*$', line): continue
        is_label = True
        for regex in ORDERS:
            if match(regex, line): 
                is_label = False
                break
        if is_label: LABELS[line.split()[0]] = (location, CURRENT_LINE)
        if match('^\s*KONIEC\s*$', line): break
# SET PROGRAM STATE BITS (0b00 etc.)
def set_state(target):
    global STATE
    if REGISTER[int(target)] == 0: STATE = 0b00
    elif REGISTER[int(target)] > 0: STATE = 0b01
    elif REGISTER[int(target)] < 0: STATE = 0b10
    else: STATE = 0b11
# TRANSFORM FULL MEMORY CELL ADRESS INTO PYTHON LIST ONE
def get_short_adress(label):
    if match('^[A-Z_]+$', label): return (MEMORY_LABELS[label] - MEMORY_START) // WORD_LENGTH # ETYKIETA
    elif match('^[0-9]+$', label): return (int(label) - MEMORY_START) // WORD_LENGTH # ADRES
    elif match('^\-?[0-9]+\([0-9]+\)$', label): # REJESTR ADRESOWY
        label = sub('\)', '', label).split('(')
        delta = int(label[0])
        register = int(label[1])
        return get_short_adress(str(REGISTER[register] + delta))
# STORE FULL MEMORY CELL ADRESS IN LABEL DICTIONARY
def store_label(label):
    global MEMORY, MEMORY_LABELS, MEMORY_START
    MEMORY_LABELS[label] = len(MEMORY) * WORD_LENGTH + MEMORY_START
# CHECK IF THERE IS A LABEL AT A SPECIFIC MEMORY ADRESS
def get_label(input_adress):
    for label, adress in MEMORY_LABELS.items():
        if adress == input_adress: return label
    return ""
# INTERPRET A LINE OF CODE
def interpret(line):
    global STATE, REGISTER, MEMORY, LABELS, ORDERS, CURRENT_LINE
    # PUSTE LINIJKI
    if match("^\s*$", line): return
    # IGNORUJ ETYKIETY
    has_label = True
    line = line.lstrip().rstrip() # OBETNIJ Z BIAŁYCH ZNAKÓW
    for regex in ORDERS:
        if match(regex, line): 
            has_label = False
            break
    if has_label:
        line = line.split()
        line.pop(0)
        line = ' '.join(line).lstrip()
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
            line = sub('[\)\n]','', sub('\s*\(', '', line)).split()
            line[2] = line[2].split('*INTEGER')
            label = line[0]
            order = line[1]
            count = int(line[2][0])
            if order == "DC": # WARTOSCI OKRESLONE
                number = int(line[2][1])
                store_label(label)
                for _ in range(count): MEMORY.append(number)
            elif order == "DS": # ALOKACJA PAMIĘCI BEZ WARTOSCI
                store_label(label)
                for _ in range(count): MEMORY.append(None)
    elif match('^(L[AR]?|ST)\s+[0-9]+\s*,\s*.+', line): # OPERACJE ŁADOWANIA Z I DO PAMIĘCI
        line = sub(',', ' ', sub('\n','', line)).split()
        order = line[0]
        target = line[1]
        source = get_short_adress(line[2])
        if order == 'L': REGISTER[int(target)] = MEMORY[source]
        elif order == 'LA': REGISTER[int(target)] = source * WORD_LENGTH + MEMORY_START # ADRES OD POCZĄTKU W SŁOWACH
        elif order == 'LR': REGISTER[int(target)] = REGISTER[int(line[2])]
        elif order == 'ST': MEMORY[source] = REGISTER[int(target)]
    elif match('^[ASMDC]R?\s+[0-9]+\s*,\s*.+', line): # OPERACJE ARYTMETYCZNE I PORÓWNANIA
        line = sub(',', ' ', sub('\n','', line)).split()
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
        if order == "J":
            program.seek(LABELS[label][0])
            CURRENT_LINE = LABELS[label][1]
        elif order == "JP":
            if STATE == 0b01:
                program.seek(LABELS[label][0])
                CURRENT_LINE = LABELS[label][1]
        elif order == "JN":
            if STATE == 0b10:
                program.seek(LABELS[label][0])
                CURRENT_LINE = LABELS[label][1]
        elif order == "JZ":
            if STATE == 0b00:
                program.seek(LABELS[label][0])
                CURRENT_LINE = LABELS[label][1]
    else: #COULDN'T MATCH ANYTHING
        raise SyntaxError
# PRINT ALL INFORMATION TO THE OUTPUT TEXT FIELDS             
def dump_all():
    # DRUKOWANIE WARTOSCI SŁOWA STANU PROGRAMU ORAZ ZAWARTOSCI REJESTRÓW
    formated_state = bin(STATE).split('b')[1]
    if STATE <2: formated_state = '0' + formated_state
    registers_text = "STATE:\t" + formated_state +  "\nREGISTERS:\nINDEX\tVALUE\tTWO'S COMPLEMENT\n"
    for x in range(len(REGISTER)):
        registers_text = registers_text + str(x) + "\t" + str(REGISTER[x]) + "\t" + int_to_u2(REGISTER[x]) + "\n"
    registers.print_output(registers_text)
    # DRUKOWANIE ZAWARTOSCI PAMIĘCI
    memory_text = "MEMORY:\nADRESS\tVALUE:\tLABEL:\tTWO'S COMPLEMENT:\n"
    for x in range(len(MEMORY)):
        memory_text = memory_text + str(x * WORD_LENGTH + MEMORY_START) + "\t" + str(MEMORY[x]) + "\t" + get_label(x * WORD_LENGTH + MEMORY_START) + "\t" + int_to_u2(MEMORY[x]) +"\n"
    memory.print_output(memory_text)
# TRANSLATE DECIMAL TO TWO'S COMPLEMENT BINARY
def int_to_u2(integer):
    if integer == None: return ""
    binary = bin(integer % (1<< (WORD_LENGTH * 8))).split('b')[1]
    if integer >= 0:
        for i in range(8*WORD_LENGTH - len(binary)): binary= '0' + binary
    return binary
# EDITOR TEXTBOX CLASS (ALSO, MENU)
class Editor():
    def __init__(self, root):
        self.root = root        
        self.TITLE = "Pseudoassembler IDE"
        self.file_path = None
        self.set_title()
        
        frame = Frame(root)
        self.yscrollbar = Scrollbar(frame, orient="vertical")
        self.xscrollbar = Scrollbar(frame, orient="horizontal")
        self.editor = Text(frame, yscrollcommand=self.yscrollbar.set, xscrollcommand=self.xscrollbar.set, bg="white", cursor="xterm")
        self.editor.pack(side="top", fill="y", expand=1)
        self.editor.config(wrap = "none",
               undo = True,
               width = EDITOR_WIDTH)
        self.editor.focus() 
        frame.pack(side="left", fill="both", expand=0)

        # EXECUTE A FUNCTION INSTEAD OF CLOSING THE WINDOW
        root.protocol("WM_DELETE_WINDOW", self.file_quit) 

        # TOP LEVEL MENU
        self.menubar = Menu(root)
        # MENU ITEM FILE
        filemenu = Menu(self.menubar, tearoff=0) # teardown = 0 -> can't be separated from window
        filemenu.add_command(label="New", underline=1, command=self.file_new, accelerator="Ctrl+N")
        filemenu.add_command(label="Open...", underline=1, command=self.file_open, accelerator="Ctrl+O")
        filemenu.add_command(label="Save", underline=1, command=self.file_save, accelerator="Ctrl+S")
        filemenu.add_command(label="Save As...", underline=5, command=self.file_save_as, accelerator="Ctrl+Alt+S")
        filemenu.add_separator()
        filemenu.add_command(label="Exit", underline=2, command=self.file_quit, accelerator="Alt+F4")
        self.menubar.add_cascade(label="File", underline=0, menu=filemenu)        
        # DISPLAY THE MENU
        root.config(menu=self.menubar)
    
    def save_if_modified(self, event=None):
        if self.editor.edit_modified(): # modified
            response = messagebox.askyesnocancel("Save?", "This document has been modified. Do you want to save changes?") # yes = True, no = False, cancel = None
            if response: # yes/save
                result = self.file_save()
                if result == "saved": # saved
                    return True
                else: # save cancelled
                    return None
            else:
                return response # None = cancel/abort, False = no/discard
        else: # not modified
            return True
    
    def file_new(self, event=None):
        result = self.save_if_modified()
        if result != None: # None => Aborted or Save cancelled, False => Discarded, True = Saved or Not modified
            self.editor.delete(1.0, "end")
            self.editor.edit_modified(False)
            self.editor.edit_reset()
            self.file_path = None
            self.set_title()
            
    def file_open(self, event=None, filepath=None):
        result = self.save_if_modified()
        if result != None: # None => Aborted or Save cancelled, False => Discarded, True = Saved or Not modified
            if filepath == None:
                filepath = filedialog.askopenfilename()
            if filepath != None  and filepath != '':
                with open(filepath, encoding="utf-8") as f:
                    fileContents = f.read()# Get all the text from file.           
                # SET CURRENT TEXT TO FILE CONTENTS
                self.editor.delete(1.0, "end")
                self.editor.insert(1.0, fileContents)
                self.editor.edit_modified(False)
                self.file_path = filepath
                self.set_title()

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
        self.editor.bind("<Command-b>", run_code) # global?
# OUTPUT TEXTBOXES CLASS
class Output():
    def __init__(self, root, side, height = 20):
        self.root = root
        self.yscroll = Scrollbar(self.root, orient="vertical")
        self.xscroll = Scrollbar(self.root, orient="horizontal")
        self.field = Text(self.root, height = height, width = 60, yscrollcommand=self.yscroll.set, xscrollcommand=self.xscroll.set, cursor="arrow")
        self.field.config(state = "disabled", wrap="none")
        self.field.pack(side=side, fill="x", expand=1)
    def print_output(self, text):
        self.field.config(state = "normal")
        self.field.delete("1.0", END)
        self.field.insert("1.0", text)
        self.field.config(state = "disabled")
# HALT EXECUTION IF ERROR DETECTED
def call_error():
    global STATE, CURRENT_LINE, EDITOR_WIDTH, editor
    dump_all()
    STATE = 0b11 # SET STATE TO ERROR CODE
    # HIGHLIGHT THE WRONG LINE IN RED
    CURRENT_LINE -= 1
    editor.editor.tag_add("error_line", str(CURRENT_LINE), str(CURRENT_LINE + EDITOR_WIDTH/100))
    editor.editor.tag_config("error_line", background="red", foreground="white")
    editor.editor.tag_remove("error_line", "1.0", str(CURRENT_LINE))
    editor.editor.tag_remove("error_line", str(CURRENT_LINE + EDITOR_WIDTH/100), END)
# RUN ALL OF THE CODE AT ONCE
def run_code(event=None):
    global STATE, CURRENT_LINE, program
    editor.save_if_modified()
    program = open(editor.file_path, mode='r')
    reset_state()
    editor.editor.tag_remove("error_line", "1.0", END) # CLEAR ERROR HIGHLIGHT
    preprocess_labels()
    # WYZEROWANIE POZYCJI WSKAŹNIKA STRUMIENIA
    program.seek(0)
    CURRENT_LINE = 1.0
    # GŁÓWNA PĘTLA
    while True:
        line = program.readline()
        # USUWANIE KOMENTARZY
        line = sub('\#.+', '', line)
        if match('^\s*$', line): continue
        if match('^\s*KONIEC\s*$', line): break
        try: 
            CURRENT_LINE += 1
            interpret(line)
        except:
            call_error()
            program.close()
            return
    dump_all()
    program.close()
# TOGGLE <RUN_BY_LINE> MODE
def run_by_line(event=None):
    global BY_LINE_MODE, CURRENT_LINE, program
    if not BY_LINE_MODE:
        BY_LINE_MODE = True
        editor.editor.tag_remove("error_line", "1.0", END) # CLEAR ERROR HIGHLIGHT
        run_by_line_button.config(text="EXIT BY LINE MODE")
        next_line_button.config(state="normal")
        run_button.config(state="disabled")
        # SET STATE
        editor.save_if_modified()
        program = open(editor.file_path, mode='r')
        reset_state()
        preprocess_labels()
        program.seek(0)
        CURRENT_LINE = 1.0
        next_line()
    else:
        BY_LINE_MODE = False
        CURRENT_LINE = 1.0
        run_by_line_button.config(text="RUN BY LINE")
        next_line_button.config(state="disabled")
        run_button.config(state="normal")
        reset_state()
        editor.editor.tag_remove("current_line", "1.0", END) # CLEAR NORMAL HIGHLIGHTING
# PROCESS NEXT LINE IN <RUN_BY_LINE> MODE
def next_line(event=None):
    global CURRENT_LINE, BY_LINE_MODE, STATE, program
    # HIGHLIGHT CURRENT LINE AND REMOVE HIGHLIGHT FROM ALL OTHER
    editor.editor.tag_add("current_line", str(CURRENT_LINE), str(CURRENT_LINE + EDITOR_WIDTH/100))
    editor.editor.tag_config("current_line", background="black", foreground="white")
    editor.editor.tag_remove("current_line", "1.0", str(CURRENT_LINE))
    editor.editor.tag_remove("current_line", str(CURRENT_LINE + EDITOR_WIDTH/100), END)
    # PROCESS LINE
    CURRENT_LINE += 1.0
    line = program.readline()
    line = sub('\#.+', '', line)
    if match('^\s*KONIEC\s*$', line):
        run_by_line()
        return
    try: interpret(line)
    except:
        call_error()
        run_by_line()
        return
    dump_all()
# MAIN PROGRAM FUNCTION
if __name__ == "__main__":
    # INITIALIZE WINDOW
    global root
    root = Tk()
    # BUTTONS
    buttons = Frame(root)
    run_button = Button(buttons, text ="RUN CODE", command = run_code)
    run_by_line_button = Button(buttons, text="RUN BY LINE", command = run_by_line)
    next_line_button = Button(buttons, text ="NEXT LINE", command = next_line, state="disabled")
    run_button.pack(side="left")
    run_by_line_button.pack(side="left")
    next_line_button.pack(side="left")
    buttons.pack(side="top", fill="x")
    # TEXT FIELDS
    editor = Editor(root)
    editor.main()
    registers = Output(root, "top")
    memory = Output(root, "bottom", 20)
    # MAIN PROGRAM LOOP
    dump_all()
    root.mainloop()