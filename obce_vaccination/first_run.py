"""First run, get all existing data."""

import datetime
import io
from unicodedata import name
import numpy as np
import os
import pandas as pd
import re
import requests
import shutil
import obce_vaccination.settings as settings
import zipfile

path = "obce_vaccination/"

start_date = '2021-06-01'

# origin
origin = pd.read_csv(path + 'origin.csv')
data = origin.copy()

data['kraj'] = np.nan
data['datum'] = np.nan
data['absolutně'] = np.nan
data['dnes'] = np.nan
data['dnes2'] = np.nan

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

    newly = datavac.loc[:, ['code', 'unvaccinated']]

    newly = origin.merge(newly, on='code', how='left')
    newly['population'] = newly['počet obyv.'].apply(lambda x: int(x.replace(' ', '')))
    newly['vaccinated_' + date] = round(((newly['population'] - newly['unvaccinated']) / newly['population']) * 1000) / 10

    data = data.merge(newly.loc[:, ['code', 'vaccinated_' + date, 'Kraj']], on='code', how='left')

    # remove files
    shutil.rmtree(path + 'temp/')
    os.makedirs(path + 'temp/')

newly['vaccinated'] = (newly['population'] - newly['unvaccinated'])
cz = round(newly['vaccinated'].sum() / newly['population'].sum() * 1000) / 10

data = data.merge(newly.loc[:, ['code', 'Kraj']], on='code', how='left')
data['kraj'] = data['Kraj']
del data['Kraj']
data['datum'] = datetime.datetime.fromisoformat(date).strftime('%-d. %-m. %Y')
data['absolutně'] = data['population'] - data['vaccinated_' + date]
data = data.merge(newly.loc[:, ['code', 'vaccinated','vaccinated_' + date]], on='code', how='left')
data['absolutně'] = data['vaccinated']
data['dnes'] = data['vaccinated_' + date]
data['dnes2'] = data['vaccinated_' + date]
data.rename(columns={'dnes2': 'dnes: ČR ' + str(cz) + ' %'}, inplace=True)
del data['vaccinated']

datax = data.copy()
for c in datax.columns:
    if 'vaccinated' in c:
        nc = datetime.datetime.fromisoformat(c.split('_')[1]).strftime('%-d.%-m.%y')
        datax.rename(columns={c: nc}, inplace=True)

datax.to_csv(path + 'data.csv', index=False)

# test
