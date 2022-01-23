"""Update data, if new data exists."""

import datetime
import io
import numpy as np
import os
import pandas as pd
import re
import requests
import shutil
import zipfile

path = "obce_vaccination/"

url = "https://api.github.com/repos/HlidacStatu/UZIS_COVID_DATA/contents"
url_public = "https://github.com/HlidacStatu/UZIS_COVID_DATA/raw/main/"

last_days = 3

# chart width parameter (%)
chart_width = 75
min_dist = 10

origin = pd.read_csv(path + 'origin.csv')
data = pd.read_csv(path + "data.csv")

age_labels = ['0-15', '16-29', '30-49', '50-59', '60-69', '70-79', '80+']

today = datetime.date.today()
days = [today - datetime.timedelta(days=x) for x in range(0, last_days)]

# last existing date in data
last_date = datetime.datetime.strptime(data.columns[-1], "%d.%m.%y").strftime("%Y-%m-%d")

existing = []
for day in days:
    hsdate = datetime.date.strftime(day, "%Y-%m-%d")
    if hsdate > last_date:
        # if obce vaccination data exists

      r1 = requests.get(url + "/" + hsdate)
      if r1.status_code == 200:
        j1 = r1.json()

        for k in j1:
            if ('dle_obc' in k['name'].lower()) and ('01_' in k['name'].lower()) and (('.xlsx' in k['name'].lower()) or ('.zip' in k['name'].lower())):
                fpath = hsdate + '/' + k['name']
                if '/03_' not in fpath:
                    existing.append(fpath)
                    print(fpath)

# for existing obce vaccination files
for ex in existing:
    print(ex)
    r2 = requests.get(url_public  + ex)

    # save zip files
    if r2.ok:
        if '.zip' in ex:
            z = zipfile.ZipFile(io.BytesIO(r2.content))
            z.extractall(path + 'temp/')
        else:
            name = ex.split('/')[-1]
            with open(path + 'temp/' + name, 'wb') as f:
                f.write(r2.content)

    # read excel
    fnames = os.listdir(path + 'temp/')
    for fname in fnames:
        if 'obc' in fname:
            # vaccinated
            # pd.ExcelFile(path + 'temp/' + fname).sheet_names
            datavac = pd.read_excel(path + 'temp/' + fname, sheet_name='Očko obce', header=2)
            datavac = datavac[datavac['ObecKod'] != 'CELKEM']
            # datanon = pd.read_excel(path + 'temp/' + fname, sheet_name='Neočko obce', header=2)
            # datanon = datanon[datanon['ObecKod'] != 'CELKEM']

            datavac_header = pd.read_excel(path + 'temp/' + fname, sheet_name='Očko obce', header=1).columns.tolist()
            # datanon_header = pd.read_excel(path + 'temp/' + fname, sheet_name='Neočko obce', header=1).columns.tolist()

    # data
    date = datetime.datetime.strptime(re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', datavac_header[0]).group(0), '%d.%m.%Y').strftime('%Y-%m-%d')
    
    datavac.rename(columns={'ObecKod': 'code', 'neočkovaní': 'unvaccinated_16+', 'neočkovaní.5': 'unvaccinated_0-16'}, inplace=True)
    datavac['unvaccinated'] = datavac['unvaccinated_16+'] + datavac['unvaccinated_0-16']

    newly = datavac.loc[:, ['code', 'unvaccinated']]

    newly = origin.merge(newly, on='code', how='left')
    newly['population'] = newly['počet obyv.'].apply(lambda x: int(x.replace(' ', '')))
    newly['vaccinated_' + date] = round(((newly['population'] - newly['unvaccinated']) / newly['population']) * 1000) / 10

    data = data.merge(newly.loc[:, ['code', 'vaccinated_' + date]], on='code', how='left')

    # remove files
    shutil.rmtree(path + 'temp/')
    os.makedirs(path + 'temp/')

# set the first variables (dnes, ...)
if len(existing) > 0:
    # rename dnes
    for c in data.columns:
        if 'dnes: ' in c:
            data.rename(columns={c: 'dnes2'}, inplace=True)

    # set the first variables (dnes, ...)
    newly['vaccinated'] = (newly['population'] - newly['unvaccinated'])
    cz = round(newly['vaccinated'].sum() / newly['population'].sum() * 1000) / 10

    data = data.merge(newly.loc[:, ['code', 'population']], on='code', how='left')
    data['datum'] = datetime.datetime.fromisoformat(date).strftime('%-d. %-m. %Y')
    data['absolutně'] = data['population'] - data['vaccinated_' + date]
    data = data.merge(newly.loc[:, ['code', 'vaccinated']], on='code', how='left')
    data['absolutně'] = data['vaccinated'].astype(pd.Int64Dtype())
    data['dnes'] = data['vaccinated_' + date]
    data['dnes2'] = data['vaccinated_' + date]
    data.rename(columns={'dnes2': 'dnes: ČR ' + str(cz) + ' %'}, inplace=True)
    del data['vaccinated']
    del data['population']

# set labels
if len(existing) > 0:
    r2 = requests.get(url_public  + ex)
    if r2.ok:
        z = zipfile.ZipFile(io.BytesIO(r2.content))
        z.extractall(path + 'temp/')

    fnames = os.listdir(path + 'temp/')
    for fname in fnames:
        if 'obc' in fname:
            datavac = pd.read_excel(path + 'temp/' + fname, sheet_name='Očko obce', header=2)
            datavac = datavac[datavac['ObecKod'] != 'CELKEM']
            datanon = pd.read_excel(path + 'temp/' + fname, sheet_name='Neočko obce', header=2)
            datanon = datanon[datanon['ObecKod'] != 'CELKEM']

            datavac_header = pd.read_excel(path + 'temp/' + fname, sheet_name='Očko obce', header=1).columns.tolist()
            datanon_header = pd.read_excel(path + 'temp/' + fname, sheet_name='Neočko obce', header=1).columns.tolist()

    age_labels = ['0-15', '16-29', '30-49', '50-59', '60-69', '70-79', '80+']
    age_labels_info = [
        {'label': '0-15', 'sheet': 'datavac', 'position': 5},
        {'label': '16-29', 'sheet': 'datavac', 'position': 4},
        {'label': '30-49', 'sheet': 'datavac', 'position': 3},
        {'label': '50-59', 'sheet': 'datavac', 'position': 2},
        {'label': '60-69', 'sheet': 'datanon', 'position': 1},
        {'label': '70-79', 'sheet': 'datanon', 'position': 2},
        {'label': '80+', 'sheet': 'datanon', 'position': 3}
    ]

    newly = datavac.loc[:, ['ObecKod', 'Obec']].rename(columns={'ObecKod': 'code'})
    for age in age_labels_info:
        if age['sheet'] == 'datavac':
            d = datavac
            pos_pop = age['position']
            pos_val = age['position']
        else:
            d = datanon
            pos_pop = age['position']
            pos_val = age['position'] * 2 + 1
        newly['xchart_level_0_' + age['label']] = round(d['neočkovaní.' + str(pos_val)] / d['populace.' + str(pos_pop)] * chart_width).replace(np.inf, 0)
        newly['xchart_level_1_' + age['label']] = (chart_width - newly['xchart_level_0_' + age['label']]).fillna(0).astype(int)
        newly['xchart_level_0_' + age['label']] = newly['xchart_level_0_' + age['label']].fillna(0).astype(int)
        newly['xchart_level_1_' + age['label'] + '_desc'] = (100 - round(d['neočkovaní.' + str(pos_val)] / d['populace.' + str(pos_pop)] * 100)).replace(np.inf, 0).fillna(0)
        newly['xchart_level_1_' + age['label'] + '_desc'] = newly['xchart_level_1_' + age['label'] + '_desc'].apply(lambda x: np.NaN if x < min_dist else x).astype(pd.Int64Dtype())

    del newly['Obec']

    # replace in data
    data = data.merge(newly, on='code', how='left')

    for age_label in age_labels:
        data['chart_level_0_' + age_label] = data['xchart_level_0_' + age_label].astype(pd.Int64Dtype())
        data['chart_level_1_' + age_label] = data['xchart_level_1_' + age_label].astype(pd.Int64Dtype())
        data['chart_level_1_' + age_label + '_desc'] = data['xchart_level_1_' + age_label + '_desc'].astype(pd.Int64Dtype())
        del data['xchart_level_0_' + age_label]
        del data['xchart_level_1_' + age_label]
        del data['xchart_level_1_' + age_label + '_desc']

    # remove files
    shutil.rmtree(path + 'temp/')
    os.makedirs(path + 'temp/')

# save file
if len(existing) > 0:
    datax = data.copy()
    for c in datax.columns:
        if 'vaccinated' in c:
            nc = datetime.datetime.fromisoformat(c.split('_')[1]).strftime('%-d.%-m.%y')
            datax.rename(columns={c: nc}, inplace=True)

    datax.to_csv(path + 'data.csv', index=False)