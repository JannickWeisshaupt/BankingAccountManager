#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
from tkinter import ttk
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog

import numpy as np
import pandas as pd
import os
import sys

import matplotlib as mpl

mpl.use('Tkagg')

import datetime as dt
import time
import ctypes
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

from matplotlib import gridspec
import logging
import queue

from SparkasseDataframe import SparkasseDataframe
from terminal_frame import TerminalFrame

import matplotlib.style

matplotlib.style.use('classic')
font = dict(family='serif', size=18)
plt.rc('font', **font)

sd = SparkasseDataframe()

if not os.path.exists('~/.banking_manager'):
    os.makedirs('~/.banking_manager')


logging.basicConfig(level=logging.DEBUG,
                    filename="~/.banking_manager/logfile_" + str(dt.datetime.date(dt.datetime.today())) + ".log",
                    filemode="a+",
                    format="%(asctime)-15s %(levelname)-8s %(message)s")

logging.info('Program started')

myappid = u'Konto-Verwaltung'  # arbitrary string
# ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

q1 = queue.Queue()


class LabelWithEntry(tk.Frame):
    def __init__(self, master, text, width_label=10, width_entry=20, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.label = ttk.Label(self, text=text, width=width_label)
        self.label.grid(row=0, column=0)

        self.entry = ttk.Entry(self, width=width_entry)
        self.entry.grid(row=0, column=1)

    def get(self):
        return self.entry.get()

    def set(self, value, fmt="{0:6.4f}"):
        self.entry.delete(0, 'end')
        self.entry.insert(0, fmt.format(value))


class CopyableLabel(ttk.Entry):
    def __init__(self, master, text='', **kw):
        super().__init__(master, **kw)
        self.insert(0, text)
        self.configure(state="readonly")
        # self.configure(inactiveselectbackground=self.cget("selectbackground"))

    def set_text(self, text):
        self.configure(state="NORMAL")
        self.delete(0, tk.END)
        self.insert(0, text)
        self.configure(state="readonly")


class NewCBox(ttk.Combobox):
    def __init__(self, master, dictionary, current=0, *args, **kw):
        super().__init__(master, values=sorted(list(dictionary.keys())), state='readonly', *args, **kw)
        self.dictionary = dictionary
        self.set(current)

    def value(self):
        return self.dictionary[self.get()]

    def set_values(self, dictionary):
        self.dictionary = dictionary
        self['values'] = list(dictionary.keys())


class DataFrame(tk.Frame):
    def __init__(self, master, app, *arg, **kwargs):
        self.master = master
        self.app = app
        super().__init__(master, *arg, **kwargs)

        width_value = 60
        self._after_id = None

        self.header = ttk.Label(self, text='Vorgangsinformation', justify=tk.CENTER, font=("Helvetica", 20),
                                anchor=tk.CENTER)
        self.header.grid(row=0, column=0, columnspan=2, pady=20)

        self.begL = ttk.Label(self, text='Begünstigter/Zahlungspflichtiger:', justify=tk.LEFT, anchor=tk.W, width=35)
        self.begL.grid(row=1, column=0, pady=3, sticky='w')
        self.begL_value = CopyableLabel(self, text='', justify=tk.LEFT, width=width_value)
        self.begL_value.grid(row=1, column=1, pady=3, sticky='w')

        self.betragL = ttk.Label(self, text='Betrag:', justify=tk.LEFT, anchor=tk.W)
        self.betragL.grid(row=2, column=0, pady=3, sticky='w')
        self.betragL_value = CopyableLabel(self, text='', justify=tk.LEFT, width=width_value)
        self.betragL_value.grid(row=2, column=1, pady=3, sticky='w')

        self.standL = ttk.Label(self, text='Kontostand:', justify=tk.LEFT, anchor=tk.W)
        self.standL.grid(row=3, column=0, pady=3, sticky='w')
        self.standL_value = CopyableLabel(self, text='', justify=tk.LEFT, width=width_value)
        self.standL_value.grid(row=3, column=1, pady=3, sticky='w')

        self.verwL = ttk.Label(self, text='Verwendungszweck:', justify=tk.LEFT, anchor=tk.W)
        self.verwL.grid(row=4, column=0, pady=3, sticky='w')
        self.verwL_value = CopyableLabel(self, text='', justify=tk.LEFT, width=width_value)
        self.verwL_value.grid(row=4, column=1, pady=3, sticky='w', rowspan=2)
        # self.verwL2_value = CopyableLabel(self, text='', justify=tk.LEFT, width=width_value)
        # self.verwL2_value.grid(row=5, column=1, pady=3, sticky='w')

        self.ktnrL = ttk.Label(self, text='Kontonummer:', justify=tk.LEFT, anchor=tk.W)
        self.ktnrL.grid(row=6, column=0, pady=3, sticky='w')
        self.ktnrL_value = CopyableLabel(self, text='', justify=tk.LEFT, width=width_value)
        self.ktnrL_value.grid(row=6, column=1, pady=3, sticky='w')

        self.blzL = ttk.Label(self, text='BLZ:', justify=tk.LEFT, anchor=tk.W)
        self.blzL.grid(row=7, column=0, pady=3, sticky='w')
        self.blzL_value = CopyableLabel(self, text='', justify=tk.LEFT, width=width_value)
        self.blzL_value.grid(row=7, column=1, pady=3, sticky='w')

        self.tagL = ttk.Label(self, text='Buchungstag:', justify=tk.LEFT, anchor=tk.W)
        self.tagL.grid(row=8, column=0, pady=3, sticky='w')
        self.tagL_value = CopyableLabel(self, text='', justify=tk.LEFT, width=width_value)
        self.tagL_value.grid(row=8, column=1, pady=3, sticky='w')

        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=9, column=0, columnspan=2, sticky='nwse')

        # self.delete_selected_button = ttk.Button(self.button_frame, text='Lösche Eintrag', command=self.drop_selected,takefocus=False)
        # self.delete_selected_button.pack(side=tk.LEFT, anchor='e', pady=5, padx=5)

        # Here begins the search part

        self.subframe1 = ttk.Frame(self)
        self.subframe1.grid(row=10, column=0, columnspan=2, sticky='nwse')

        self.header2 = ttk.Label(self.subframe1, text='Suche', width=30, anchor=tk.CENTER, justify=tk.CENTER,
                                 font=("Helvetica", 20))
        self.header2.grid(row=0, column=0, columnspan=4, pady=20)

        searchL = ttk.Label(self.subframe1, text='Suchen:', justify=tk.LEFT, anchor=tk.W)
        searchL.grid(row=1, column=0, sticky='w', pady=10)

        search_dic = {'Kontonummer': 'Kontonummer', 'BLZ': 'BLZ', 'Betrag': 'Betrag',
                      'Verwendungszweck': 'Verwendungszweck', 'Datum': 'Buchungstag',
                      'Begünstigter/Zahlungspflichtiger': 'Beguenstigter/Zahlungspflichtiger'}

        self.search_combo = NewCBox(self.subframe1, search_dic, width=30, takefocus=False)
        self.search_combo.grid(row=1, column=1, sticky='w', padx=5)
        self.search_combo.current(0)

        def handle_update_event(*args):
            # cancel the old job
            if self._after_id is not None:
                master.after_cancel(self._after_id)
            # create a new job
            self._after_id = master.after(100, self.app.update_search)

        self.search_combo.bind("<<ComboboxSelected>>", handle_update_event)

        def return_press_handler(event):
            self.search_checkvar.set(True)
            self.app.update_search()

        def escape_press_handler(event):
            self.search_checkvar.set(False)
            self.app.update_search()

        self.return_press_handler = lambda event: return_press_handler(event)

        self.search_field = ttk.Entry(self.subframe1, width=40)
        self.search_field.grid(row=1, column=2, padx=5)
        self.search_field.bind('<Key>', handle_update_event)
        self.search_field.bind('<Return>', return_press_handler)
        self.search_field.bind('<Escape>', escape_press_handler)

        self.search_checkvar = tk.BooleanVar()
        self.search_checkvar.set(False)
        self.search_checkbutton = ttk.Checkbutton(self.subframe1, text="Aktiv", variable=self.search_checkvar,
                                                  command=self.app.update_search, takefocus=False)
        self.search_checkbutton.grid(row=1, column=3, sticky='w')

        self.subframe2 = ttk.Frame(self)
        self.subframe2.grid(row=11, column=0, columnspan=2, sticky='nwse')

        self.NfoundL = ttk.Label(self.subframe2, text='Gefundene Einträge:', justify=tk.LEFT, anchor=tk.W, width=35)
        self.NfoundL.grid(row=0, column=0, pady=3, sticky='w')
        self.NfoundL_value = CopyableLabel(self.subframe2, text='', justify=tk.LEFT, width=width_value)
        self.NfoundL_value.grid(row=0, column=1, pady=3, sticky='w')

        self.totsumL = ttk.Label(self.subframe2, text='Gesamtsumme:', justify=tk.LEFT, anchor=tk.W)
        self.totsumL.grid(row=1, column=0, pady=3, sticky='w')
        self.totsumL_value = CopyableLabel(self.subframe2, text='', justify=tk.LEFT, width=width_value)
        self.totsumL_value.grid(row=1, column=1, pady=3, sticky='w')

        # self.subframe3 = tk.Frame(self)
        # self.subframe3.grid(row=12, column=0, columnspan=2, sticky='nwse')
        # self.header3 = ttk.Label(self.subframe3, text='Konto Statistik', width=30, anchor=tk.CENTER, justify=tk.CENTER,
        #                          font=("Helvetica", 20))
        #
        #
        # self.header3.grid(row=0, column=0, columnspan=4, pady=20)
        #
        # self.test = ttk.Label(self.subframe3, text='Begünstigter/Zahlungspflichtiger:', justify=tk.LEFT, anchor=tk.W, width=35)
        # self.test.grid(row=1, column=0, pady=3, sticky='w')
        # self.test_value = CopyableLabel(self.subframe3, text='', justify=tk.LEFT, width=width_value)
        # self.test_value.grid(row=1, column=1, pady=3, sticky='w')

    def update_elements(self):

        if app.search_active_bool and len(sd.chosen_subset) > 0:
            chosen_subset = sd.chosen_subset
        else:
            chosen_subset = sd.longterm_data

        beg = chosen_subset.loc[app.chosen_data, 'Beguenstigter/Zahlungspflichtiger']
        kontostand = chosen_subset.at[app.chosen_data, 'SumBetrag']
        betrag = chosen_subset.at[app.chosen_data, 'Betrag']
        buchungstag = chosen_subset.at[app.chosen_data, 'Buchungstag']
        verwendungszweck = str(chosen_subset.at[app.chosen_data, 'Verwendungszweck'])
        kontonummer = chosen_subset.at[app.chosen_data, 'Kontonummer']
        waehrung = chosen_subset.at[app.chosen_data, 'Waehrung']
        blz = chosen_subset.at[app.chosen_data, 'BLZ']

        if type(waehrung) is float:
            waehrung = 'EUR'
            blz = ''
            kontonummer = ''
            beg = ''

        if betrag > 0:
            self.begL.config(text='Zahlungspflichtiger:')
        else:
            self.begL.config(text='Begünstigter:')

        self.begL_value.set_text(beg)
        self.betragL_value.set_text("{:1.2f}".format(betrag) + ' ' + waehrung)
        self.standL_value.set_text("{:1.2f}".format(kontostand) + ' ' + 'EUR')

        self.verwL_value.set_text(verwendungszweck)
        # self.verwL2_value.config(text=verwendungszweck[35:])
        self.ktnrL_value.set_text(kontonummer)
        self.blzL_value.set_text(blz)
        self.tagL_value.set_text(dt.datetime.date(buchungstag))

    def update_search(self):

        if app.search_active_bool:
            chosen_subset = sd.chosen_subset
            gesamtsumme = chosen_subset['Betrag'].sum()
            Nfound = len(chosen_subset)
            self.NfoundL_value.set_text(Nfound)
            self.totsumL_value.set_text('{:1.2f}'.format(gesamtsumme))
        else:
            self.NfoundL_value.set_text('')
            self.totsumL_value.set_text('')

    def drop_selected(self):
        if not messagebox.askokcancel('Nachfrage', 'Moechten Sie diesen Eintrag wirklich loeschen', parent=self):
            return
        if app.search_active_bool:
            chosen_subset = sd.chosen_subset
            betrag = chosen_subset.at[app.chosen_data, 'Betrag']
            buchungstag = chosen_subset.at[app.chosen_data, 'Buchungstag']
            kontonummer = chosen_subset.at[app.chosen_data, 'Kontonummer']
            info = {'Kontonummer': kontonummer, 'Buchungstag': buchungstag, 'Betrag': betrag}
            app.chosen_data = int(sd.find_entry(info)[0])
        if app.chosen_data is None:
            return

        sd.drop_entry(app.chosen_data)
        app.update_search()
        q1.put('Update Plot')


class EmbeddedFigure(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.f = plt.Figure(figsize=(10, 10))
        gs = gridspec.GridSpec(1, 1, height_ratios=[1])
        self.subplot1 = self.f.add_subplot(gs[0])

        self.canvas = FigureCanvasTkAgg(self.f, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.master)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        bg = ttk.Style().lookup('TFrame', 'background')
        bg_rgb = self.winfo_rgb(bg)
        self.f.patch.set_facecolor([x / 2 ** 16 for x in bg_rgb])
        ##        self.f.tight_layout()
        self.subplot1.grid('on')
        self.subplot1.set_ylabel('Kontostand')
        self.point_data = None
        self.single_point_plot = None
        self.first_plot_bool = True

    def update(self):
        if not self.first_plot_bool:
            ylim = self.subplot1.get_ylim()
            xlim = self.subplot1.get_xlim()

        self.single_point_plot = None
        if sd.longterm_data is None:
            return

        self.subplot1.clear()

        if app.search_active_bool and len(sd.chosen_subset) > 0:
            plot_alpha = 0.3
            line_index = 2
            self.search_empty_bool = False

        elif app.search_active_bool and len(sd.chosen_subset) == 0:
            line_index = 0
            plot_alpha = 0.3
            self.search_empty_bool = True

        else:
            plot_alpha = 1
            line_index = 0

        plot1 = sd.longterm_data.plot(x='Buchungstag', y='SumBetrag', grid=True, linewidth=3, ax=self.subplot1,
                                      color='#E88400', legend=False, drawstyle='steps-post',
                                      alpha=plot_alpha * 0.8)
        plot2 = sd.longterm_data.plot(x='Buchungstag', y='SumBetrag', grid=True, marker='o', linewidth=0,
                                      ax=self.subplot1, color='#E80C46', legend=False, alpha=plot_alpha)

        if app.search_active_bool and len(sd.chosen_subset) > 0:
            plot3 = sd.chosen_subset.plot(x='Buchungstag', y='SumBetrag', grid=True, marker='o', linewidth=0,
                                          ax=self.subplot1, color='g', legend=False, ms=10)

        lines = self.subplot1.get_lines()
        xdata = lines[line_index].get_data()[0]
        ydata = lines[line_index].get_data()[1]

        if app.show_mean_bool:
            self.boxcar_data = pd.DataFrame()
            self.boxcar_data['Buchungstag'] = sd.longterm_data['Buchungstag']
            self.boxcar_data['rolling_mean'] = sd.longterm_data['rolling_mean'] = sd.longterm_data['SumBetrag'].rolling(
                center=False, window=60, min_periods=1).mean()
            plt4 = self.boxcar_data.plot(ax=self.subplot1, x='Buchungstag', y='rolling_mean', color='g', linewidth=4,
                                         alpha=0.5 * plot_alpha, legend=False, grid=True)

        xdata_conv = np.array([(t - dt.datetime(1, 1, 1)).total_seconds() / 60 / 60 / 24 + 1 for t in xdata])
        self.point_data = np.zeros((len(ydata), 2))
        self.point_data[:, 0] = xdata_conv
        self.point_data[:, 1] = ydata

        self.subplot1.set_ylabel('Kontostand')
        self.f.subplots_adjust(left=0.15, right=1)

        if not self.first_plot_bool:
            self.subplot1.set_xlim(*xlim)
            self.subplot1.set_ylim(*ylim)
        else:
            xlim = self.subplot1.get_xlim()
            xlim_diff = xlim[1] - xlim[0]
            self.subplot1.set_xlim(xlim[0] - xlim_diff / 40, xlim[1] + xlim_diff / 40)

        self.f.tight_layout()
        # plt.pause(0.001)
        self.canvas.draw()
        self.first_plot_bool = False

    def nearest_point(self, xp, yp):
        ylim = self.subplot1.get_ylim()
        xlim = self.subplot1.get_xlim()

        resc_fac = (ylim[1] - ylim[0]) / (xlim[1] - xlim[0])

        resc_data = np.zeros(self.point_data.shape)
        resc_data[:, 1] = self.point_data[:, 1] / resc_fac
        resc_data[:, 0] = self.point_data[:, 0]

        index = np.argmin(np.linalg.norm(resc_data - np.array([xp, yp / resc_fac]), axis=1))
        ##        index = np.argmin( np.abs(self.point_data[:,0]-xp))
        self.last_selected_point = self.point_data[index, :]

        if app.search_active_bool and len(sd.chosen_subset) > 0:
            app.chosen_data = sd.chosen_subset.index[index]
        else:
            app.chosen_data = index

        ##        print(sd.longterm_data.ix[index])
        return index

    def add_selected(self):

        if app.chosen_data is None:
            return

        if self.single_point_plot is not None:
            self.single_point_plot.remove()

        self.single_point_plot, = self.subplot1.plot(self.last_selected_point[0], self.last_selected_point[1], 'o',
                                                     color=[7 / 255, 85 / 255, 240 / 255], ms=7)

        plt.pause(0.001)
        self.canvas.draw()

    def reset(self):
        self.subplot1.cla()
        # self.toolbar._views.clear()
        # self.toolbar._positions.clear()
        self.first_plot_bool = True


class AccountCorrectionWindow(tk.Toplevel):
    def __init__(self, application, *args, **kwargs):
        super().__init__(application, *args, **kwargs)
        self.app = application
        self.konto_entry = LabelWithEntry(self, 'Aktueller Kontostand', width_label=20)
        self.konto_entry.grid(row=0, column=0)

        self.ok_button = ttk.Button(self, text='Ok', command=self.ok_event)
        self.ok_button.grid(row=1, column=0)

    def ok_event(self):
        try:
            sd.adjust_to_value(float(self.konto_entry.get().replace('.', '').replace(',', '.')), dt.datetime.now())
            self.destroy()
            app.EF1.first_plot_bool = True
            q1.put('Update Plot')
        except Exception:
            pass


class LabelFrame(ttk.Frame):
    def __init__(self, master, application, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.app = application
        self.header = ttk.Label(self, text='Labels', justify=tk.CENTER, font=("Helvetica", 20),
                                anchor=tk.CENTER)
        self.header.grid(row=0, column=0, columnspan=2, pady=20)

        self.cbox = NewCBox(self, dict.fromkeys(sd.labels, sd.labels))
        self.cbox.grid(row=1, column=0, columnspan=2)

        self.cbox.set('Unbekannt')

    def add_label(self):
        label_tl = ttk.Toplevel(self)
        label_entry = ttk.Entry(label_tl, width=20)
        label_entry.pack()

    def update_all(self):
        self.cbox.set_values(dict.fromkeys(list(sd.labels), list(sd.labels)))


class StatFigureFrame(tk.Toplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.f = plt.Figure(figsize=(20, 12))
        gs = gridspec.GridSpec(2, 3, height_ratios=[1, 1])
        self.subplot1 = self.f.add_subplot(gs[0])
        self.subplot2 = self.f.add_subplot(gs[1])
        self.f.patch.set_facecolor([240 / 255, 240 / 255, 237 / 255])
        self.canvas = FigureCanvasTkAgg(self.f, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def create_plots(self, account_data):
        def convert_to_days(date):
            return date.day

        account_data['Monatstag'] = account_data['Buchungstag'].apply(convert_to_days)
        days = np.array(range(1, 32))
        binned_res = np.zeros(31)
        n_entries = np.zeros(31) + 1e-12

        total_time_days = (account_data['Buchungstag'].iloc[-1] - account_data['Buchungstag'].iloc[0]).days
        total_time_months = total_time_days / 30

        for index, row in account_data.iterrows():
            if row['Verwendungszweck'] != 'Konto Korrektur':
                day = row['Monatstag']
                binned_res[day - 1] += row['Betrag']
                n_entries[day - 1] += 1

        self.subplot1.plot(days, 0 * days + (binned_res / total_time_months).mean(), 'r--', alpha=0.5, linewidth=2)
        self.subplot1.bar(days, binned_res / total_time_months, color=[0.6, 0.6, 0.6], align='center')
        self.subplot1.set_title('Ausgaben pro Monat')
        self.subplot1.set_xlabel('Tag im Monat')
        self.subplot1.set_ylabel('Betrag [Euro]')
        self.subplot1.set_xlim(0, 31.5)

        self.subplot2.bar(days, binned_res / n_entries, color=[0.6, 0.6, 0.6], align='center')
        self.subplot2.set_title('Mittlerer Betrag')
        self.subplot2.set_xlim(0, 31.5)
        self.subplot2.set_xlabel('Tag im Monat')
        self.subplot2.set_ylabel('Mittlerer Betrag [Euro]')

        self.f.tight_layout()
        plt.pause(0.001)
        self.canvas.draw()


class NewDatabaseFrame(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.geometry('{}x{}'.format(700, 300))
        self.wm_title("Neue Datenbank")
        self.resizable(width=False, height=False)

        self.temp_database_filename = None
        self.csv_loadname = None

        InformationFrame = ttk.Frame(self)
        InformationFrame.grid(row=0, column=0, sticky='ewns')

        label2 = ttk.Label(InformationFrame, text="File Name: ")
        label2.grid(row=0, column=0, sticky='w')

        labelDir = ttk.Label(InformationFrame, background='white', relief='ridge', width=60)
        labelDir.grid(row=0, column=1, sticky='w', columnspan=2)

        def ask_filename_database(labelDir):
            temp_filename = filedialog.asksaveasfilename(initialdir='./databases',
                                                         filetypes=[('Databases', '.pkl'), ('all files', '.*')],
                                                         parent=self)
            if len(temp_filename) == 0:
                return
            elif temp_filename[-4] == '.':
                temp_filename = temp_filename[:-4]
            self.temp_database_filename = temp_filename
            labelDir.config(text=temp_filename)

        SaveDirectoryButton = ttk.Button(InformationFrame, width=8, text='Name',
                                         command=lambda: ask_filename_database(labelDir), takefocus=False)
        SaveDirectoryButton.grid(column=3, row=0, padx=5, pady=3)

        KontostandL = ttk.Label(InformationFrame, text="Aktueller Kontostand: ")
        KontostandL.grid(row=1, column=0, sticky='w')

        self.KontostandL_value = ttk.Entry(InformationFrame, width=10)
        self.KontostandL_value.grid(row=1, column=1, sticky='w')

        KontostandL2 = ttk.Label(InformationFrame, text="Bitte im Format 10.000,23 oder 10000,23 eingeben")
        KontostandL2.grid(row=1, column=2, sticky='w', padx=5)

        csvL = ttk.Label(InformationFrame, text="Erstes CSV: ")
        csvL.grid(row=2, column=0, sticky='w')

        csvL_value = ttk.Label(InformationFrame, background='white', relief='ridge', width=60)
        csvL_value.grid(row=2, column=1, sticky='w', columnspan=2)

        def ask_filename_csv(labelDir):
            temp_filename = filedialog.askopenfilename(initialdir='./CSV',
                                                       filetypes=[('CSV files', '.csv'), ('all files', '.*')],
                                                       parent=self)
            if len(temp_filename) == 0:
                return
            self.csv_loadname = temp_filename
            labelDir.config(text=temp_filename)

        csvButton = ttk.Button(InformationFrame, width=8, text='Name', command=lambda: ask_filename_csv(csvL_value),
                               takefocus=False)
        csvButton.grid(column=3, row=2, padx=5, pady=3)

        ButtonFrame = ttk.Frame(self)
        ButtonFrame.grid(row=1, column=0, columnspan=2, sticky='ewns')

        OkBut = ttk.Button(ButtonFrame, text="OK", command=self.ask_new_database)
        OkBut.grid(row=0, column=0, ipady=5, pady=10)

        CancelBut = ttk.Button(ButtonFrame, text="Abbrechen", command=self.destroy)
        CancelBut.grid(row=0, column=1, ipady=5)

    def ask_new_database(self):
        try:
            kontostand_string = self.KontostandL_value.get()
            kontostand_string = kontostand_string.replace('.', '')
            kontostand_string = kontostand_string.replace(',', '.')
            aktueller_kontostand = float(kontostand_string)
        except:
            aktueller_kontostand = None

        missing_string = ''
        if self.temp_database_filename is None:
            missing_string += 'Filename, '
        if self.csv_loadname is None:
            missing_string += 'Erstes Csv, '
        if aktueller_kontostand is None:
            missing_string += 'aktueller Kontostand '

        if not missing_string == '' and not messagebox.askokcancel('Unvollständige Anhaben',
                                                                   'Sie haben nichts im Feld ' + missing_string + 'eingetragen. Trotzdem fortfahren?',
                                                                   parent=self):
            return

        if sd.longterm_data is None or messagebox.askokcancel('Sicherheitsabfrage',
                                                              'Möchten Sie wirklich eine neue Database beginnen? Ungesicherte Daten werden unwiederbringlich gelöscht',
                                                              parent=self):
            self.master.create_new_database()
            if self.csv_loadname is not None:
                sd.load_data(self.csv_loadname)
            if aktueller_kontostand is not None:
                datum = sd.longterm_data['Buchungstag'][0] - dt.timedelta(1)
                korr_value = float(sd.longterm_data['SumBetrag'].tail(1) - sd.longterm_data['SumBetrag'][0])
                sd.adjust_to_value(aktueller_kontostand - korr_value, datum)

            self.master.database_filename = self.temp_database_filename
            self.master.save_database()
            q1.put('Update Plot')
            self.destroy()


class Application(ttk.Frame):
    def create_new_database_frame(self):
        self.new_database_frame = NewDatabaseFrame(self)

    def update_search(self):
        if sd.longterm_data is None:
            return

        search_string = self.dataframe.search_field.get()
        if self.dataframe.search_checkvar.get() and not search_string.isspace() and len(search_string) > 0:
            column = self.dataframe.search_combo.value()
            if column == 'Betrag':
                search_string.replace(',', '.')
                sd.find_subset(column, float(search_string))
            else:
                sd.find_subset_contains(column, search_string)

            self.search_active_bool = True

        else:
            self.search_active_bool = False

        self.dataframe.update_search()
        q1.put('Update Plot')

    def create_new_database(self):
        sd.reset()
        self.EF1.reset()
        self.database_filename = None
        self.main_auftragskonto = None

    def update_status(self):
        root.after(1, lambda: self.update_status())
        if not q1.empty():
            q_command = q1.get()
            if q_command == 'Update Plot':
                self.EF1.update()
            elif q_command == 'Update Dataframe':
                self.dataframe.update_elements()
            elif q_command == 'Add selected to plot':
                self.EF1.add_selected()
            else:
                logging.warning("Command \"" + str(q_command) + "\" in queue could not be executed")

    def load_database(self):
        OpenFilename = filedialog.askopenfilename(initialdir='~',
                                                  filetypes=[('Databases', '.pkl'), ('all files', '.*')])

        if len(OpenFilename) == 0:
            return

        sd.load_database(OpenFilename, overwrite=True)
        self.database_filename = OpenFilename[:-4]
        self.main_auftragskonto = sd.longterm_data['Auftragskonto'].value_counts().idxmax()
        self.EF1.reset()
        self.update_search()
        self.labelframe.update_all()
        q1.put('Update Plot')

    def import_csv(self):
        OpenFilename = filedialog.askopenfilename(initialdir='~',
                                                  filetypes=[('CSV Datenbank', '.csv'), ('all files', '.*')])

        if len(OpenFilename) == 0:
            return
        try:
            main_auftragkonto_load = sd.get_main_auftragskonto(OpenFilename)
        except Exception as ex1:
            messagebox.showerror('Fehler beim Importieren',
                                 'Importieren ist mit Fehler ' + repr(ex1) + ' fehlgeschlagen')
            return

        if main_auftragkonto_load != self.main_auftragskonto and self.main_auftragskonto is not None:
            if not messagebox.askokcancel('Sicherheitsabfrage',
                                          'Kontonummer des CSVs stimmt nicht mit bestehenden Daten überein. Trotzdem fortfahren?'):
                return
        try:
            info = sd.load_data(OpenFilename)
        except Exception as ex1:
            messagebox.showerror('Fehler beim Importieren',
                                 'Importieren ist mit Fehler ' + repr(ex1) + ' fehlgeschlagen')

        self.EF1.first_plot_bool = True
        q1.put('Update Plot')
        messagebox.showinfo('Import Bericht',
                            'Eine csv Datei mit {Csv size} Einträgen wurde geladen. {#Duplicate} davon waren schon vorhanden und {#Imported} neue Einträge wurden importiert. Die Datenbank enthält nun {New size} Einträge'.format(
                                **info))

    def save_database(self):
        if self.database_filename is not None:
            sd.save_database(self.database_filename, overwrite=True)
        else:
            self.save_database_as()

    def save_database_as(self):
        SaveFilename = filedialog.asksaveasfilename(initialdir='~')
        if SaveFilename[-4:] == '.pkl' or SaveFilename[-4:] == '.csv':
            SaveFilename = SaveFilename[:-4]
        if not len(SaveFilename) == 0:
            sd.save_database(SaveFilename, overwrite=True)

    def export_selection(self, filetype=None):
        save_filename = filedialog.asksaveasfilename(initialdir='~',
                                                     filetypes=[('CSV Datenbank', '.csv'), ('PKL Datenbank', '.pkl')])

        if save_filename == '':
            return
        else:
            sd.export_selection(save_filename, filetype=filetype)

    def open_terminal_frame(self):
        if sd.longterm_data is not None:
            shared_vars = {'Konto': sd.longterm_data, 'Betrag': sd.longterm_data['Betrag'],
                           'Kontostand': sd.longterm_data['SumBetrag'], 'Buchungstag': sd.longterm_data['Buchungstag']}
        else:
            shared_vars = None

        if sd.chosen_subset is not None:
            shared_vars['Suchergebnisse'] = sd.chosen_subset

        self.terminal_frame = TerminalFrame(root, shared_vars)

    def open_account_correction_window(self):
        if self.account_correction_window is None or not self.account_correction_window.winfo_exists():
            self.account_correction_window = AccountCorrectionWindow(self)

    def open_stat_frame(self):
        stat_frame = StatFigureFrame(self)
        stat_frame.create_plots(sd.longterm_data)

    def quit_program(self):
        root.destroy()
        sys.exit()

    def create_widgets(self):
        self.menubar = tk.Menu(self, tearoff=0)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)

        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.filemenu.add_command(label="New Database", command=self.create_new_database_frame, accelerator="Strq+n")
        self.filemenu.add_command(label="Load Database", command=self.load_database, accelerator="Strq+l")
        self.filemenu.add_command(label="Save Database", command=self.save_database, accelerator="Strq+s")
        self.filemenu.add_command(label="Save Database as", command=self.save_database_as, accelerator="Strq+Shift+s")
        self.filemenu.add_command(label="Add csv", command=self.import_csv, accelerator="Strq+g")
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.quit_program, accelerator="Strq+q")

        self.exportmenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Export", menu=self.exportmenu)
        self.exportmenu.add_command(label="Selection as csv", command=lambda: self.export_selection(filetype='csv'))
        self.exportmenu.add_command(label="Selection as pkl", command=lambda: self.export_selection(filetype='pkl'))

        self.terminalmenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Terminal", menu=self.terminalmenu)
        self.terminalmenu.add_command(label="Starte Terminal", command=self.open_terminal_frame, accelerator="Strq+t")

        self.statmenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Statistik", menu=self.statmenu)
        self.statmenu.add_command(label="Statistische Übersicht", command=self.open_stat_frame)

        canvasFrame = ttk.Frame(self, takefocus=False)
        canvasFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def read_coordinates(event):
            self.EF1.canvas._tkcanvas.focus_set()
            self.EF1.toolbar.set_cursor(1)
            if event.xdata is None or event.ydata is None:
                return
            if event.button == 1:
                self.EF1.nearest_point(event.xdata, event.ydata)
                q1.put('Update Dataframe')
                q1.put('Add selected to plot')

        def handle_figure_key_press(event):
            key = event.key
            if app.chosen_data is None:
                app.chosen_data = 0
            if key == 'right' and app.chosen_data + 1 < sd.longterm_data.shape[0]:
                app.chosen_data += 1
            elif key == 'left' and app.chosen_data > 0:
                app.chosen_data += -1
            else:
                return

            self.EF1.last_selected_point = self.EF1.point_data[app.chosen_data, :]
            q1.put('Update Dataframe')
            q1.put('Add selected to plot')

        self.EF1 = EmbeddedFigure(canvasFrame)

        self.EF1.canvas.mpl_connect('button_press_event', read_coordinates)
        self.EF1.canvas.mpl_connect('key_press_event', handle_figure_key_press)

        self.EF1.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        sideFrame = ttk.Frame(self, takefocus=False)
        sideFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.dataframe = DataFrame(sideFrame, self)

        self.accountmenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Konto", menu=self.accountmenu)
        self.accountmenu.add_command(label="Konto Korrektur", command=self.open_account_correction_window)
        self.accountmenu.add_command(label="Loesche Eintrag", command=self.dataframe.drop_selected)
        self.dataframe.pack(side=tk.TOP, fill='x', expand=True)

        self.labelframe = LabelFrame(sideFrame, self)
        self.labelframe.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def __init__(self):
        self.search_active_bool = False
        self.chosen_data = None
        self.database_filename = None
        self.show_mean_bool = True

        ttk.Frame.__init__(self)
        self.pack()
        root.protocol('WM_DELETE_WINDOW', self.quit_program)
        root.resizable(width=False, height=False)
        root.title('Control')
        self.create_widgets()
        root.after(300, self.update_status)
        root.geometry('{}x{}'.format(1600, 850))

        root.config(menu=self.menubar)
        root.title('Konto Verwaltungssoftware')

        # Windows
        self.account_correction_window = None

        #        sd.load_database('./databases/test_database.pkl')  # for testing faster
        q1.put('Update Plot')
        # Root bindings
        root.bind_all('<Control-s>', lambda event: self.save_database())
        root.bind_all('<Control-S>', lambda event: self.save_database_as())
        root.bind_all('<Control-q>', lambda event: self.quit_program())
        root.bind_all('<Control-l>', lambda event: self.load_database())
        root.bind_all('<Control-n>', lambda event: self.new_database_frame())
        root.bind_all('<Control-f>',
                      lambda event: self.dataframe.search_field.focus_set() or self.dataframe.return_press_handler(
                          event))
        root.bind_all('<Control-g>', lambda event: self.import_csv())
        root.bind_all('<Control-t>', lambda event: self.open_terminal_frame())


root = tk.Tk()

root.style = ttk.Style()
# ('clam', 'alt', 'default', 'classic')
root.style.theme_use("clam")

app = Application()
app.mainloop()
