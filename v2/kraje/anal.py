"""Prepare data from UZIS for maps."""

import datetime
# import numpy as np
import pandas as pd

# last date
today = datetime.date.today()
last_day = today + datetime.timedelta(days=-1)
last_date = last_day.isoformat()

# read data from UZIS
url = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/incidence-7-14-kraje.csv"
df = pd.read_csv(url, delimiter=",")
url0 = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/incidence-7-14-cr.csv"
df0 = pd.read_csv(url0, delimiter=",")

# read data from 'origin.csv' (geometries)
origin = pd.read_csv("kraje/origin.csv")

# basics
data = origin

data['datum'] = f'{last_day.day}. {last_day.month}.'
last_day_7 = last_day + datetime.timedelta(days=-7)
last_date_7 = last_day_7.isoformat()
data['datum-7'] = f'{last_day_7.day}. {last_day_7.month}.'

last_incidence = round(df0[df0['datum'] == last_date]['incidence_7_100000'].reset_index()['incidence_7_100000'][0])
today_title = 'dnes (ČR: ' + str(last_incidence) + ')'

# prepare empty
data[today_title] = 0
data['dnes'] = 0
data['dnes-7'] = 0
data['změna'] = 0

# pivot table
pt = pd.pivot_table(df, index='kraj_nuts_kod', columns='datum', values='incidence_7_100000', fill_value=0).reset_index().rename(columns={'kraj_nuts_kod': 'kód'})

# add today
data[today_title] = pt[last_date]
data['dnes'] = pt[last_date]
data['dnes-7'] = pt[last_date_7]
data['změna'] = pt[last_date] - pt[last_date_7]

# change dates names
dates = pt.columns[1:]
pt.columns = ['kód'] + [(lambda x: datetime.datetime.fromisoformat(x).strftime('%-d.%-m.%y'))(x) for x in dates]

# result
data = data.merge(pt, how='left', on='kód')

data.to_csv("kraje/table.csv", index=False, decimal=",", float_format="%.1f")
