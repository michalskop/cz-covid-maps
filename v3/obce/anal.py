"""Prepare data from UZIS for maps and table - obce."""

import datetime
import pandas as pd

localpath = "v3/obce/"

# last date
today = datetime.date.today()
last_day = today + datetime.timedelta(days=-1)
last_date = last_day.isoformat()

# read data from UZIS
url = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/obce.csv"
df = pd.read_csv(url, delimiter=",")
url0 = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/incidence-7-14-cr.csv"
df0 = pd.read_csv(url0, delimiter=",")

# read data from 'origin.csv'
origin = pd.read_csv(localpath + "origin.csv")

# remove non existing Brdy and 999999 and NA
df = df[df.obec_kod != 539996]
df = df[df.obec_kod != 999999]
df = df[~df['obec_kod'].isna()]

# vojenske ujezdy
vu_codes = [545422, 592935, 555177, 503941]

# reorder data
sincidence = pd.pivot_table(df, index=['obec_kod'], columns=['datum'], values=['nove_pripady_7_dni']).reset_index()
sincidence.columns = sincidence.columns.droplevel(0)
sincidence.rename(columns={'': 'kód'}, inplace=True)
sincidence.index = sincidence['kód']

# prepare data for output - incidence
data = origin.copy()
data.index = data['code']

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

# get only once a week from the last year and the whole last week
dates = sincidence.columns[1:].to_list()
days = [datetime.datetime.fromisoformat(x).date() for x in dates]

last_day_dow = last_day.weekday()
one_year_ago = last_day + datetime.timedelta(days=-365)
last_year_weeks_days = [x for x in days if (x >= one_year_ago and x.weekday() == last_day_dow)]
last_year_weeks_dates = [x.isoformat() for x in last_year_weeks_days][:-2]
# add last week
last_week_days = sorted([last_day + datetime.timedelta(days=-x) for x in range(0, 8)])
last_week_dates = sorted([x.isoformat() for x in last_week_days])

# add last year weeks into the data for the chart
for i in range(0, len(last_year_weeks_dates)):
  data["week_" + str(i)] = (sincidence[last_year_weeks_dates[i]] / sincidence.loc[:, last_year_weeks_dates].max(axis=1) * 100).round().fillna(0).astype(int)

# add last year and last week into the data for the map
for i in range(0, len(last_year_weeks_dates)):
  data[last_year_weeks_days[i].strftime('%-d.%-m.%y')] = sincidence[last_year_weeks_dates[i]].round(1) / data['počet obyv.'].str.replace('\s+', '').astype(int) * 100000
for i in range(0, len(last_week_dates)):
  data[last_week_days[i].strftime('%-d.%-m.%y')] = sincidence[last_week_dates[i]].round(1) / data['počet obyv.'].str.replace('\s+', '').astype(int) * 100000

# add today
data[today_title] = round(sincidence[last_date], 1) / data['počet obyv.'].str.replace('\s+', '').astype(int) * 100000
data['dnes'] = round(sincidence[last_date], 1) / data['počet obyv.'].str.replace('\s+', '').astype(int) * 100000
data['dnes-7'] = round(sincidence[last_date_7], 1) / data['počet obyv.'].str.replace('\s+', '').astype(int) * 100000
data['změna'] = round(sincidence[last_date] - sincidence[last_date_7], 1) / data['počet obyv.'].str.replace('\s+', '').astype(int) * 100000

# save data
data.to_csv(localpath + "incidence.csv", index=False)
