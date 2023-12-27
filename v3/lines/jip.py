"""Weekly JIP and hospitalizations."""

import datetime
import pandas as pd

localpath = "v3/lines/"

# read data from UZIS
url = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/nakazeni-hospitalizace-testy.csv"
df = pd.read_csv(url, delimiter=",")

# last date
last_date = df['datum'].max()


df['date'] = pd.to_datetime(df['datum'])
df = df.set_index('date')
pt = df.resample('W', closed='right', label='right').sum().reset_index().sort_values(by='date')

ptout = pt[['date', 'nove_hospitalizace', 'nove_jip']].copy()
ptout.rename(columns={'date': 'datum', 'nove_hospitalizace': 'Nové hospitalizace', 'nove_jip': 'Nově na JIP'}, inplace=True)

# set as integer
ptout.fillna(0, inplace=True)
ptout['Nové hospitalizace'] = ptout['Nové hospitalizace'].astype(int)
ptout['Nově na JIP'] = ptout['Nově na JIP'].astype(int)

# save
ptout.to_csv(localpath + "hospitalizace_jip.csv", index=False)

