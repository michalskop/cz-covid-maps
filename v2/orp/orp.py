"""Creates SZ maps with ORP."""

# https://app.flourish.studio/visualisation/7917801/
# https://app.flourish.studio/visualisation/7917809/

import datetime
# import numpy as np
import pandas as pd

# resolve path
import sys
sys.path.insert(0, 'orp/')
try:
    import settings
    path = settings.path() + "orp/"
except ImportError:
    path = "orp/"

# get data
data = pd.read_csv(path + "orps.csv")
source = pd.read_csv("https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/orp.csv")

# reorder data
sincidence = pd.pivot_table(source, index=['orp_kod'], columns=['datum'], values=['incidence_7']).reset_index()
sprevalence = pd.pivot_table(source, index=['orp_kod'], columns=['datum'], values=['prevalence']).reset_index()

sincidence.columns = sincidence.columns.droplevel(0)
sincidence.rename(columns={'': 'kód'}, inplace=True)
sprevalence.columns = sprevalence.columns.droplevel(0)
sprevalence.rename(columns={'': 'kód'}, inplace=True)

# all dates
isodates = sincidence.columns.tolist()[1:]
dates = []
for d in isodates:
    # This only works on Unix (Linux, OS X), not Windows (including Cygwin). On Windows, you would use #, e.g. %Y/%#m/%#d."
    dates.append(datetime.datetime.fromisoformat(d).strftime('%-d.%-m.%y'))

# merge data + source
datai = data.merge(sincidence, how='left', on='kód')
datap = data.merge(sprevalence, how='left', on='kód')

# incidence
incidence = pd.DataFrame()
incidence['geometry'] = datai['geometry']
incidence['datum'] = [datetime.datetime.fromisoformat(isodates[-2]).strftime('%-d. %-m. %Y')] * len(datai)
incidence['kód'] = datai['kód']
incidence['obec'] = datai['obec']
incidence['aktuálně covid+'] = datap[isodates[-2]]
incidence['aktuálně na 100k'] = (datap[isodates[-2]] / datap['population_2021'] * 100000).round(1)
incidence['7 covid+'] = datai[isodates[-2]]
incidence['7 na 100k'] = (datai[isodates[-2]] / datai['population_2021'] * 100000).round(1)
incidence['dnes'] = incidence['7 na 100k']

t = (datai.iloc[:, 4:-1].div(datai['population_2021'], axis=0) * 100000).round(1)
t.columns = dates[:-1]
incidence = pd.concat([incidence, t], axis=1)

# incidence.sort_values(by=['obec'], inplace=True)
incidence.to_csv(path + "incidence.csv", index=False, decimal=',')

# prevalence
prevalence = pd.DataFrame()
prevalence['geometry'] = datap['geometry']
prevalence['datum'] = [datetime.datetime.fromisoformat(isodates[-2]).strftime('%-d. %-m. %Y')] * len(datap)
prevalence['kód'] = datap['kód']
prevalence['obec'] = datap['obec']
prevalence['aktuálně covid+'] = datap[isodates[-2]]
prevalence['aktuálně na 100k'] = (datap[isodates[-2]] / datap['population_2021'] * 100000).round(1)
prevalence['7 covid+'] = datai[isodates[-2]]
prevalence['7 na 100k'] = (datai[isodates[-2]] / datai['population_2021'] * 100000).round(1)
prevalence['dnes'] = prevalence['aktuálně na 100k']

t = (datap.iloc[:, 4:-1].div(datap['population_2021'], axis=0) * 100000).round(1)
t.columns = dates[:-1]
prevalence = pd.concat([prevalence, t], axis=1)

# prevalence.sort_values(by=['obec'], inplace=True)
prevalence.to_csv(path + "prevalence.csv", index=False, decimal=',')
