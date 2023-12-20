"""Prepare data from UZIS for maps."""

import datetime
import pandas as pd

localpath = "v3/kraje/"

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
origin = pd.read_csv(localpath + "regions_origin.csv")

# format of the data:
# columns from origin, datum, datum-7, dnes, dnes-7, změna, počet, week_0, ... week_52,
# 20.12.22 (Tue + 1 year ago), ...11.12.23 (Tue), 12.12.23, 13.12.23, ... 19.12.22 (Tue)

# basics
data = origin
data.index = data['kód']

data['datum'] = f'{last_day.day}. {last_day.month}. {last_day.year}'
last_day_7 = last_day + datetime.timedelta(days=-7)
last_date_7 = last_day_7.isoformat()
data['datum-7'] = f'{last_day_7.day}. {last_day_7.month}. {last_day_7.year}'

last_incidence = round(df0[df0['datum'] == last_date]['incidence_7_100000'].reset_index()['incidence_7_100000'][0], 1)
today_title = 'dnes (ČR: ' + str(last_incidence).replace('.', ',') + ')'

# prepare empty
data[today_title] = 0
data['dnes'] = 0
data['dnes-7'] = 0
data['změna'] = 0

# pivot table
pt = pd.pivot_table(df, index='kraj_nuts_kod', columns='datum', values='incidence_7_100000', fill_value=0).reset_index().rename(columns={'kraj_nuts_kod': 'kód'})
pt.index = pt['kód']

# add today
data[today_title] = round(pt[last_date], 1)
data['dnes'] = round(pt[last_date], 1)
data['dnes-7'] = round(pt[last_date_7], 1)
data['změna'] = round(pt[last_date] - pt[last_date_7], 1)

# get only once a week from the last year and the whole last week
dates = pt.columns[1:].to_list()
days = [datetime.datetime.fromisoformat(x).date() for x in dates]

last_day_dow = last_day.weekday()
one_year_ago = last_day + datetime.timedelta(days=-365)
last_year_weeks_days = [x for x in days if (x >= one_year_ago and x.weekday() == last_day_dow)]
last_year_weeks_dates = [x.isoformat() for x in last_year_weeks_days][:-1]
# add last week
last_week_days = sorted([last_day + datetime.timedelta(days=-x) for x in range(0, 8)])
last_week_dates = sorted([x.isoformat() for x in last_week_days])

# add last year weeks into the data for the chart
for i in range(0, len(last_year_weeks_dates)):
  data["week_" + str(i)] = (pt[last_year_weeks_dates[i]] / pt.loc[:, last_year_weeks_dates].max(axis=1) * 100).round().astype(int)

# add last year and last week into the data for the map
for i in range(0, len(last_year_weeks_dates)):
  data[last_year_weeks_days[i].strftime('%-d.%-m.%y')] = pt[last_year_weeks_dates[i]].round(1)
for i in range(0, len(last_week_dates)):
  data[last_week_days[i].strftime('%-d.%-m.%y')] = pt[last_week_dates[i]].round(1)

# save data
data.to_csv(localpath + "table.csv", index=False, decimal=",", float_format="%.1f")
