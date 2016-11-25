
import tkinter as tk
from TerminalClass import PythonTerminal
from tkinter import ttk
import time
from tkinter import messagebox
from tkinter import filedialog
from pygments import lex
from pygments.lexers import PythonLexer


highlight_pattern = {"Token.Keyword":"orange","Token.Literal.String":"green","Token.Name.Builtin":"purple",
                    "Token.Literal.Number.Integer":"blue","Token.Literal.Number.Float":"blue","Token.Operator.Word":"orange",
                     "Token.Name.Builtin.Pseudo": "medium purple","Token.Keyword.Namespace":"orange",
                     "Token.Comment.Single":"red","Token.Name.Class":"blue"}

class CustomText(tk.Text):
    def __init__(self, master,highlight_pattern={}, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        for name,color in highlight_pattern.items():
            self.tag_configure(name, foreground=color)


        self.special_taglist = [name for name in highlight_pattern]


    def highlight(self):
        for tag in self.tag_names():
            if tag in self.special_taglist:
                self.tag_remove(tag, '1.0', 'end')

        self.mark_set("range_start", "1.0")
        data = self.get("1.0", "end-1c")
        for token, content in lex(data, PythonLexer(stripnl=False)):
            self.mark_set("range_end", "range_start + %dc" % len(content))
            self.tag_add(str(token), "range_start", "range_end")
            self.mark_set("range_start", "range_end")

    def highlight_pattern(self, pattern, tag, start="1.0", end="end",
                          regexp=False):
        '''Apply the given tag to all text that matches the given pattern

        If 'regexp' is set to True, pattern will be treated as a regular
        expression according to Tcl's regular expression syntax.
        '''

        start = self.index(start)
        end = self.index(end)
        self.mark_set("matchStart", start)
        self.mark_set("matchEnd", start)
        self.mark_set("searchLimit", end)

        count = tk.IntVar()
        while True:
            index = self.search(pattern, "matchEnd", "searchLimit",
                                count=count, regexp=regexp)
            if index == "": break
            if count.get() == 0: break  # degenerate pattern which matches zero-length strings
            self.mark_set("matchStart", index)
            self.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            self.tag_add(tag, "matchStart", "matchEnd")


class ReadOnlyText(tk.Text):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config(state=tk.DISABLED)

    def new_insert(self, index, string):
        self.config(state=tk.NORMAL)
        self.insert(index, string)
        self.config(state=tk.DISABLED)

    def new_delete(self, index1, index2):
        self.config(state=tk.NORMAL)
        self.delete(index1, index2)
        self.config(state=tk.DISABLED)

    def clear(self):
        self.config(state=tk.NORMAL)
        self.delete("1.0", tk.END)
        self.config(state=tk.DISABLED)


class TerminalFrame(tk.Toplevel):
    def __init__(self, master, shared_vars):
        super().__init__(master)
        self.geometry('{}x{}'.format(1300, 800))

        self.shared_vars = shared_vars
        self.script_field_width = 30
        self.output_field_width = 30
        self.command_line_history = []
        self.current_history_pos = 0
        self.PyTerm = PythonTerminal(shared_vars)

        self.start_code = "import matplotlib.pyplot as plt\nimport numpy as np"
        self.PyTerm.run_code(self.start_code)
        mini_command_line_frame = tk.Frame(self)
        mini_command_line_frame.pack(side=tk.BOTTOM, anchor='w', fill='x')
        command_line_label = tk.Label(mini_command_line_frame, text='>>')
        command_line_label.pack(side=tk.LEFT, anchor='w', pady=5, padx=5)
        self.command_line = ttk.Entry(mini_command_line_frame, width=70)
        self.command_line.pack(side=tk.LEFT, anchor='w', pady=5, padx=5)
        self.command_line.bind('<Return>', self.run_command_line)
        self.command_line.bind('<Up>', self.up_down_command_line)
        self.command_line.bind('<Down>', self.up_down_command_line)

        self.script_field = CustomText(self,highlight_pattern=highlight_pattern, height=30, width=self.script_field_width)
        self.script_field.pack(side=tk.LEFT, fill="both", expand=True)
        self.script_field_scollbar = ttk.Scrollbar(self)
        self.script_field_scollbar.config(command=self.script_field.yview)
        self.script_field_scollbar.pack(side=tk.LEFT, fill="y", padx=5)
        self.script_field.config(yscrollcommand=self.script_field_scollbar.set)
        self.script_field.bind('<F5>', self.run_script_field)

        def tab(arg):
            self.script_field.insert(tk.INSERT, " " * 4)
            return 'break'

        self.script_field.bind("<Tab>", tab)

        self.output_field = ReadOnlyText(self, height=30, width=self.output_field_width)
        self.output_field.pack(side=tk.LEFT, fill="both", expand=True)
        self.output_field_scollbar = ttk.Scrollbar(self)
        self.output_field_scollbar.config(command=self.output_field.yview)
        self.output_field_scollbar.pack(side=tk.LEFT, fill="y", padx=5)
        self.output_field.config(yscrollcommand=self.output_field_scollbar.set)
        self.output_field.tag_configure("error", foreground='red')

        def restart_interpreter():
            self.PyTerm.restart_interpreter()
            self.PyTerm.run_code(self.start_code)

        self.clear_interpreter_button = ttk.Button(mini_command_line_frame, text='Restart interpreter',
                                                   command=restart_interpreter, takefocus=False)
        self.clear_interpreter_button.pack(side=tk.RIGHT, anchor='e', pady=5, padx=5)

        self.clear_output_field_button = ttk.Button(mini_command_line_frame, text='Lösche Output',
                                                    command=self.output_field.clear, takefocus=False)
        self.clear_output_field_button.pack(side=tk.RIGHT, anchor='e', pady=5, padx=5)

        self.print_welcome()

        self.menubar = tk.Menu(self, tearoff=0)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.filemenu.add_command(label="New", command=lambda: self.script_field.delete('1.0', tk.END),
                                  accelerator="Strq+shift+n")
        self.filemenu.add_command(label="Load", command=self.load_script_from_file, accelerator="Strq+shift+l")
        self.filemenu.add_command(label="Save", command=self.save_script_to_file, accelerator="Strq+shift+s")
        self.config(menu=self.menubar)
        self.bind_all('<Control-L>', lambda event: self.load_script_from_file())
        self.bind_all('<Control-S>', lambda event: self.save_script_to_file())
        self.bind_all('<Control-N>', lambda event: self.script_field.delete('1.0', tk.END))

        self.after(100, self.update_highlighting)

    def update_highlighting(self):

        self.script_field.highlight()

        self.after(100, self.update_highlighting)
        # self.script_field.highlight_pattern('return |for |def |if |else:|elif |while |class |True |False|import | in |','keywords',regexp=True)
        # self.script_field.highlight_pattern('range\(|print\(','builtin',regexp=True)
        # self.script_field.highlight_pattern(r'"(.*?)"','string',regexp=True)
        # self.script_field.highlight_pattern(r"'(.*?)'", 'string', regexp=True)

    def run_command_line(self, event):
        code = self.command_line.get()
        self.command_line_history.append(code)
        self.current_history_pos = 0
        result = self.PyTerm.run_code(code)

        self.command_line.delete(0, tk.END)
        self.print_output(result)

    def run_script_field(self, event):
        code = self.script_field.get("1.0", tk.END)
        stime = time.time()
        result = self.PyTerm.run_code(code)
        etime = time.time()
        self.print_output(result, run_time=etime - stime)

    def print_output(self, result, run_time=None):
        if run_time is not None:
            self.output_field.new_insert(tk.END, '\n--- Code was run in {:1.4f} s ---\n'.format(run_time))
        self.output_field.new_insert(tk.END, result[0])
        if result[1]:
            st_index = self.output_field.index(tk.END)
            st_index = "{:1.1f}".format(float(st_index) - 1)
            self.output_field.new_insert(tk.END, result[1])
            end_index = self.output_field.index(tk.END)
            end_index = "{:1.1f}".format(float(end_index) - 1)
            self.output_field.mark_set("errorStart", st_index)
            self.output_field.mark_set("errorEnd", end_index)
            self.output_field.tag_add('error', "errorStart", "errorEnd")
            self.output_field.tag_add('error', "errorStart", "errorEnd")

        self.output_field.see(tk.END)

    def save_script_to_file(self):
        save_filename = filedialog.asksaveasfilename(initialdir='./scripts',
                                                     filetypes=[('Python', '.py'), ('all files', '.*')],
                                                     parent=self)

        code = self.script_field.get("1.0", tk.END)
        if '.' not in save_filename:
            save_filename += '.py'
        with open(save_filename, 'w') as f:
            f.write(code)

    def load_script_from_file(self):
        load_filename = filedialog.askopenfilename(initialdir='./scripts',
                                                   filetypes=[('Python', '.py'), ('all files', '.*')],
                                                   parent=self)
        if not load_filename:
            return
        if '.' not in load_filename:
            load_filename += '.py'

        try:
            with open(load_filename, 'r') as f:
                code = f.read()
            self.script_field.delete('1.0', tk.END)
            self.script_field.insert('1.0', code)
        except Exception as ex1:
            messagebox.showerror('Fehler beim Laden', 'Laden ist mit Fehler ' + repr(ex1) + ' fehlgeschlagen',
                                 parent=self)

    def print_welcome(self):
        message_start = """Willkommen zum interaktiven Terminal
Sie koennen mit der Skriptsprache Python selbst ihr Konto analysieren
Folgende Variablen sind schon fuer Sie vorhanden:

np:             Numerische Bibliothek numpy
plt:            Graphische Bibliothek matplotlib
pd:             Tabellen-Bibliothek pandas"""

        if self.shared_vars:
            message_mid = """
Konto:          Ihr Konto als pandas Tabelle mit vollstaendigen Daten
Betrag:         Alle einzelnen Vorgaenge als numpy array
Kontostand:     Kontostand als numpy array
Buchungstag:    Der Buchungstag der Vorgaenge"""
        else:
            message_mid = """
Kontodaten waren nicht vorhanden und konnten nicht geladen werden.
Falls Sie diese benoetigen laden Sie bitte ihre Kontodaten ein und starten das Terminal neu
"""

        message_end = """
Beispiel:
plt.figure(figsize=(16,10)) # Erzeugt plot des Kontostandes
plt.plot(Buchungstag,Kontostand)
plt.show()

print(Kontostand.mean()) # Zeigt den mittleren Kontostand an

print(Konto.ix[0]) # Zeigt die erste Buchung des Kontos an

-------------------- Python --------------------

        """
        self.output_field.new_insert('1.0', message_start + message_mid + message_end)

    def up_down_command_line(self, event):
        if len(self.command_line_history) == 0:
            return
        if event.keysym == 'Up' and abs(self.current_history_pos - 1) <= len(self.command_line_history):
            self.current_history_pos += -1
        elif event.keysym == 'Down' and self.current_history_pos < 0:
            self.current_history_pos += 1

        self.command_line.delete(0, tk.END)
        if self.current_history_pos != 0:
            self.command_line.insert(0, self.command_line_history[self.current_history_pos])


if __name__ == "__main__":
    root = tk.Tk()
    TerminalFrame(root, None)
    root.mainloop()



