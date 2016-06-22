
def convert_to_days(date):
	return date.day

Konto['Monatstag'] = Konto['Buchungstag'].apply(convert_to_days)





days = range(1,32)
binned_res = np.zeros(31)
n_entries = np.zeros(31)+1e-12

for index,row in Konto.iterrows():
	if row['Verwendungszweck'] != 'Konto Korrektur':
		day = row['Monatstag']
		binned_res[day-1] += row['Betrag']
		n_entries[day-1] += 1

plt.figure(1,figsize=(12,8))
plt.plot(days,binned_res,'ko-',linewidth=2)
plt.show()

plt.figure(2,figsize=(12,8))
plt.plot(days,binned_res/n_entries,'ko-',linewidth=2)
plt.show()

