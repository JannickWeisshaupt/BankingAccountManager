from tkinter import ttk
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import numpy as np
import pandas as pd

import datetime as dt
import ctypes
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib import gridspec
##plt.rc('font',**{'family':'serif','serif':['Palatino']})
##plt.rc('text', usetex=True)
font = {'family' : 'serif',
        'size'   : 18}

plt.rc('font', **font)

import logging
import threading
import queue

from SparkasseDataframe import SparkasseDataframe

sd = SparkasseDataframe()


logging.basicConfig(level=logging.DEBUG, filename="logfiles/logfile_"+ str(dt.datetime.date(dt.datetime.today()))+ ".log", filemode="a+",format="%(asctime)-15s %(levelname)-8s %(message)s")
logging.info('Program started')

myappid = u'Konto-Verwaltung' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

q1 = queue.Queue()


class DataFrame(tk.Frame):

    def __init__(self,master):
        super().__init__(master)

        width_value = 40

        self.header = ttk.Label(self,text='Vorgangsinformation',justify=tk.CENTER,font=("Helvetica", 20))
        self.header.grid(row=0,column=0,columnspan=2,pady=10)

        self.begL = ttk.Label(self,text='Begünstigter/Zahlungspflichtiger:',justify=tk.LEFT,anchor=tk.W)
        self.begL.grid(row=1,column=0,pady=3,sticky='w')
        self.begL_value = ttk.Label(self,text='',justify=tk.LEFT,width=width_value,anchor=tk.W)
        self.begL_value.grid(row=1,column=1,pady=3,sticky='w')

        self.betragL = ttk.Label(self,text='Betrag:',justify=tk.LEFT,anchor=tk.W)
        self.betragL.grid(row=2,column=0,pady=3,sticky='w')
        self.betragL_value = ttk.Label(self,text='',justify=tk.LEFT,width=width_value,anchor=tk.W)
        self.betragL_value.grid(row=2,column=1,pady=3,sticky='w')

        self.standL = ttk.Label(self,text='Kontostand:',justify=tk.LEFT,anchor=tk.W)
        self.standL.grid(row=3,column=0,pady=3,sticky='w')
        self.standL_value = ttk.Label(self,text='',justify=tk.LEFT,width=width_value,anchor=tk.W)
        self.standL_value.grid(row=3,column=1,pady=3,sticky='w')

        self.verwL = ttk.Label(self,text='Verwendungszweck:',justify=tk.LEFT,anchor=tk.W)
        self.verwL.grid(row=4,column=0,pady=3,sticky='w')
        self.verwL_value = ttk.Label(self,text='',justify=tk.LEFT,width=width_value,anchor=tk.W)
        self.verwL_value.grid(row=4,column=1,pady=3,sticky='w')
        self.verwL2_value = ttk.Label(self,text='',justify=tk.LEFT,width=70,anchor=tk.W)
        self.verwL2_value.grid(row=5,column=0,pady=3,columnspan=2,sticky='w')

        self.ktnrL = ttk.Label(self,text='Kontonummer:',justify=tk.LEFT,anchor=tk.W)
        self.ktnrL.grid(row=6,column=0,pady=3,sticky='w')
        self.ktnrL_value = ttk.Label(self,text='',justify=tk.LEFT,width=width_value,anchor=tk.W)
        self.ktnrL_value.grid(row=6,column=1,pady=3,sticky='w')

        self.blzL = ttk.Label(self,text='BLZ:',justify=tk.LEFT,anchor=tk.W)
        self.blzL.grid(row=7,column=0,pady=3,sticky='w')
        self.blzL_value = ttk.Label(self,text='',justify=tk.LEFT,width=width_value,anchor=tk.W)
        self.blzL_value.grid(row=7,column=1,pady=3,sticky='w')

        self.tagL = ttk.Label(self,text='Buchungstag:',justify=tk.LEFT,anchor=tk.W)
        self.tagL.grid(row=8,column=0,pady=3,sticky='w')
        self.tagL_value = ttk.Label(self,text='',justify=tk.LEFT,width=width_value,anchor=tk.W)
        self.tagL_value.grid(row=8,column=1,pady=3,sticky='w')

    def update(self):
        beg = sd.longterm_data.at[app.chosen_data,'Beguenstigter/Zahlungspflichtiger']
        kontostand = sd.longterm_data.at[app.chosen_data,'SumBetrag']
        betrag = sd.longterm_data.at[app.chosen_data,'Betrag']
        buchungstag = sd.longterm_data.at[app.chosen_data,'Buchungstag']
        verwendungszweck = str(sd.longterm_data.at[app.chosen_data,'Verwendungszweck'])
        kontonummer = sd.longterm_data.at[app.chosen_data,'Kontonummer']
        waehrung = sd.longterm_data.at[app.chosen_data,'Waehrung']
        blz = sd.longterm_data.at[app.chosen_data,'BLZ']

        

        if type(waehrung) is float:
            waehrung = 'EUR'
            blz = ''
            kontonummer = ''
            beg = ''
            
        if betrag > 0:
            self.begL.config(text='Zahlungspflichtiger:')
        else:
            self.begL.config(text='Begünstigter:')

        self.begL_value.config(text = beg )
        self.betragL_value.config(text = "{:1.2f}".format(betrag) +' '+ waehrung )
        self.standL_value.config(text = "{:1.2f}".format(kontostand) +' '+ 'EUR' )

        self.verwL_value.config(text = verwendungszweck[:35])
        self.verwL2_value.config(text = verwendungszweck[35:])
        self.ktnrL_value.config(text = kontonummer )
        self.blzL_value.config(text = blz )
        self.tagL_value.config(text = dt.datetime.date(buchungstag))

class EmbeddedFigure:
    def __init__(self):
        plt.ion()
        self.f = plt.Figure(figsize=(10,8))
        gs = gridspec.GridSpec(1, 1, height_ratios=[1])
        self.subplot1 = self.f.add_subplot(gs[0])
##        self.subplot2=  self.f.add_subplot(gs[1])
##        self.subplot2.text(0.3, 0.25, 'Program written by\nJannick Weisshaupt', size=25)
        self.f.patch.set_facecolor([240/255,240/255,237/255])
##        self.f.tight_layout()
        self.subplot1.grid('on')
        self.subplot1.set_ylabel('Kontostand')
        self.point_data = None
        self.single_point_plot = None
        
    def update(self):
        self.single_point_plot = None
        if sd.longterm_data is None:
            return

        self.subplot1.clear()
        plot1 = sd.longterm_data.plot(x='Buchungstag',y='SumBetrag',grid=True,linewidth=3,ax=self.subplot1,color=[255/255, 19/255, 0],legend=False, drawstyle='steps-post')
        plot2 = sd.longterm_data.plot(x='Buchungstag',y='SumBetrag',grid=True,marker='o',linewidth=0,ax=self.subplot1,color=[255/255, 19/255, 0],legend=False)


##            i_rub = app_chosen_index
##            single_point = self.subplot1.plot(self.point_data_unconv[i_rub,0],self.point_data_unconv[i_rub,1],'bo')

        lines =     self.subplot1.get_lines()
        xdata = lines[0].get_data()[0]
        ydata = lines[0].get_data()[1]

##        xdata_conv = (xdata-dt.datetime(1,1,1)).total_seconds()/60/60/24

        xdata_conv = np.array([(t-dt.datetime(1,1,1)).total_seconds()/60/60/24+1 for t in xdata ])
        self.point_data = np.zeros((len(ydata),2))
        self.point_data[:,0] = xdata_conv
        self.point_data[:,1] = ydata
        

        self.subplot1.set_ylabel('Kontostand')
##        self.f.tight_layout()
        self.f.subplots_adjust(left = 0.15,right=1)
        self.f.tight_layout()
        plt.pause(0.001)
        self.canvas.draw()

    def nearest_point(self,xp,yp):

        ylim = self.subplot1.get_ylim()
        xlim = self.subplot1.get_xlim()
        resc_fac = (ylim[1]-ylim[0])/(xlim[1]-xlim[0])
        
        resc_data = np.zeros(self.point_data.shape)
        resc_data[:,1] = self.point_data[:,1]/resc_fac
        resc_data[:,0] = self.point_data[:,0]

        index = np.argmin( np.linalg.norm(resc_data-np.array([xp,yp/resc_fac])     ,axis=1) )
##        index = np.argmin( np.abs(self.point_data[:,0]-xp)) 
        self.last_selected_point = self.point_data[index,:]
        app.chosen_data = index
##        print(sd.longterm_data.ix[index])
        return index

    def add_selected(self):
  
        if app.chosen_data is None:
            return
        
        if self.single_point_plot is not None:
            self.single_point_plot.remove()
            
        self.single_point_plot, = self.subplot1.plot(self.last_selected_point[0],self.last_selected_point[1],'o',color=[7/255, 85/255, 240/255],ms=7)
        plt.pause(0.001)
        self.canvas.draw()

    def reset(self):
        self.subplot1.clear()
        plt.pause(0.001)
        self.canvas.draw()


EF1 = EmbeddedFigure()






class Application(tk.Frame):
    
    def update_status(self):
        root.after(1, lambda: self.update_status())
        if not q1.empty():
            q_command = q1.get()
            if q_command == 'Update Plot':
                EF1.update()
            elif q_command == 'Update Dataframe':
                self.dataframe.update()
            elif q_command == 'Add selected to plot':
                EF1.add_selected()
            else:
                logging.warning("Command \""+str(q_command) + "\" in queue could not be executed")

    def new_database(self):
        if messagebox.askokcancel('Sicherheitsabfrage','Möchten Sie wirklich eine neue Database beginnen? Ungesicherte Daten werden unwiederbringlich gelöscht'):
            sd.reset()
            EF1.reset()
            self.database_filename = None
            
    def load_database(self):
        OpenFilename = filedialog.askopenfilename(initialdir = './databases',filetypes = [('Databases', '.pkl'), ('all files', '.*')])

        if len(OpenFilename ) == 0:
            return

        sd.load_database(OpenFilename,overwrite=True)
        self.database_filename = OpenFilename
        self.main_auftragskonto = sd.longterm_data['Auftragskonto'].value_counts().idxmax()
        q1.put('Update Plot')

    def import_csv(self):
        OpenFilename = filedialog.askopenfilename(initialdir = './csv',filetypes = [('CSV Datenbank', '.csv'), ('all files', '.*')])

        if len(OpenFilename ) == 0:
            return
        main_auftragkonto_load = sd.get_main_auftragskonto(OpenFilename)

        if main_auftragkonto_load !=self.main_auftragskonto:
            if not messagebox.askokcancel('Sicherheitsabfrage','Kontonummer des CSVs stimmen nicht mit bestehenden Daten überein. Trotzdem fortfahren?'):
                return
    
            
        info = sd.load_data(OpenFilename)
        q1.put('Update Plot')
        messagebox.showinfo('Import Bericht','Eine csv Datei mit {Csv size} Einträgen wurde geladen. {#Duplicate} davon waren schon vorhanden und {#Imported} neue Einträge wurden importiert. Die Datenbank enthält nun {New size} Einträge'.format(**info))

    def save_database(self):
        if self.database_filename is not None:
            sd.save_database(self.database_filename[:-4],overwrite=True)
        else:
            self.save_database_as()

    def save_database_as(self):
        SaveFilename = filedialog.asksaveasfilename(initialdir = './databases')
        if SaveFilename[-4:] == '.pkl' or SaveFilename[-4:] == '.csv':
            SaveFilename = SaveFilename[:-4]
        
        if not len(SaveFilename )==0:
            sd.save_database(SaveFilename,overwrite=True)

        
    def quit_program(self):
        root.destroy()

    def create_widgets(self):
        self.menubar = tk.Menu(self,tearoff=0)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        
        self.filemenu.add_command(label="New Database", command=self.new_database)
        self.filemenu.add_command(label="Load Database", command=self.load_database)
        self.filemenu.add_command(label="Save Database", command=self.save_database)
        self.filemenu.add_command(label="Save Database as", command=self.save_database_as)
        
        self.filemenu.add_command(label="Add csv", command=self.import_csv)


        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.quit_program)

        canvasFrame = tk.Frame(self,takefocus = False)
        canvasFrame.pack(side=tk.LEFT, fill=tk.BOTH,expand=True)


        def read_coordinates(event):
            if event.xdata is None or event.ydata is None:
                return
            if event.button == 1:
                EF1.nearest_point(event.xdata, event.ydata  )
                q1.put('Update Dataframe')
                q1.put('Add selected to plot')

        def handle_figure_key_press(event):
            key = event.key
            if app.chosen_data is None:
                app.chosen_data = 0
            if key == 'right' and app.chosen_data+1 < sd.longterm_data.shape[0]:
                app.chosen_data += 1 
            elif key == 'left' and app.chosen_data>0:
                app.chosen_data += -1

            EF1.last_selected_point = EF1.point_data[app.chosen_data,:]

##            print(sd.longterm_data.ix[app.chosen_data])
            q1.put('Update Dataframe')
            q1.put('Add selected to plot')

        EF1.canvas = FigureCanvasTkAgg(EF1.f, canvasFrame)
        EF1.canvas.show()
        EF1.canvas.mpl_connect('button_press_event', read_coordinates)
        EF1.canvas.mpl_connect('key_press_event', handle_figure_key_press)
        EF1.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        EF1.toolbar = NavigationToolbar2TkAgg(EF1.canvas, canvasFrame)
        EF1.toolbar.update()
        EF1.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


        self.dataframe = DataFrame(self)
        self.dataframe.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    def __init__(self):

        self.chosen_data = None
        self.database_filename = None
        
        tk.Frame.__init__(self)
        self.pack()
        root.protocol('WM_DELETE_WINDOW', self.quit_program)
        root.resizable(width=False, height=False)
        root.title('Control')
        root.after(300, self.update_status)
        root.geometry('{}x{}'.format(1300, 700))
        self.create_widgets()
        root.config(menu=self.menubar)
        root.title('Konto Verwaltungssoftware')
##        sd.load_database('./databases/test_database.pkl')  # for testing faster
        q1.put('Update Plot')

root = tk.Tk()
app = Application()
app.mainloop()
