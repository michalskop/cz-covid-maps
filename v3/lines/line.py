"""General overview line of the covid cases."""

import pandas as pd

localpath = "v3/lines/"

# read data from UZIS
url = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/incidence-7-14-kraje.csv"

df = pd.read_csv(url, delimiter=",")

# pivot table
pt = pd.pivot_table(df, index='datum',  values='incidence_7', fill_value=0, aggfunc='sum').reset_index()

# save
pt.rename(columns={'datum': 'datum', 'incidence_7': 'Týdenní přírůstek'}, inplace=True )
pt.to_csv(localpath + "incidence_7.csv", index=False)