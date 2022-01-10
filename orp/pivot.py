"""Vaccination CZ."""

import datetime
import numpy as np
import pandas as pd

# null after time:
null_after_days = round(365 * 0.75)
today = datetime.date.today()
null_day = today - datetime.timedelta(days=null_after_days)
null_date = null_day.strftime("%Y-%m-%d")

# chart width parameter (%)
chart_width = 75

# last date
# today = datetime.date.today()
last_day = today + datetime.timedelta(days=-1)
last_date = last_day.isoformat()
first_day = today + datetime.timedelta(days=-366)
first_date = first_day.isoformat()

# load data
# https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/ockovani-profese.csv
path = "/home/michal/dev/coronavirus/cz-covid-maps/orp/"
data = pd.read_csv(path + "ockovani-profese.csv")

# print(data['datum_vakcinace'].max())
print(data['datum'].max())

# read data from 'origin.csv' (geometries)
origin = pd.read_csv(path + "origin.csv")
out = origin.copy()

# read data about population
population = pd.read_csv(path + "orp_population_age.csv")

population_bins=[0, 12, 18, 30, 40, 50, 60, 70, 80, 110]

population_labels = ['0-11', '12-17', '18-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+']

# encode population
population['age_group'] = pd.cut(population['age'], bins=population_bins, labels=population_labels, right=False)

# add regions to population
population['region_code'] = round(population['code'] / 100)

# pivot population by age groups
population_pt = population.pivot_table(index=['region_code', 'age_group'], values=['value', 'value_m', 'value_f'], aggfunc=np.sum).reset_index()

population_pto = population.pivot_table(index=['code', 'age_group'], values=['value', 'value_m', 'value_f'], aggfunc=np.sum).reset_index()

population_ptr = population.pivot_table(index=['region_code'], values=['value', 'value_m', 'value_f'], aggfunc=np.sum).reset_index()

population_pto_all = population.pivot_table(index=['code'], values=['value', 'value_m', 'value_f'], aggfunc=np.sum).reset_index()

# Others (than Johnson & Johnson)
data['first_others'] = ((data['poradi_davky'] == 1) & (data['vakcina'] != 'COVID-19 Vaccine Janssen'))
data['second_others'] = ((data['poradi_davky'] == 2) & (data['vakcina'] != 'COVID-19 Vaccine Janssen'))
data['third_others'] = ((data['poradi_davky'] == 3) & (data['vakcina'] != 'COVID-19 Vaccine Janssen'))
# Johnson & Johnson
data['first_janssen'] = ((data['poradi_davky'] == 1) & (data['vakcina'] == 'COVID-19 Vaccine Janssen'))
data['second_janssen'] = ((data['poradi_davky'] == 2) & (data['vakcina'] == 'COVID-19 Vaccine Janssen'))
data['third_janssen'] = ((data['poradi_davky'] == 3) & (data['vakcina'] == 'COVID-19 Vaccine Janssen'))

# recode to our age groups
data['age_group'] = data['vekova_skupina'].replace({
    '12-15': '12-17',
    '16-17': '12-17',
    '18-24': '18-29',
    '25-29': '18-29',
    '30-34': '30-39',
    '35-39': '30-39',
    '40-44': '40-49',
    '45-49': '40-49',
    '50-54': '50-59',
    '55-59': '50-59',
    '60-64': '60-69',
    '65-69': '60-69',
    '70-74': '70-79',
    '75-79': '70-79'
})
# bydliste region_code
data['region_code'] = round(data['orp_bydliste_kod'] / 100)

# weeks
data['week'] = data['datum'].apply(datetime.datetime.fromisoformat).dt.isocalendar().year.astype(str) + '-' + data['datum'].apply(datetime.datetime.fromisoformat).dt.isocalendar().week.map("{:02}".format)

# select weeks from the last year without current week
weeks = sorted(sorted(data['week'].unique(), reverse=True)[1:54])

# prepare
out['datum'] = f'{last_day.day}. {last_day.month}. {last_day.year}'
out['absolutně'] = 0
out['dnes'] = 0
out['dnes 2'] = 0

# total vaccines in week and region for small charts
pt_w = data[data['week'].isin(weeks)].pivot_table(index=['orp_bydliste_kod'], values=['id'], columns=['week'], dropna=False, aggfunc='count').reset_index().replace(np.nan, 0)
pt_w.columns = pt_w.columns.droplevel(0)
pt_w.rename(columns={'': 'kód'}, inplace=True)
pt_w100 = pt_w.loc[:, ['kód']].merge((round(pt_w.loc[:, weeks].divide(pt_w.loc[:, weeks].max(axis=1), axis='index') * 100)).fillna(0).astype(int), left_index=True, right_index=True)
pt_w100 = pt_w100[['kód'] + weeks]
pt_w100.columns = ['kód'] + [(lambda x: ("week_" + str(x)))(x) for x in range(0, len(weeks))]

out = out.merge(pt_w100, on='kód', how='left')

# current data by orp and 1/2/3 and age
groups = ['first_others', 'second_others', 'third_others', 'first_janssen', 'second_janssen', 'third_janssen']

pto = {}
for g in groups:
    pto[g] = data[data['datum'] > null_date].pivot_table(index=["orp_bydliste_kod", 'age_group', g], values='id', aggfunc='count', dropna=False).reset_index().fillna(0).merge(population_pto, how='left', left_on=['orp_bydliste_kod', 'age_group'], right_on=['code', 'age_group'])

level = [0] * 4

level[3] = pto['third_others'][pto['third_others']['third_others']]['id'] + pto['third_janssen'][pto['third_janssen']['third_janssen']]['id'] + pto['second_janssen'][pto['second_janssen']['second_janssen']]['id']
level[2] = (pto['second_others'][pto['second_others']['second_others']]['id'] + pto['first_janssen'][pto['first_janssen']['first_janssen']]['id'] - level[3]).apply(lambda x: max(x, 0))
level[1] = (pto['first_others'][pto['first_others']['first_others']]['id'] - pto['second_others'][pto['second_others']['second_others']]['id']).apply(lambda x: max(x, 0))
level_one_plus = level[3] + level[2] + level[1]
level_two_plus = level[3] + level[2]
level[0] = pto['first_others'][pto['first_others']['first_others']]['value'] - level_one_plus

# current: absolutne, rate, age-specific rates
pto_selected = pto['first_others'][pto['first_others']['first_others']]
# pto_selected['level_one_plus'] = 0
pto_selected['level_two_plus'] = level_two_plus.to_frame()
for i in range(0, 4):
    pto_selected['level_' + str(i)] = level[i].to_frame()

totals = pd.pivot_table(pto_selected, index='code', values=['level_two_plus', 'value'], aggfunc=np.sum)
totals['rate'] = round(totals['level_two_plus'] / totals['value'] * 100, 1)
totals = totals.reset_index()

out['absolutně'] = totals['level_two_plus'].astype(int)
out['dnes'] = totals['rate']
out['dnes 2'] = totals['rate']

ts = totals.sum(axis=0)
total_rate = round(ts['level_two_plus'] / ts['value'] * 100, 1)
out.rename(columns={'dnes 2': 'dnes: ČR ' + str(total_rate) + ' %'}, inplace=True)


pt_chart_levels = []
pt_chart_real_levels = []
for i in range(0, 4):
    c = 'chart_level_' + str(i)
    cr = 'chart_real_level_' + str(i)
    pto_selected[c] = round(pto_selected['level_' + str(i)] / pto_selected['value'] * chart_width)
    pto_selected[cr] = round(pto_selected['level_' + str(i)] / pto_selected['value'] * 100)
    pt_chart_levels.append(c)
    pt_chart_real_levels.append(cr)
# problems with rounds:
pto_selected['chart_level_0'] = chart_width - pto_selected['chart_level_1'] - pto_selected['chart_level_2'] - pto_selected['chart_level_3']

pto_chart = pd.pivot_table(pto_selected, index='code', values=pt_chart_levels, columns='age_group')
pto_chart.columns = pto_chart.columns.get_level_values(0) + '_' +  pto_chart.columns.get_level_values(1)
pto_chart.reset_index(inplace=True)

out = out.join(pto_chart, how='left')
del out['code']

# descriptions
pto_chart_real = pd.pivot_table(pto_selected, index='code', values=pt_chart_real_levels, columns='age_group')
pto_chart_real.columns = pto_chart_real.columns.get_level_values(0) + '_' +  pto_chart_real.columns.get_level_values(1)
pto_chart_real.reset_index(inplace=True)

min_dist = 10

pto_chart_desc = pd.DataFrame(index=pto_chart_real.index)
for pl in population_labels:
    for i in range(3, 0, -1):
        s = 0
        for j in range(3, i - 1, -1):
            s += pto_chart_real['chart_real_level_' + str(j) + '_' + pl]
        pto_chart_desc['chart_level_' + str(i) + '_' + pl + '_desc'] = s

for pl in population_labels:
    pto_chart_desc['chart_level_1_' + pl + '_desc'] = (pto_chart_desc['chart_level_1_' + pl + '_desc'] > (pto_chart_desc['chart_level_2_' + pl + '_desc'] + min_dist)) * pto_chart_desc['chart_level_1_' + pl + '_desc']
    pto_chart_desc['chart_level_2_' + pl + '_desc'] = (pto_chart_desc['chart_level_2_' + pl + '_desc'] > (pto_chart_desc['chart_level_3_' + pl + '_desc'] + min_dist)) * pto_chart_desc['chart_level_2_' + pl + '_desc']

pto_chart_desc[pto_chart_desc < min_dist] = np.NaN

out = out.join(pto_chart_desc, how='left')

# history
since_date = '2021-03-01'
since_day = datetime.date.fromisoformat(since_date)
selected_days = pd.date_range(since_day, today, freq='2W').to_list()
if selected_days[-1].strftime('%Y-%m-%d') != today.strftime('%Y-%m-%d'):
    selected_days.append(today)
for until_day in selected_days:
    until_date = until_day.strftime('%Y-%m-%d')
    null_day = until_day - datetime.timedelta(days=null_after_days)
    null_date = null_day.strftime("%Y-%m-%d")

    pto = {}
    for g in groups:
        pto[g] = data[(data['datum'] > null_date) & (data['datum'] <= until_date)].pivot_table(index=["orp_bydliste_kod", 'age_group', g], values='id', aggfunc='count', dropna=False).reset_index().fillna(0).merge(population_pto, how='left', left_on=['orp_bydliste_kod', 'age_group'], right_on=['code', 'age_group'])

    level = [0] * 4

    level[3] = pto['third_others'][pto['third_others']['third_others']]['id'] + pto['third_janssen'][pto['third_janssen']['third_janssen']]['id'] + pto['second_janssen'][pto['second_janssen']['second_janssen']]['id']
    level[2] = (pto['second_others'][pto['second_others']['second_others']]['id'] + pto['first_janssen'][pto['first_janssen']['first_janssen']]['id'] - level[3]).apply(lambda x: max(x, 0))
    level[1] = (pto['first_others'][pto['first_others']['first_others']]['id'] - pto['second_others'][pto['second_others']['second_others']]['id']).apply(lambda x: max(x, 0))
    level_one_plus = level[3] + level[2] + level[1]
    level_two_plus = level[3] + level[2]
    level[0] = pto['first_others'][pto['first_others']['first_others']]['value'] - level_one_plus

    # current: absolutne, rate, age-specific rates
    pto_selected = pto['first_others'][pto['first_others']['first_others']]
    # pto_selected['level_one_plus'] = 0
    pto_selected['level_two_plus'] = level_two_plus.to_frame()
    for i in range(0, 4):
        pto_selected['level_' + str(i)] = level[i].to_frame()

    totals = pd.pivot_table(pto_selected, index='code', values=['level_two_plus', 'value'], aggfunc=np.sum)
    totals[until_day.strftime('%-d.%-m.%y')] = round(totals['level_two_plus'] / totals['value'] * 100, 1)
    totals = totals.reset_index()
    totals
    out = out.merge(totals.loc[:, [until_day.strftime('%-d.%-m.%y'), 'code']], how='left', left_on='kód', right_on='code')
    del out['code']
    out[until_day.strftime('%-d.%-m.%y')].fillna(0, inplace=True)


out.to_csv(path + 'orp.csv')



# generate html for chart tooltip
li = "<li><span class='party-bar' style='display: inline-block; background-color: #5021AB; width: {{chart_level_3_XXX}}%'><span class='party-desc'>{{chart_level_3_XXX_desc}}&nbsp;</span></span><span class='party-bar' style='display: inline-block; background-color: #63698C; width: {{chart_level_2_XXX}}%'><span class='party-desc'>{{chart_level_2_XXX_desc}}&nbsp;</span></span><span class='party-bar' style='display: inline-block; background-color: #76B7CE; width: {{chart_level_1_XXX}}%'><span  class='party-desc'>{{chart_level_1_XXX_desc}}&nbsp;</span></span><span class='party-bar' style='display: inline-block; background-color: #e2626d; width: {{chart_level_0_XXX}}%'><span  class='party-desc'>&nbsp;</span></span>&nbsp;<span class='party-name'>XXX</span></li>"
tooltip = ''
for k in reversed(population_labels):
    tooltip += li.replace('XXX', k)
    tooltip += "\n"
print(tooltip)

style = ".party-desc {color: #eee; font-size: 0.9em; font-weight: bold; position: relative; bottom: 1px; float: right}"




type(pto_selected)

pto_first_others = data[data['datum'] > null_date].pivot_table(index=["orp_bydliste_kod", 'age_group', 'first_others'], values='id', aggfunc='count', dropna=False).reset_index().fillna(0).merge(population_pto, how='left', left_on=['orp_bydliste_kod', 'age_group'], right_on=['code', 'age_group'])

pto_first_others = data[data['datum'] > null_date].pivot_table(index=["orp_bydliste_kod", 'age_group', 'first_others'], values='id', aggfunc='count', dropna=False).reset_index().fillna(0).merge(population_pto, how='left', left_on=['orp_bydliste_kod', 'age_group'], right_on=['code', 'age_group'])

pto_db = data[data['datum'] > null_date].pivot_table(index=["orp_bydliste_kod", 'age_group', 'booster', 'full', 'first_only'], values='id', aggfunc='count', dropna=False).reset_index().fillna(0).merge(population_pto, how='left', left_on=['orp_bydliste_kod', 'age_group'], right_on=['code', 'age_group'])

pto_db = data[data['datum'] > null_date].pivot_table(index=["orp_bydliste_kod", 'age_group', 'first_others', 'second_others', 'third_others', 'first_janssen', 'second_janssen', 'third_janssen'], values='id', aggfunc='count', dropna=False).reset_index().fillna(0).merge(population_pto, how='left', left_on=['orp_bydliste_kod', 'age_group'], right_on=['code', 'age_group'])



pto_db = data[data['datum'] > null_date].pivot_table(index=["orp_bydliste_kod", 'age_group', 'final_vaccine', 'booster'], values='id', aggfunc='count', dropna=False).reset_index().fillna(0).merge(population_pto, how='left', left_on=['orp_bydliste_kod', 'age_group'], right_on=['code', 'age_group'])

pto_db['rate'] = pto_db['id'] / pto_db['value']

pto_db = pto_db[~(pto_db['age_group'] == 'nezařazeno')].reset_index()

pto_db['vaccine'] = 1 + pto_db['final_vaccine'].astype(int) + pto_db['booster'].astype(int).apply(lambda x: 2 * x)

pto = pto_db[pto_db['vaccine'] != 4].rename(columns={'id': 'n'}).pivot_table(index='orp_bydliste_kod', columns=['vaccine', 'age_group'], values=['rate'])

first = pto.loc[:, (slice(None), 2)].loc[:, ('rate', 2)] - pto.loc[:, (slice(None), 1)].loc[:, ('rate', 1)]
first.mask(first < 0, 0, inplace=True)

pto.loc[:, (slice(None), 1)].loc[:, ('rate', 1)] 

pto.columns = pto.columns.to_flat_index().str.join('_')

pto.to_csv('orp_age_rates_n.csv')

# current data by orp and "at least one" and age
# Počty a podíl - orp x věk.sk
pto1_db = data.pivot_table(index=["orp_bydliste_kod", 'age_group', 'poradi_davky'], values='pohlavi', aggfunc='count', dropna=False).reset_index().fillna(0).merge(population_pto, how='left', left_on=['orp_bydliste_kod', 'age_group'], right_on=['code', 'age_group'])

pto1_db['rate'] = pto1_db['pohlavi'] / pto1_db['value'] * 100

pto1_db = pto1_db[~(pto1_db['age_group'] == 'nezařazeno')].reset_index()

pto1 = pto1_db.rename(columns={'pohlavi': 'n'}).pivot_table(index='orp_bydliste_kod', columns=['poradi_davky', 'age_group'], values=['rate', 'n'])

# pto1.columns = pto1.columns.to_flat_index().str.join('_') # doesn't work, because 1 and 2 are integeres. not strings
# quick hack:
# pto1.columns = pto.columns
# https://stackoverflow.com/a/7687615/1666623
pto1.columns = [(x[0], str(x[1]), x[2])for x in pto1.columns]
pto1.columns = pto1.columns.to_flat_index().str.join('_')

pto1.to_csv('orp_age_rates_n1.csv')

ws = sh.worksheet('Počty a podíl - orp x věk.sk.')
# ws.update('B1', [pto1.columns.tolist()]) # not changing
ws.update('C2', pto1.replace(np.nan, 0).values.tolist())


# at least once x week x region
ptr_db = data[data['poradi_davky'] == 1].pivot_table(index=['region_code', 'week'], values='pohlavi', aggfunc='count').reset_index().merge(population_ptr, how='left', left_on=['region_code'], right_on=['region_code'])

ptr_db_cum = ptr_db.groupby(by=['region_code', 'week']).sum().groupby(level=[0])['pohlavi'].cumsum().reset_index().merge(ptr_db.loc[:, ['region_code', 'week', 'value']], how='left', left_on=['region_code', 'week'], right_on=['region_code', 'week'])
ptr_db_cum['rate'] = ptr_db_cum['pohlavi'] / ptr_db_cum['value']
ptr_db_cum['rate100'] = ptr_db_cum['pohlavi'] / ptr_db_cum['value'] * 100

ptr_db_cum.pivot_table(index='region_code', columns='week', values=['rate']).reset_index().to_csv('region_week_first.csv')


# at least once x date x region
# Počty - kraj x den | první
# Podíl - kraj x kumul. x den | první
ptrd_db = data[data['poradi_davky'] == 1].pivot_table(index=['region_code', 'datum'], values='pohlavi', aggfunc='count', dropna=False).reset_index().merge(population_ptr, how='left', left_on=['region_code'], right_on=['region_code'])

ptrd = data[data['poradi_davky'] == 1].pivot_table(index=['region_code'], columns=['datum'], values='pohlavi', aggfunc='count', dropna=False).reset_index()

ptrd.to_csv('region_date_first_n.csv')

ws = sh.worksheet('Počty - kraj x den | první')
ws.update('B1', [ptrd.columns.tolist()])
ws.update('B2', ptrd.replace(np.nan, '').values.tolist())


ptrd_db_cum = ptrd_db.groupby(by=['region_code', 'datum']).sum().groupby(level=[0])['pohlavi'].cumsum().reset_index().merge(ptrd_db.loc[:, ['region_code', 'datum', 'value']], how='left', left_on=['region_code', 'datum'], right_on=['region_code', 'datum'])
ptrd_db_cum['rate'] = ptrd_db_cum['pohlavi'] / ptrd_db_cum['value']
ptrd_db_cum['rate100'] = ptrd_db_cum['pohlavi'] / ptrd_db_cum['value'] * 100

ptrd_db_cum_out = ptrd_db_cum.pivot_table(index='region_code', columns='datum', values=['rate100']).reset_index()
ptrd_db_cum_out.to_csv('region_date_first.csv')

ws = sh.worksheet('Podíl - kraj x kumul. x den | první')
dates_out = [[x[1] for x in ptrd_db_cum_out.columns.tolist()]]
dates_out[0][0] = 'region_code'
ws.update('A1', dates_out)
ws.update('A2', ptrd_db_cum_out.replace(np.nan, 0).values.tolist())



# finished x week x region
pts_db = data[data['final_vaccine'] == '1'].pivot_table(index=['region_code', 'week'], values='pohlavi', aggfunc='count').reset_index().merge(population_ptr, how='left', left_on=['region_code'], right_on=['region_code'])

pts_db_cum = pts_db.groupby(by=['region_code', 'week']).sum().groupby(level=[0])['pohlavi'].cumsum().reset_index().merge(pts_db.loc[:, ['region_code', 'week', 'value']], how='left', left_on=['region_code', 'week'], right_on=['region_code', 'week'])
pts_db_cum['rate'] = pts_db_cum['pohlavi'] / pts_db_cum['value']

pts_db_cum.pivot_table(index='region_code', columns='week', values=['rate']).reset_index().to_csv('region_week_finished.csv')


# at least once (=1st vaccine) x orp x date - cummulative
# Počty - orp x den | první
# Podíl - orp x kumul. x den | první
ptso_db = data[data['poradi_davky'] == 1].pivot_table(index=['orp_bydliste_kod', 'datum'], values='pohlavi', aggfunc='count').reset_index().merge(population_pto_all, how='left', left_on=['orp_bydliste_kod'], right_on=['code'])

ptso = data[data['poradi_davky'] == 1].pivot_table(index=['orp_bydliste_kod'], columns=['datum'], values='pohlavi', aggfunc='count', dropna=False).reset_index()
ptso.to_csv('orp_date_first_n.csv')

ws = sh.worksheet('Počty - orp x den | první')
ws.update('B1', [ptso.columns.tolist()])
ws.update('B2', ptso.replace(np.nan, 0.0).values.tolist())


ptso_db_cum = ptso_db.groupby(by=['code', 'datum']).sum().groupby(level=[0])['pohlavi'].cumsum().reset_index().merge(ptso_db.loc[:, ['code', 'datum', 'value']], how='left', left_on=['code', 'datum'], right_on=['code', 'datum'])

ptso_db_cum['rate'] = ptso_db_cum['pohlavi'] / ptso_db_cum['value']
ptso_db_cum['rate100'] = ptso_db_cum['pohlavi'] / ptso_db_cum['value'] * 100

ptso_out = ptso_db_cum.pivot_table(index='code', columns='datum', values=['rate100']).reset_index()

ptso_out.columns = ptso_out.columns.to_flat_index().str.join('').str.replace('rate100','')

ptso_out.iloc[:, 1] = ptso_out.iloc[:, 1].fillna(0)

for d in range(2, len(ptso_out.columns)):
    ptso_out.iloc[:, d].fillna(ptso_out.iloc[:, (d - 1)], inplace=True)

ptso_out.to_csv('orp_date_first.csv')

ws = sh.worksheet('Podíl - orp x kumul. x den | první')
ws.update('A1', [ptso_out.columns.tolist()])
ws.update('A2', ptso_out.replace(np.nan, 0).values.tolist())


# for chart: orp x fully vaccinated/partly/none
# Bar Chart - orp x věk.sk.
population_groups = population_labels
pto_chart = pto_db.pivot_table(index=["orp_bydliste_kod"], columns=['age_group', 'final_vaccine'], values=['pohlavi', 'value'])

pto_chart = pto_chart.fillna(0)

pto_chart.columns = pto_chart.columns.to_flat_index().str.join('_')

# pto_db[pto_db['orp_bydliste_kod'] == 8022]
# pto_chart['value_0-17_1']

bar = 75

pto_chart_out = pd.DataFrame(index=pto_chart.index)
for k in population_groups:
    pto_chart_out[k + '_fully_vaccinated'] = pto_chart['pohlavi_' + k + '_1'] / pto_chart['value_' + k + '_1'] * bar
    pto_chart_out[k + '_partly_vaccinated'] = (pto_chart['pohlavi_' + k + '_0'] - pto_chart['pohlavi_' + k + '_1']) / pto_chart['value_' + k + '_1'] * bar
    pto_chart_out[k + '_no_vaccinated'] = (pto_chart['value_' + k + '_1'] - pto_chart['pohlavi_' + k + '_0']) / pto_chart['value_' + k + '_1'] * bar

pto_chart_out.reset_index().to_csv("orp_bar_chart_values.csv")

ws = sh.worksheet('Bar Chart - orp x věk.sk.')
ws.update('B2', pto_chart_out.replace(np.nan, 0).values.tolist())

bar = 100
min_dist = 10

pto_chart_desc = pd.DataFrame(index=pto_chart.index)
for k in population_groups:
    pto_chart_desc[k + '_fully_vaccinated_desc'] = round(pto_chart['pohlavi_' + k + '_1'] / pto_chart['value_' + k + '_1'] * bar)
    pto_chart_desc[k + '_partly_vaccinated_desc'] = round(pto_chart['pohlavi_' + k + '_0'] / pto_chart['value_' + k + '_1'] * bar)

pto_chart_desc[pto_chart_desc < min_dist] = np.NaN
for k in population_groups:
    pto_chart_desc[k + '_fully_vaccinated_desc'][pto_chart_desc[k + '_partly_vaccinated_desc'] - pto_chart_desc[k + '_fully_vaccinated_desc'] < min_dist] = np.NaN

pto_chart_desc.reset_index().to_csv("orp_bar_chart_descriptions.csv")

ws = sh.worksheet('Bar Chart desc - orp x věk.sk.')
ws.update('B2', pto_chart_desc.replace(np.nan, '').values.tolist())

# for chart: region x fully vaccinated/partly/none
# Bar Chart - kraj x věk.sk.
# Bar Chart desc - kraj x věk.sk.
pt_chart = pt_db.pivot_table(index=["region_code"], columns=['age_group', 'final_vaccine'], values=['pohlavi', 'value'])

pt_chart = pt_chart.fillna(0)

pt_chart.columns = pt_chart.columns.to_flat_index().str.join('_')


bar = 75

pt_chart_out = pd.DataFrame(index=pt_chart.index)
for k in population_groups:
    pt_chart_out[k + '_fully_vaccinated'] = pt_chart['pohlavi_' + k + '_1'] / pt_chart['value_' + k + '_1'] * bar
    pt_chart_out[k + '_partly_vaccinated'] = (pt_chart['pohlavi_' + k + '_0'] - pt_chart['pohlavi_' + k + '_1']) / pt_chart['value_' + k + '_1'] * bar
    pt_chart_out[k + '_no_vaccinated'] = (pt_chart['value_' + k + '_1'] - pt_chart['pohlavi_' + k + '_0']) / pt_chart['value_' + k + '_1'] * bar

pt_chart_out.reset_index().to_csv("region_bar_chart_values.csv")

ws = sh.worksheet('Bar Chart - kraj x věk.sk.')
ws.update('B2', pt_chart_out.replace(np.nan, 0).values.tolist())

bar = 100
min_dist = 10

pt_chart_desc = pd.DataFrame(index=pt_chart.index)
for k in population_groups:
    pt_chart_desc[k + '_fully_vaccinated_desc'] = round(pt_chart['pohlavi_' + k + '_1'] / pt_chart['value_' + k + '_1'] * bar)
    pt_chart_desc[k + '_partly_vaccinated_desc'] = round(pt_chart['pohlavi_' + k + '_0'] / pt_chart['value_' + k + '_1'] * bar)

pt_chart_desc[pt_chart_desc < min_dist] = np.NaN
for k in population_groups:
    pt_chart_desc[k + '_fully_vaccinated_desc'][pt_chart_desc[k + '_partly_vaccinated_desc'] - pt_chart_desc[k + '_fully_vaccinated_desc'] < min_dist] = np.NaN

pt_chart_desc.reset_index().to_csv("region_bar_chart_descriptions.csv")

ws = sh.worksheet('Bar Chart desc - kraj x věk.sk.')
ws.update('B2', pt_chart_desc.replace(np.nan, '').values.tolist())


# generate html for chart tooltip
li = "<li><span class='party-bar' style='display: inline-block; background-color: #63698C; width: {{XXX_fully_vaccinated}}%'><span class='party-desc'>{{XXX_fully_vaccinated_desc}}&nbsp;</span></span><span class='party-bar' style='display: inline-block; background-color: #76B7CE; width: {{XXX_partly_vaccinated}}%'><span  class='party-desc'>{{XXX_partly_vaccinated_desc}}&nbsp;</span></span><span class='party-bar' style='display: inline-block; background-color: #DBACAC; width: {{XXX_no_vaccinated}}%'></span>&nbsp;<span class='party-name'>XXX</span></li>"
tooltip = ''
for k in reversed(population_groups):
    tooltip += li.replace('XXX', k)
    tooltip += "\n"
print(tooltip)

style = ".party-desc = {color: #eee; font-size: 0.9em; font-weight: bold; position: relative; bottom: 1px; float: right}"

######
# data.pivot_table(index="orp_bydliste_kod", columns=['vekova_skupina'], values=['pohlavi'], aggfunc='count').to_csv("basic_overview.csv")

# data.pivot_table(index="orp_bydliste_kod", columns=['datum'], values=['pohlavi'], aggfunc='count').to_csv("pt_date.csv")

# data[data['week'] == '2021-53']

# data['datum'].max()

# data['vakcina'].unique()
# data['vakcina_kod'].unique()
# data['vekova_skupina'].unique()

# data[data['vakcina'] == 'COVID-19 Vaccine Janssen'].pivot_table(index='kraj_nazev', columns=['datum'], values=['pohlavi'], aggfunc='count')

# round(data['orp_bydliste_kod'] / 100)

# data[1:5]

# data['datum'].apply(datetime.datetime.fromisoformat).dt.month.map("{:02}".format)
# data['datum'].apply(datetime.datetime.fromisoformat).dt.year

# import os
# os.getcwd()

# pto1_db = data[data['datum'] > '2021-05-05'].pivot_table(index=["orp_bydliste_kod", 'age_group', 'poradi_davky'], values='pohlavi', aggfunc='count', dropna=False).reset_index().fillna(0).merge(population_pto, how='left', left_on=['orp_bydliste_kod', 'age_group'], right_on=['code', 'age_group'])

# pto1_db['rate'] = pto1_db['pohlavi'] / pto1_db['value']

# pto1_db = pto1_db[~(pto1_db['age_group'] == 'nezařazeno')].reset_index()

# pto1 = pto1_db.rename(columns={'pohlavi': 'n'}).pivot_table(index='orp_bydliste_kod', columns=['poradi_davky', 'age_group'], values=['rate', 'n'])

# pto1.columns = pto1.columns.to_flat_index().str.join('_') # doesn't work, because 1 and 2 are integeres. not strings
# # quick hack:
# pto1.columns = pto.columns

# pto1.to_csv('test.csv')

# #######################
# data[data['datum'] == '2021-05-18'].to_csv('d18.csv')

# data.groupby(['vekova_skupina']).sum()

# data[data['vekova_skupina'] == '0-17'].to_csv('d017.csv')

# data.columns

# age_date = data[data['poradi_davky'] == 1].groupby(['datum', 'vekova_skupina', ], dropna=False)['kraj_kod'].count().reset_index().rename(columns={'kraj_kod': 'value'})

# pd.pivot_table(age_date, index='datum', columns=['vekova_skupina'], values='value').to_csv('age_date.csv')
