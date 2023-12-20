"""Creates SZ maps with ORP."""

import datetime
import pandas as pd

localpath = "v3/orp/"

# last date
today = datetime.date.today()
last_day = today + datetime.timedelta(days=-1)
last_date = last_day.isoformat()

# read data from UZIS
url = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/orp.csv"
df = pd.read_csv(url, delimiter=",")
urlp = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/mestske-casti.csv"
dfp = pd.read_csv(urlp, delimiter=",")
url0 = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/incidence-7-14-cr.csv"
df0 = pd.read_csv(url0, delimiter=",")
url0p = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/zakladni-prehled.csv"
df0p = pd.read_csv(url0p, delimiter=",")

# read data from 'origin.csv'
origin = pd.read_csv(localpath + "origin.csv")

# reorder data
sincidence = pd.pivot_table(df, index=['orp_kod'], columns=['datum'], values=['incidence_7']).reset_index()
sprevalence = pd.pivot_table(df, index=['orp_kod'], columns=['datum'], values=['prevalence']).reset_index()

sincidence.columns = sincidence.columns.droplevel(0)
sincidence.rename(columns={'': 'kód'}, inplace=True)
sincidence = sincidence[sincidence['kód'] != 0]
sprevalence.columns = sprevalence.columns.droplevel(0)
sprevalence.rename(columns={'': 'kód'}, inplace=True)
sprevalence = sprevalence[sprevalence['kód'] != 0]

# add Praha
pincidence = pd.pivot_table(dfp, index=['orp_kod'], columns=['datum'], values=['nove_pripady_7_dni']).reset_index().sum()
pincidence = pd.DataFrame(pincidence).T.droplevel(0, axis=1)
pincidence.rename(columns={'': 'kód'}, inplace=True)
pincidence['kód'] = 1000
xincidence = pd.concat([pincidence, sincidence], axis=0)
xincidence.index = xincidence['kód']

pprevalence = pd.pivot_table(dfp, index=['orp_kod'], columns=['datum'], values=['aktivni_pripady']).reset_index().sum()
pprevalence = pd.DataFrame(pprevalence).T.droplevel(0, axis=1)
pprevalence.rename(columns={'': 'kód'}, inplace=True)
pprevalence['kód'] = 1000
xprevalence = pd.concat([pprevalence, sprevalence], axis=0)
xprevalence.index = xprevalence['kód']

# prepare data for output - incidence
data = origin.copy()
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

# get only once a week from the last year and the whole last week
dates = xincidence.columns[1:].to_list()
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
  data["week_" + str(i)] = (xincidence[last_year_weeks_dates[i]] / xincidence.loc[:, last_year_weeks_dates].max(axis=1) * 100).round().astype(int)

# add last year and last week into the data for the map
for i in range(0, len(last_year_weeks_dates)):
  data[last_year_weeks_days[i].strftime('%-d.%-m.%y')] = xincidence[last_year_weeks_dates[i]].round(1) / data['počet obyv.'] * 100000
for i in range(0, len(last_week_dates)):
  data[last_week_days[i].strftime('%-d.%-m.%y')] = xincidence[last_week_dates[i]].round(1) / data['počet obyv.'] * 100000

# add today
data[today_title] = round(xincidence[last_date], 1) / data['počet obyv.'] * 100000
data['dnes'] = round(xincidence[last_date], 1) / data['počet obyv.'] * 100000
data['dnes-7'] = round(xincidence[last_date_7], 1) / data['počet obyv.'] * 100000
data['změna'] = round(xincidence[last_date] - xincidence[last_date_7], 1) / data['počet obyv.'] * 100000

# save data
data.to_csv(localpath + "incidence.csv", index=False, decimal=',', float_format="%.1f")

# prepare data for output - prevalence
data = origin.copy()
data.index = data['kód']

data['datum'] = f'{last_day.day}. {last_day.month}. {last_day.year}'
last_day_7 = last_day + datetime.timedelta(days=-7)
last_date_7 = last_day_7.isoformat()
data['datum-7'] = f'{last_day_7.day}. {last_day_7.month}. {last_day_7.year}'
last_prevalence = round(df0p['aktivni_pripady'][0] / origin['počet obyv.'].sum() * 100000, 1)
today_title = 'dnes (ČR: ' + str(last_prevalence).replace('.', ',') + ')'

# prepare empty
data[today_title] = 0
data['dnes'] = 0
data['dnes-7'] = 0
data['změna'] = 0

# get only once a week from the last year and the whole last week
dates = xprevalence.columns[1:].to_list()
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
  data["week_" + str(i)] = (xprevalence[last_year_weeks_dates[i]] / xprevalence.loc[:, last_year_weeks_dates].max(axis=1) * 100).round().astype(int)

# add last year and last week into the data for the map
for i in range(0, len(last_year_weeks_dates)):
  data[last_year_weeks_days[i].strftime('%-d.%-m.%y')] = xprevalence[last_year_weeks_dates[i]].round(1) / data['počet obyv.'] * 100000
for i in range(0, len(last_week_dates)):
  data[last_week_days[i].strftime('%-d.%-m.%y')] = xprevalence[last_week_dates[i]].round(1) / data['počet obyv.'] * 100000

# add today
data[today_title] = round(xprevalence[last_date], 1) / data['počet obyv.'] * 100000
data['dnes'] = round(xprevalence[last_date], 1) / data['počet obyv.'] * 100000
data['dnes-7'] = round(xprevalence[last_date_7], 1) / data['počet obyv.'] * 100000
data['změna'] = round(xprevalence[last_date] - xprevalence[last_date_7], 1) / data['počet obyv.'] * 100000

# save data
data.to_csv(localpath + "prevalence.csv", index=False, decimal=',', float_format="%.1f")

