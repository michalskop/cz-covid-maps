"""Prepare data from UZIS for maps and table."""

import datetime
from os import replace
# import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame

# read data from UZIS
url = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/obce.csv"
df = pd.read_csv(url, delimiter=",")

# remove non existing Brdy and 999999
df = df[df.obec_kod != 539996]
df = df[df.obec_kod != 999999]

# vojenske ujezdy
vu_codes = [545422, 592935, 555177, 503941]

# last date
today = datetime.date.today()
last_day = today + datetime.timedelta(days=-1)
last_date = last_day.isoformat()
first_day = today + datetime.timedelta(days=-366)
first_date = first_day.isoformat()

# read data from 'origin.csv' (geometries)
origin = pd.read_csv("obce/origin.csv")

# basics
data = origin
# data2 = origin

data['datum'] = f'{last_day.day}. {last_day.month}.'
# data2['datum'] = f'{first_day.day}. {first_day.month}.'

# prepare empty
data['týdenní přírůstek na 100 tis. obyvatel'] = 0

# data2['value'] = 0
# data2['aktuálně nemocných na 100 tis. obyvatel'] = 0

# pivot table
pt = pd.pivot_table(df, index='obec_kod', columns='datum', values='nove_pripady_7_dni', fill_value=0)

# change dates names, prepare values
all_dates = pt.columns[1:]
selected_dates = [d for d in all_dates if d >= first_date and d <= last_date]
weekly_dates = [d for d in selected_dates if datetime.datetime.fromisoformat(d).weekday() == last_day.weekday()]

pt_selected = pt[selected_dates]
pt_weekly = pt[weekly_dates]

pt_selected.columns = [(lambda x: datetime.datetime.fromisoformat(x).strftime('%-d.%-m.%y'))(x) for x in selected_dates]
pt_selected = pt_selected.reset_index().rename(columns={'obec_kod': 'code'})
pt_weekly.columns = [(lambda x: ("week_" + str(x)))(x) for x in range(0, len(weekly_dates))]

pt_selected_last = pt_selected.iloc[:, [0, -1]]

weekly = (pt_weekly.divide(pt_weekly.max(axis=1), axis=0) * 100).reset_index().rename(columns={'obec_kod': 'code'})

population = origin.sort_values(by=['code'])[['code', 'počet obyv.']]
population['počet obyv.'] = population['počet obyv.'].str.replace(' ','').astype(int)

pt_selected = pt_selected.merge(population, on='code')

selected = pd.concat([pt_selected['code'], round(pt_selected.iloc[:, 1:-1].divide(pt_selected['počet obyv.'], axis=0).fillna(0) * 100000, 1)], axis=1)

# merge
pt_selected_last.columns = ['code', 'dnes']
data = data.merge(pt_selected_last, on='code')

data = data.merge(weekly, on='code', how='left')
data = data.merge(selected, on='code', how='left')

# add today values
data['týdenní přírůstek na 100 tis. obyvatel'] = data.iloc[:, -1]

# save
data.to_csv('obce/incidence7.csv', index=False)



# test
# selected[selected['code'] == 554979]
# pt_selected[pt_selected['obec_kod'] == 554979]
# df[df['obec_kod'] == 554979]

# df[df['obec_kod'] == 581291]