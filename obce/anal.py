"""Prepare data from UZIS for maps and table - obce."""

import copy
import datetime
import pandas as pd
import numpy as np

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
data = copy.deepcopy(origin)
data2 = copy.deepcopy(origin)


data['datum'] = f'{last_day.day}. {last_day.month}.'
data2['datum'] = f'{first_day.day}. {first_day.month}.'

# prepare empty
data['dnes'] = 0
data2['dnes'] = 0

# pivot tables
pt = pd.pivot_table(df, index='obec_kod', columns='datum', values='nove_pripady_7_dni', fill_value=0)
pt2 = pd.pivot_table(df, index='obec_kod', columns='datum', values='aktivni_pripady', fill_value=0)

# change dates names, prepare values
all_dates = pt.columns[1:]
selected_dates0 = [d for d in all_dates if d >= first_date and d <= last_date]
selected_dates = [d for d in all_dates if (d >= first_date and d <= last_date) and (((last_day - datetime.date.fromisoformat(d)).days <= 30) or ((last_day - datetime.date.fromisoformat(d)).days % 2 == 1))] # only last 30 days and odd days
weekly_dates = [d for d in selected_dates0 if datetime.datetime.fromisoformat(d).weekday() == last_day.weekday()]

pt_selected = pt[selected_dates]
pt_weekly = pt[weekly_dates]
pt2_selected = pt2[selected_dates]
pt2_weekly = pt2[weekly_dates]

pt_selected.columns = [(lambda x: datetime.datetime.fromisoformat(x).strftime('%-d.%-m.%y'))(x) for x in selected_dates]
pt_selected = pt_selected.reset_index().rename(columns={'obec_kod': 'code'})
pt_weekly.columns = [(lambda x: ("week_" + str(x)))(x) for x in range(0, len(weekly_dates))]

pt2_selected.columns = [(lambda x: datetime.datetime.fromisoformat(x).strftime('%-d.%-m.%y'))(x) for x in selected_dates]
pt2_selected = pt2_selected.reset_index().rename(columns={'obec_kod': 'code'})
pt2_weekly.columns = [(lambda x: ("week_" + str(x)))(x) for x in range(0, len(weekly_dates))]

pt_selected_last = pt_selected.iloc[:, [0, -1]]
pt2_selected_last = pt2_selected.iloc[:, [0, -1]]

weekly = (round(pt_weekly.divide(pt_weekly.max(axis=1), axis=0) * 100).fillna(0).astype(int)).reset_index().rename(columns={'obec_kod': 'code'})
weekly2 = (round(pt2_weekly.divide(pt2_weekly.max(axis=1), axis=0) * 100).fillna(0).astype(int)).reset_index().rename(columns={'obec_kod': 'code'})

population = origin.sort_values(by=['code'])[['code', 'počet obyv.']]
population['počet obyv.'] = population['počet obyv.'].str.replace(' ','').astype(int)

pt_selected = pt_selected.merge(population, on='code')
pt2_selected = pt2_selected.merge(population, on='code')

# last year with code
selected = pd.concat([pt_selected['code'], round(pt_selected.iloc[:, 1:-1].divide(pt_selected['počet obyv.'], axis=0).fillna(0) * 100000, 1)], axis=1)
selected2 = pd.concat([pt2_selected['code'], round(pt2_selected.iloc[:, 1:-1].divide(pt2_selected['počet obyv.'], axis=0).fillna(0) * 100000, 1)], axis=1)

# merge
pt_selected_last.columns = ['code', 'počet']
data = data.merge(pt_selected_last, on='code')

data = data.merge(weekly, on='code', how='left')
data = data.merge(selected, on='code', how='left')

pt2_selected_last.columns = ['code', 'počet']
data2 = data2.merge(pt2_selected_last, on='code')

data2 = data2.merge(weekly2, on='code', how='left')
data2 = data2.merge(selected2, on='code', how='left')

# add today values
data['dnes'] = data.iloc[:, -1]
data2['dnes'] = data2.iloc[:, -1]

# vojenske ujezdy
vu_index = data[data['code'].isin(vu_codes)].index
data.loc[vu_index, 'dnes'] = np.nan
data2.loc[vu_index, 'dnes'] = np.nan
data.loc[vu_index, 'počet'] = np.nan
data2.loc[vu_index, 'počet'] = np.nan
for s in selected.columns[1:]:
    data.loc[vu_index, s] = np.nan
    data2.loc[vu_index, s] = np.nan

data['počet'] = data['počet'].astype(str).apply(lambda x: x.replace('.0',''))
data2['počet'] = data2['počet'].astype(str).apply(lambda x: x.replace('.0',''))

# save
data.to_csv('obce/incidence7.csv', index=False)
data2.to_csv('obce/prevalence.csv', index=False)

# get back to float
data['počet'].astype(float)
data2['počet'].astype(float)

# table
data3 = copy.deepcopy(origin)

del data3["geometry"]

# table prevalence
data3['počet obyv.'] = data3['počet obyv.'].str.replace(' ','').astype(int)
data3 = data3.merge(pt2_selected_last, on='code')
data3.rename(columns={'počet': 'prevalence'}, inplace=True)

selected2_last = selected2.iloc[:, [0, -1]].apply(round).astype(int)
selected2_last.columns = ['code', '/100 tis.']
data3 = data3.merge(selected2_last, on='code')

t = selected2.iloc[:, -15:]
t = pd.concat([t, selected2.iloc[:, 0]], axis=1)
t.columns = [(lambda x: x.replace(".", ". "))(x) for x in t.columns]
data3 = data3.merge(t, on='code')

# table incidence
data3 = data3.merge(pt_selected_last, on='code')
data3.rename(columns={'počet': 'incidence 7d'}, inplace=True)

data3 = data3.merge(selected.iloc[:, [0, -1]].apply(round).astype(int), on='code')
c = data3.columns.tolist()
c[-1] = '/100tis.'
data3.columns = c

table_weekly_dates = [d for d in all_dates if datetime.datetime.fromisoformat(d).weekday() == last_day.weekday()]

pt_table_weekly = pt[table_weekly_dates]
pt_table_weekly.columns = [(lambda x: datetime.datetime.fromisoformat(x).strftime('%-d.%-m.%y'))(x) for x in table_weekly_dates]
pt_table_weekly = pt_table_weekly.reset_index().rename(columns={'obec_kod': 'code'})

data3 = data3.merge(pt_table_weekly, on='code')

data3.sort_values(by=['počet obyv.'], ascending=[False], inplace=True)

# vojenske ujezdy
vu_index = data3[data3['code'].isin(vu_codes)].index
data3.drop(vu_index, inplace=True)

# save table
data3.to_csv('obce/table.csv', index=False)
