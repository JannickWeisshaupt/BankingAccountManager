import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

plt.ion()


##matplotlib.style.use('ggplot')

##

class SparkasseDataframe:
    def __init__(self):
        self.longterm_data = None
        self.chosen_subset = None
        self.labels = set(['Unbekannt'])

    def sanitize_data(self, data_in,inplace=True):
        if inplace:
            data = data_in
        else:
            data = data_in.copy(deep=True)

        if 'Label' not in data.columns:
            data['Label'] = 'Unbekannt'

        data.drop_duplicates(inplace=True, subset=['Betrag', 'Buchungstag', 'Kontonummer'])
        data.sort_values(by=['Buchungstag', 'Verwendungszweck'], ascending=[True, True], inplace=True)
        data['SumBetrag'] = data['Betrag'].cumsum()
        data.reset_index(drop=True, inplace=True)
        return data

    def load_data(self, filename):

        data = pd.read_csv(filename, sep=';', error_bad_lines=True, encoding="ISO-8859-1", decimal=",")
        data.drop(['Buchungstag'], axis=1, inplace=True)
        data['Buchungstag'] = pd.to_datetime(data['Valutadatum'], dayfirst=True)
        data.sort_values(by='Buchungstag', ascending=True, inplace=True)
        data['Betrag'].astype(float)
        ##        data['SumBetrag'] = data['Betrag'].cumsum()
        if self.longterm_data is not None:
            old_size = self.longterm_data.shape[0]
            merged_data = pd.concat([self.longterm_data, data])
            ##            merged_data.drop_duplicates(inplace=True,subset=['Betrag','Buchungstag','Kontonummer','Verwendungszweck'])
            ##            merged_data.sort_values(by='Buchungstag',ascending=True,inplace=True)
            ##            merged_data['SumBetrag'] = merged_data['Betrag'].cumsum()
            merged_data = self.sanitize_data(merged_data)
            self.longterm_data = merged_data
        else:
            old_size = 0
            data = self.sanitize_data(data)
            data['SumBetrag'] = data['Betrag'].cumsum()
            self.longterm_data = data

        importfile_size = data.shape[0]
        new_size = self.longterm_data.shape[0]
        n_import = new_size - old_size
        n_duplicate = importfile_size - n_import

        return {'New size': new_size, '#Imported': n_import, '#Duplicate': n_duplicate, 'Csv size': importfile_size}

    def adjust_to_value(self, value, date):
        print(type(date))
        if type(date) is not datetime and type(date) is not pd.tslib.Timestamp:
            date = datetime.strptime(date, '%Y-%m-%d')

        for row in self.longterm_data.iterrows():
            if row[1]['Buchungstag'] > date:
                break

        betrag_at_date = row[1]['SumBetrag']
        corr_value = value - betrag_at_date
        df = pd.DataFrame(np.matrix(['Konto Korrektur', corr_value, date]), index=range(1),
                          columns=['Verwendungszweck', 'Betrag', 'Buchungstag'])
        merged_data = pd.concat([self.longterm_data, df])
        merged_data = self.sanitize_data(merged_data)
        self.longterm_data = merged_data

    def save_database(self, filename, overwrite=False):
        if not overwrite and os.path.isfile(filename):
            return
        self.longterm_data.to_pickle(filename + '.pkl')
        self.longterm_data.to_csv(filename + '.csv')

    def load_database(self, filename, overwrite=False):
        if (self.longterm_data is not None) and not overwrite:
            raise Exception('database already in memory')
        self.longterm_data = pd.read_pickle(filename)
        self.sanitize_data(self.longterm_data)
        self.labels = set(self.longterm_data['Label'].dropna())

    def statistical_analysis(self):
        summe = self.longterm_data['SumBetrag']
        print(summe.mean())


    def find_subset(self, column, value):
        if column == 'Buchungstag':
            value = datetime.strptime(value, '%Y-%m-%d')
        self.chosen_subset = self.longterm_data.loc[self.longterm_data[column] == value]
        self.chosen_subset.reset_index(drop=True, inplace=True)

    def export_daterange(self, datestart, dateend):
        datestart = datetime.strptime(datestart, '%Y-%m-%d')
        dateend = datetime.strptime(dateend, '%Y-%m-%d')
        return self.longterm_data.loc[
            (self.longterm_data['Buchungstag'] >= datestart) * (self.longterm_data['Buchungstag'] <= dateend)]

    def get_main_auftragskonto(self, filename):
        data = pd.read_csv(filename, sep=';', error_bad_lines=True, encoding="ISO-8859-1", decimal=",")
        return data['Auftragskonto'].value_counts().idxmax()

    def reset(self):
        self.longterm_data = None

    def find_subset_contains(self, column, string, reset_index=False):
        df = self.longterm_data
        self.chosen_subset = df[df[column].str.contains(string, case=False).fillna(False)]
        if reset_index:
            self.chosen_subset.reset_index(drop=True, inplace=True)
        return self.chosen_subset

    def export_selection(self, filename, filetype=None):
        if self.chosen_subset is None or filetype is None:
            return
        if filename[-4] == '.':
            filename = filename[:-4]

        subset_for_export = self.sanitize_data(self.chosen_subset,inplace=False)
        subset_for_export.drop('rolling_mean', axis=1, inplace=True)

        if filetype == 'csv':
            subset_for_export.to_csv(filename+'.csv')
        elif filetype == 'pkl':
            subset_for_export.to_pickle(filename+'.pkl')


    def drop_entry(self,index):
        self.longterm_data.drop(index,inplace=True)
        self.sanitize_data(self.longterm_data)


    def find_entry(self,info):
        return self.longterm_data.ix[(self.longterm_data['Betrag'] == info['Betrag']) &
                                   (self.longterm_data['Buchungstag'] == info['Buchungstag']) & (self.longterm_data['Kontonummer'] == info['Kontonummer'])].index

    def set_label(self, df, label, index=None):
        if index is None:
            df.loc[:, 'Label'] = label
        else:
            df.loc[index, 'Label'] = label

    def set_label_by_subset(self, subset, label):
        self.longterm_data.loc[subset.index, 'Label'] = label




if __name__ == "__main__":
    sd = SparkasseDataframe()
    ##    sd.load_data('umsatz.CSV')
    ####    sd.longterm_data.plot(x='Buchungstag',y='SumBetrag',marker='.',linewidth=2)
    ##    sd.load_data('umsatz_20_05_16.CSV')
    ####    sd.longterm_data.plot(x='Buchungstag',y='SumBetrag',marker='.',linewidth=2)
    ##
    ##    sd.adjust_to_value(5250,'2015-11-15')
    sd.load_database('./databases/jannick_sparkasse.pkl')
    sd.sanitize_data(sd.longterm_data, inplace=True)
    mbi = sd.find_subset_contains('Beguenstigter/Zahlungspflichtiger', 'forschungs', reset_index=False)
    sd.set_label_by_subset(mbi, 'Gehalt')
    sd.save_database('test')

    ##    sd.adjust_to_value(400,'2016-02-20')
    ##    sd.save_database('./databases/familienkonto_sparkasse',overwrite=True)
    # ax1 = sd.longterm_data.plot(x='Buchungstag', y='SumBetrag', marker='.', linewidth=2)
    # sd.find_subset('Betrag', -205)
    # sd.longterm_data['rolling_mean'] = sd.longterm_data['SumBetrag'].rolling(center=False, window=60,
    #                                                                          min_periods=1).mean()
    # sd.longterm_data.plot(ax=ax1, x='Buchungstag', y='rolling_mean', color='g', linewidth=2)
    ##    sd.save_database('test_database')
    ##    sd.load_database('test_database.pkl')
