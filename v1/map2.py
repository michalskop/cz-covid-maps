"""Prepare data from UZIS for maps and table."""

import csv
import datetime
import locale
import numpy as np
import pandas as pd

# parameters: last date, tooltips length
# last_date = '2020-11-12'
tooltip_delay = 3
table_delay = 14

# last date
today = datetime.date.today()
last_day = today + datetime.timedelta(days=-1)
last_date = last_day.isoformat()

# set Czech locale
# locale.setlocale(locale.LC_ALL, 'cs_CZ.UTF-8')

# read data from UZIS
# url = "https://share.uzis.cz/s/dCZBiARJ27ayeoS/download?path=%2F&files=obec.csv"
url = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/obce.csv"
# url = "/home/michal/Downloads/obce.csv"
df = pd.read_csv(url, delimiter=",")

# remove non existing Brdy and 999999
df = df[df.obec_kod != 539996]
df = df[df.obec_kod != 999999]

# vojenske ujezdy
vu_codes = [545422, 592935, 555177, 503941]

# len(df.index)

# read data from 'origin.csv' (geometries)
origin = pd.read_csv("pretty_municipalities.csv")
# origin = origin.drop(["datum"], axis=1)

# set dates
first_date = '2020-09-01'
last_day = datetime.datetime.fromisoformat(last_date)
first_day = datetime.datetime.fromisoformat(first_date)
last_date_name = ''

# parts of final file:
tooltips_dates = origin[['code']]
tooltips_values = origin[['code']]
tooltips2_values = origin[['code']]
densities = origin[['code']]
currents = origin[['code']]
table = origin[['code']]
table_values = origin[['code']]


# for each date
for i in range(0, (last_day - first_day).days + 1):
    # last 7 days, density
    previous_week = []
    day = first_day + datetime.timedelta(days=i)
    for j in range(0, 7):
        previous_week.append((day - datetime.timedelta(days=j)).isoformat()[0:10])
    pivot = pd.pivot_table(df[df.datum.isin(previous_week)], values='nove_pripady', index=['obec_kod', 'obec_nazev'], aggfunc=np.sum)
    joined = pivot.join(origin.set_index('code'), on='obec_kod')
    joined['density'] = round(joined['nove_pripady'] / joined['population'] * 100000 * 10) / 10
    # merge to densities
    densities = densities.merge(joined['density'].to_frame(), left_on='code', right_on='obec_kod')
    # format column
    densities['density'] = densities['density'].apply(lambda x: "{:,}".format(x).replace(',', ' ').replace('.', ','))
    # rename column to date
    formatted_day = f'{day.day}.{day.month}.{day.strftime("%y")}'
    formatted_day2 = f'{day.day}. {day.month}. {day.strftime("%y")}'
    densities = densities.rename(columns={'density': formatted_day})
    last_date_name = formatted_day
    last_date_name2 = formatted_day2

    # currents
    cdf = df[df['datum']==day.isoformat()[0:10]]
    cdf = cdf.set_index('obec_kod')
    cdf = cdf.join(origin.set_index('code'), on='obec_kod')
    cdf['current_density'] = round(cdf['aktivni_pripady'] / cdf['population'] * 100000 * 10) / 10
    currents = currents.merge(cdf['current_density'].to_frame(), left_on='code', right_on='obec_kod')
    currents['current_density'] = currents['current_density'].apply(lambda x: "{:,}".format(x).replace(',', ' ').replace('.', ','))
    currents = currents.rename(columns={'current_density': formatted_day})

    # table
    if last_day.weekday() == day.weekday():
        table = table.merge(pivot['nove_pripady'], left_on="code", right_on="obec_kod")
        # table['nove_pr']
        table = table.rename(columns={'nove_pripady': formatted_day})

    # tooltip values, dates
    delay = (last_day - first_day).days - i
    if delay < tooltip_delay:
        tooltips_dates['date_' + str(delay)] =  f'{day.day}.{day.month}.'
        # values and rename
        tooltips_values = tooltips_values.merge(joined['nove_pripady'].to_frame(), left_on='code', right_on='obec_kod')
        tooltips_values['nove_pripady'] = tooltips_values['nove_pripady'].apply(lambda x: "{:,}".format(x).replace(',', ' ').replace('.', ','))
        tooltips_values = tooltips_values.rename(columns={'nove_pripady': 'value_' + str(delay)})
        # current values and rename
        tooltips2_values = tooltips2_values.merge(cdf['aktivni_pripady'].to_frame(), left_on='code', right_on='obec_kod')
        tooltips2_values['aktivni_pripady'] = tooltips2_values['aktivni_pripady'].apply(lambda x: "{:,}".format(x).replace(',', ' ').replace('.', ','))
        tooltips2_values = tooltips2_values.rename(columns={'aktivni_pripady': 'value_' + str(delay)})
    
    # table delay (prevalence)
    if delay < table_delay:
        table_values = table_values.merge(cdf['aktivni_pripady'], left_on="code", right_on="obec_kod")
        table_values = table_values.rename(columns={'aktivni_pripady': formatted_day2})




# PUTTING TOGETHER WEEKLY
# origin
# data = origin[['geometry', 'code', 'obec']]
data = origin[['code', 'pretty_name']]
data = data.rename(columns={'pretty_name': 'obec'})
data = data.set_index('code', drop=False)
data.index.name = None
# tooltips
data = data.merge(tooltips_dates, left_on='code', right_on='code')
data = data.merge(tooltips_values, left_on='code', right_on='code')
# tooltips last density, population
densities = densities.set_index('code')
data = data.merge(densities[last_date_name].to_frame(), left_on='code', right_on='code')
data = data.rename(columns={last_date_name: 'týdenní přírůstek na 100 tis. obyvatel'})
origin = origin.set_index('code', drop=False)
data = data.merge(origin['population'].to_frame(), left_on='code', right_on='code')
# today, densities
data = data.merge(densities[last_date_name].to_frame(), left_on='code', right_on='code')
data = data.rename(columns={last_date_name: 'dnes'})
data = data.merge(densities, left_on='code', right_on='code')
data['population'] = data['population'].apply(lambda x: "{:,}".format(x).replace(',', ' ').replace('.', ','))
# remove vojenské újezdy
# for vuc in vu_codes:
#     data = data[data.code != vuc]

data = data.rename(columns={'population': 'počet obyv.'})
data.to_csv("weekly.csv", index=False, decimal=",", float_format="%.1f")

# PUTTING TOGETHER CURRENT
# origin
# data = origin[['geometry', 'code', 'obec']]
data = origin[['code', 'pretty_name']]
data = data.rename(columns={'pretty_name': 'obec'})
data = data.set_index('code', drop=False)
data.index.name = None
# tooltips
data = data.merge(tooltips_dates, left_on='code', right_on='code')
data = data.merge(tooltips2_values, left_on='code', right_on='code')
# tooltips last density, population
currents = currents.set_index('code')
data = data.merge(currents[last_date_name].to_frame(), left_on='code', right_on='code')
data = data.rename(columns={last_date_name: 'aktuálně nemocných na 100 tis. obyvatel'})
# origin = origin.set_index('code', drop=False)
data = data.merge(origin['population'].to_frame(), left_on='code', right_on='code')
# today, currents densities
data = data.merge(currents[last_date_name].to_frame(), left_on='code', right_on='code')
data = data.rename(columns={last_date_name: 'dnes'})
data = data.merge(currents, left_on='code', right_on='code')
data['population'] = data['population'].apply(lambda x: "{:,}".format(x).replace(',', ' ').replace('.', ','))
# remove vojenské újezdy
# for vuc in vu_codes:
#     data = data[data.code != vuc]

data = data.rename(columns={'population': 'počet obyv.'})
data.to_csv("current.csv", index=False, decimal=",", float_format="%.1f")

# PUTTING TOGETHER TABLE
data = origin[['pretty_name', 'code', 'population']]
data = data.set_index('code', drop=False)
data.index.name = None
table = table.set_index('code')
table_values = table_values.set_index('code')
# replace negative values by 0
table = table.mask(table < 0, 0)
table_values = table_values.mask(table_values < 0, 0)
# today, current prevalence
data = data.merge(table_values[last_date_name2].to_frame(), left_on='code', right_on='code')
data = data.rename(columns={last_date_name2: "prevalence"})
data['/100 tis.'] = round(data['prevalence'] / data['population'] * 100000).fillna(0).replace(np.inf, 0).apply(lambda x: int(x))
data = data.merge(table_values, left_on='code', right_on='code')
# today, incidence
data = data.merge(table[last_date_name].to_frame(), left_on='code', right_on='code')
data = data.rename(columns={last_date_name: "incidence 7d"})
data['/100tis.'] = round(data['incidence 7d'] / data['population'] * 100000).fillna(0).replace(np.inf, 0).apply(lambda x: int(x))
data = data.merge(table, left_on='code', right_on='code')
# renaming columns
data = data.rename(columns={'population': 'počet obyv.', 'pretty_name': 'obec'})
# remove vojenské újezdy
for vuc in vu_codes:
    data = data[data.code != vuc]
# save
data.to_csv("table.csv", index=False, decimal=",", float_format="%.1f")

# locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
