"""First run, get all existing data."""

import datetime
import io
import numpy as np
import os
import pandas as pd
import re
import requests
import shutil
import obce_vaccination.settings as settings
import zipfile

path = "obce_vaccination/"

# chart width parameter (%)
chart_width = 75
min_dist = 10

start_date = '2021-06-01'

# origin
origin = pd.read_csv(path + 'origin.csv')
data = origin.copy()

data['kraj'] = np.nan
data['datum'] = np.nan
data['absolutně'] = np.nan
data['dnes'] = np.nan
data['dnes2'] = np.nan

age_labels = ['0-15', '16-29', '30-49', '50-59', '60-69', '70-79', '80+']
for age_label in age_labels:
    data['chart_level_0_' + age_label] = np.nan
for age_label in age_labels:
    data['chart_level_1_' + age_label] = np.nan
for age_label in age_labels:
    data['chart_level_1_' + age_label + '_desc'] = np.nan

# github connections
headers = {
    "Authorization": "token " + settings.GITHUB_TOKEN,
}

url = "https://api.github.com/repos/HlidacStatu/UZIS_COVID_DATA/contents"
url_public = "https://github.com/HlidacStatu/UZIS_COVID_DATA/raw/main/"

# get all directories
r = requests.get(url, headers=headers)

j = r.json()

# existing dates
hsdates = []
for k in j:
    if (k['size'] == 0) and (k['name'] >= start_date):
        hsdates.append(k['name'])

# if obce vaccination data exists
existing = []
for hsdate in hsdates:
    r1 = requests.get(url + "/" + hsdate, headers=headers)
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

    newly = datavac.loc[:, ['code', 'Kraj', 'unvaccinated']]

    newly = origin.merge(newly, on='code', how='left')
    newly['population'] = newly['počet obyv.'].apply(lambda x: int(x.replace(' ', '')))
    newly['vaccinated_' + date] = round(((newly['population'] - newly['unvaccinated']) / newly['population']) * 1000) / 10

    data = data.merge(newly.loc[:, ['code', 'vaccinated_' + date, 'Kraj']], on='code', how='left')

    # remove files
    shutil.rmtree(path + 'temp/')
    os.makedirs(path + 'temp/')

    # remove Krajs
    data['kraj'] = data['Kraj']
    del data['Kraj_x']
    del data['Kraj_y']
    del data['Kraj']

# set the first variables (dnes, ...)
newly['vaccinated'] = (newly['population'] - newly['unvaccinated'])
cz = round(newly['vaccinated'].sum() / newly['population'].sum() * 1000) / 10

data = data.merge(newly.loc[:, ['code', 'population']], on='code', how='left')
data['datum'] = datetime.datetime.fromisoformat(date).strftime('%-d. %-m. %Y')
data['absolutně'] = data['population'] - data['vaccinated_' + date]
data = data.merge(newly.loc[:, ['code', 'vaccinated']], on='code', how='left')
data['absolutně'] = data['vaccinated']
data['dnes'] = data['vaccinated_' + date]
data['dnes2'] = data['vaccinated_' + date]
data.rename(columns={'dnes2': 'dnes: ČR ' + str(cz) + ' %'}, inplace=True)
del data['vaccinated']
del data['population']


# set first labels
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
    data['chart_level_0_' + age_label] = data['xchart_level_0_' + age_label]
    data['chart_level_1_' + age_label] = data['xchart_level_1_' + age_label]
    data['chart_level_1_' + age_label + '_desc'] = data['xchart_level_1_' + age_label + '_desc']
    del data['xchart_level_0_' + age_label]
    del data['xchart_level_1_' + age_label]
    del data['xchart_level_1_' + age_label + '_desc']

# remove files
shutil.rmtree(path + 'temp/')
os.makedirs(path + 'temp/')


# save file
datax = data.copy()
for c in datax.columns:
    if 'vaccinated' in c:
        nc = datetime.datetime.fromisoformat(c.split('_')[1]).strftime('%-d.%-m.%y')
        datax.rename(columns={c: nc}, inplace=True)

datax.to_csv(path + 'data.csv', index=False)

# test
# data.columns