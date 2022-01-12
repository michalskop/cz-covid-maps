"""Vaccination CZ."""

import datetime
import numpy as np
import pandas as pd

path = "/home/michal/dev/coronavirus/cz-covid-maps/orp/"

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

regional_levels =['kraje', 'orp']

for regional_level in regional_levels:
    # load data
    # https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/ockovani-profese.csv
    data = pd.read_csv(path + "ockovani-profese.csv")

    # print(data['datum_vakcinace'].max())
    print(data['datum'].max())

    data['kraje_bydliste_kod'] = round(data['orp_bydliste_kod'] / 100)

    # read data from 'origin.csv' (geometries)
    origin = pd.read_csv(path + "origin_" + regional_level + ".csv")
    out = origin.copy()

    # read data about population
    population = pd.read_csv(path + regional_level + "_population_age.csv")

    population_bins=[0, 12, 18, 30, 40, 50, 60, 70, 80, 110]

    population_labels = ['0-11', '12-17', '18-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+']

    # encode population
    population['age_group'] = pd.cut(population['age'], bins=population_bins, labels=population_labels, right=False)

    # add regions to population
    if regional_level == 'orp':
        population['region_code'] = round(population['code'] / 100)
    else:
        population['region_code'] = population['code']

    # pivot population by age groups
    population_pt = population.pivot_table(index=['region_code', 'age_group'], values=['value'], aggfunc=np.sum).reset_index()

    population_pto = population.pivot_table(index=['code', 'age_group'], values=['value'], aggfunc=np.sum).reset_index()

    population_ptr = population.pivot_table(index=['region_code'], values=['value'], aggfunc=np.sum).reset_index()

    population_pto_all = population.pivot_table(index=['code'], values=['value'], aggfunc=np.sum).reset_index()

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
    if regional_level == 'orp':
        data['region_code'] = round(data['orp_bydliste_kod'] / 100)
    else:
        data['region_code'] = data['kraje_bydliste_kod']

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
    pt_w = data[data['week'].isin(weeks)].pivot_table(index=[regional_level + '_bydliste_kod'], values=['id'], columns=['week'], dropna=False, aggfunc='count').reset_index().replace(np.nan, 0)
    pt_w.columns = pt_w.columns.droplevel(0)
    pt_w.rename(columns={'': 'kód'}, inplace=True)
    pt_w100 = pt_w.loc[:, ['kód']].merge((round(pt_w.loc[:, weeks].divide(pt_w.loc[:, weeks].max(axis=1), axis='index') * 100)).fillna(0).astype(int), left_index=True, right_index=True)
    pt_w100 = pt_w100[['kód'] + weeks]
    pt_w100.columns = ['kód'] + [(lambda x: ("week_" + str(x)))(x) for x in range(0, len(weeks))]

    out = out.merge(pt_w100, on='kód', how='left')

    # current data by orp/kraje and 1/2/3 and age
    groups = ['first_others', 'second_others', 'third_others', 'first_janssen', 'second_janssen', 'third_janssen']

    pto = {}
    for g in groups:
        pto[g] = data[data['datum'] > null_date].pivot_table(index=[regional_level + "_bydliste_kod", 'age_group', g], values='id', aggfunc='count', dropna=False).reset_index().fillna(0).merge(population_pto, how='left', left_on=[regional_level + '_bydliste_kod', 'age_group'], right_on=['code', 'age_group'])

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
    pto_chart_real.fillna(-999, inplace=True)
    pto_chart_real = pto_chart_real.astype(int)
    pto_chart_real.replace(-999, np.nan, inplace=True)

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
    selected_days = pd.date_range(since_day, last_day, freq='2W').to_list()
    if selected_days[-1].strftime('%Y-%m-%d') != last_date:
        selected_days.append(last_day)
    for until_day in selected_days:
        until_date = until_day.strftime('%Y-%m-%d')
        print(until_date) # progress bar
        null_day = until_day - datetime.timedelta(days=null_after_days)
        null_date = null_day.strftime("%Y-%m-%d")

        pto = {}
        for g in groups:
            pto[g] = data[(data['datum'] > null_date) & (data['datum'] <= until_date)].pivot_table(index=[regional_level + "_bydliste_kod", 'age_group', g], values='id', aggfunc='count', dropna=False).reset_index().fillna(0).merge(population_pto, how='left', left_on=[regional_level + '_bydliste_kod', 'age_group'], right_on=['code', 'age_group'])

        levelone = pto['first_others'][pto['first_others']['first_others']]['id'] - pto['second_others'][pto['second_others']['second_others']]['id']

        empty_column = levelone.copy()
        empty_column[:] = 0
        level = [0] * 4

        level[3] = pto['third_others'][pto['third_others']['third_others']]['id'] + pto['third_janssen'][pto['third_janssen']['third_janssen']]['id'] + pto['second_janssen'][pto['second_janssen']['second_janssen']]['id']
        level[3].fillna(0, inplace=True)
        if len(level[3]) == 0:  # no third level
            level[3] = empty_column
        level[2] = (pto['second_others'][pto['second_others']['second_others']]['id'] + pto['first_janssen'][pto['first_janssen']['first_janssen']]['id'] - level[3]).apply(lambda x: max(x, 0))
        level[2].fillna(0, inplace=True)
        if len(level[2]) == 0:  # no second level
            level[2] = empty_column
        level[1] = (levelone).apply(lambda x: max(x, 0))
        level[1].fillna(0, inplace=True)
        if len(level[1]) == 0:  # no first level
            level[1] = empty_column
        level_one_plus = level[3] + level[2] + level[1]
        level_two_plus = level[3] + level[2]
        level[0] = pto['first_others'][pto['first_others']['first_others']]['value'] - level_one_plus

        # current: absolutne, rate, age-specific rates
        pto_selected = pto['first_others'][pto['first_others']['first_others']]
        # pto_selected['level_one_plus'] = 0
        pto_selected['level_two_plus'] = level_two_plus.to_frame()
        for i in range(0, 4):
            pto_selected['level_' + str(i)] = level[i].to_frame()

        # break

        totals = pd.pivot_table(pto_selected, index='code', values=['level_two_plus', 'value'], aggfunc=np.sum)
        totals[until_day.strftime('%-d.%-m.%y')] = round(totals['level_two_plus'] / totals['value'] * 100, 1)
        totals = totals.reset_index()
        out = out.merge(totals.loc[:, [until_day.strftime('%-d.%-m.%y'), 'code']], how='left', left_on='kód', right_on='code')
        del out['code']
        out[until_day.strftime('%-d.%-m.%y')].fillna(0, inplace=True)

        # break

    out.to_csv(path + regional_level + '.csv', index=False)
    print(regional_level + ' done')



# generate html for chart tooltip
# li = "<li><span class='party-bar level-3' style='width: {{chart_level_3_XXX}}%'><span class='party-desc'>{{chart_level_3_XXX_desc}}&nbsp;</span></span><span class='party-bar level-2' style='width: {{chart_level_2_XXX}}%'><span class='party-desc'>{{chart_level_2_XXX_desc}}&nbsp;</span></span><span class='party-bar level-1' style='width: {{chart_level_1_XXX}}%'><span class='party-desc'>{{chart_level_1_XXX_desc}}&nbsp;</span></span><span class='party-bar level-0' style='width: {{chart_level_0_XXX}}%'><span  class='party-desc'>&nbsp;</span></span>&nbsp;<span class='party-name'>XXX</span></li>"
# tooltip = ''
# for k in reversed(population_labels):
#     tooltip += li.replace('XXX', k)
#     tooltip += "\n"
# print(tooltip)

# <style>
# .party-bar {
#   width: 0;
#   display: inline-block;
#   vertical-align: top;
#   height: 14px;
#   background-color: #ccc;
# }

# .party-desc {
#   color: #eee;
#   font-size: 0.9em;
#   font-weight: bold;
#   position: relative;
#   bottom: 1px; 
#   float: right
# }

# .sc-only {
#   display:none;  
# }
# @media(min-width: 600px) {
#   .sc-only {
#     display: block
#   }
# }
# </style>
