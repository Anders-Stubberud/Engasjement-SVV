```python
%load_ext autoreload
%autoreload 2

from source.config import EXTERNAL_DATA_DIR, INTERIM_DATA_DIR
import pandas as pd
```

    The autoreload extension is already loaded. To reload it, use:
      %reload_ext autoreload


**Table of contents**<a id='toc0_'></a>    
- [6: Sett opp oversikt over ulike ekvipasjer (bil og henger kombinasjoner) som har blitt benyttet.](#toc1_)    
- [7+8 (mål på hva de foretrekker): Hvor ofte har ulike ekvipasjer blitt benyttet, sett opp statistisk fordeling. + Hvor mange km har ulike ekvipasjer tilbakelagt.](#toc2_)    

<!-- vscode-jupyter-toc-config
	numbering=false
	anchor=true
	flat=false
	minLevel=1
	maxLevel=6
	/vscode-jupyter-toc-config -->
<!-- THIS CELL WILL BE REPLACED ON TOC UPDATE. DO NOT WRITE YOUR TEXT IN THIS CELL -->

# <a id='toc1_'></a>[6: Sett opp oversikt over ulike ekvipasjer (bil og henger kombinasjoner) som har blitt benyttet.](#toc0_)


```python
df_ekvipasje = pd.read_csv(EXTERNAL_DATA_DIR / 'bil_tilhenger_matching.csv').drop_duplicates(subset='VIN_lastebil')
df_vehicle_data = pd.read_csv(INTERIM_DATA_DIR / "vehicle weight from 74t.csv")

df_vehicle_data = (
    df_vehicle_data[df_vehicle_data['VIN'].isin(df_ekvipasje['VIN_lastebil'])]
    .assign(
        år=pd.to_datetime(df_vehicle_data['Dato'], format='ISO8601').dt.year,
        ekvipasje=df_vehicle_data['VIN'].map(df_ekvipasje.set_index('VIN_lastebil')['ekvipasje'])
    )
)

df6 = (
    df_vehicle_data.groupby(['år', 'ekvipasje']).agg(**{
        'registrerte kjøretøy': ('VIN', 'nunique'),
    })
    .reset_index()
)

df6[['år', 'ekvipasje', 'registrerte kjøretøy']].sort_values(by=['år', 'ekvipasje'], ascending=True)

```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>år</th>
      <th>ekvipasje</th>
      <th>registrerte kjøretøy</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2021</td>
      <td>3-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>3</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2021</td>
      <td>3-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>4</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2021</td>
      <td>4-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>1</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2021</td>
      <td>4-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>1</td>
    </tr>
    <tr>
      <th>4</th>
      <td>2022</td>
      <td>3-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>4</td>
    </tr>
    <tr>
      <th>5</th>
      <td>2022</td>
      <td>3-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>7</td>
    </tr>
    <tr>
      <th>6</th>
      <td>2022</td>
      <td>4-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>2</td>
    </tr>
    <tr>
      <th>7</th>
      <td>2022</td>
      <td>4-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>2</td>
    </tr>
    <tr>
      <th>8</th>
      <td>2023</td>
      <td>3-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>4</td>
    </tr>
    <tr>
      <th>9</th>
      <td>2023</td>
      <td>3-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>8</td>
    </tr>
    <tr>
      <th>10</th>
      <td>2023</td>
      <td>4-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>2</td>
    </tr>
    <tr>
      <th>11</th>
      <td>2023</td>
      <td>4-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>3</td>
    </tr>
    <tr>
      <th>12</th>
      <td>2024</td>
      <td>3-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>4</td>
    </tr>
    <tr>
      <th>13</th>
      <td>2024</td>
      <td>3-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>8</td>
    </tr>
    <tr>
      <th>14</th>
      <td>2024</td>
      <td>4-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>2</td>
    </tr>
    <tr>
      <th>15</th>
      <td>2024</td>
      <td>4-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>3</td>
    </tr>
  </tbody>
</table>
</div>




```python
df_antall_unike = (
    df_vehicle_data.groupby(['ekvipasje']).agg(**{
        'registrerte kjøretøy': ('VIN', 'nunique'),
    })
    .reset_index()
)

df_antall_unike[['ekvipasje', 'registrerte kjøretøy']].sort_values(by=['ekvipasje'], ascending=True)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>ekvipasje</th>
      <th>registrerte kjøretøy</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>3-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>4</td>
    </tr>
    <tr>
      <th>1</th>
      <td>3-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>8</td>
    </tr>
    <tr>
      <th>2</th>
      <td>4-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>2</td>
    </tr>
    <tr>
      <th>3</th>
      <td>4-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>3</td>
    </tr>
  </tbody>
</table>
</div>



# <a id='toc2_'></a>[7+8 (mål på hva de foretrekker): Hvor ofte har ulike ekvipasjer blitt benyttet, sett opp statistisk fordeling. + Hvor mange km har ulike ekvipasjer tilbakelagt.](#toc0_)

Tabellen under viser antall turer og km tilbakelagt for hver ekvipasje for hvert år fra 2021-2024.


```python
df_grouped = df_vehicle_data.groupby(['ekvipasje', 'år']).agg(**{
    'turer': ('VIN', 'count'),
    'kilometer': ('Distanse (km)', 'sum'),
    'registrerte kjøretøy': ('VIN', 'nunique')
}).reset_index()

df_grouped['turer per kjøretøy'] = df_grouped['turer'] / df_grouped['registrerte kjøretøy']
df_grouped['km per kjøretøy'] = df_grouped['kilometer'] / df_grouped['registrerte kjøretøy']

df_grouped.sort_values(by=['år', 'ekvipasje'], ascending=True).round(2)

```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>ekvipasje</th>
      <th>år</th>
      <th>turer</th>
      <th>kilometer</th>
      <th>registrerte kjøretøy</th>
      <th>turer per kjøretøy</th>
      <th>km per kjøretøy</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>3-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>2021</td>
      <td>766</td>
      <td>282918.0</td>
      <td>3</td>
      <td>255.33</td>
      <td>94306.00</td>
    </tr>
    <tr>
      <th>4</th>
      <td>3-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>2021</td>
      <td>941</td>
      <td>326593.0</td>
      <td>4</td>
      <td>235.25</td>
      <td>81648.25</td>
    </tr>
    <tr>
      <th>8</th>
      <td>4-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>2021</td>
      <td>51</td>
      <td>12222.0</td>
      <td>1</td>
      <td>51.00</td>
      <td>12222.00</td>
    </tr>
    <tr>
      <th>12</th>
      <td>4-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>2021</td>
      <td>333</td>
      <td>137302.0</td>
      <td>1</td>
      <td>333.00</td>
      <td>137302.00</td>
    </tr>
    <tr>
      <th>1</th>
      <td>3-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>2022</td>
      <td>1131</td>
      <td>374296.0</td>
      <td>4</td>
      <td>282.75</td>
      <td>93574.00</td>
    </tr>
    <tr>
      <th>5</th>
      <td>3-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>2022</td>
      <td>1882</td>
      <td>568852.0</td>
      <td>7</td>
      <td>268.86</td>
      <td>81264.57</td>
    </tr>
    <tr>
      <th>9</th>
      <td>4-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>2022</td>
      <td>504</td>
      <td>122606.0</td>
      <td>2</td>
      <td>252.00</td>
      <td>61303.00</td>
    </tr>
    <tr>
      <th>13</th>
      <td>4-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>2022</td>
      <td>418</td>
      <td>140216.0</td>
      <td>2</td>
      <td>209.00</td>
      <td>70108.00</td>
    </tr>
    <tr>
      <th>2</th>
      <td>3-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>2023</td>
      <td>1207</td>
      <td>356309.0</td>
      <td>4</td>
      <td>301.75</td>
      <td>89077.25</td>
    </tr>
    <tr>
      <th>6</th>
      <td>3-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>2023</td>
      <td>2359</td>
      <td>724260.0</td>
      <td>8</td>
      <td>294.88</td>
      <td>90532.50</td>
    </tr>
    <tr>
      <th>10</th>
      <td>4-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>2023</td>
      <td>615</td>
      <td>153507.0</td>
      <td>2</td>
      <td>307.50</td>
      <td>76753.50</td>
    </tr>
    <tr>
      <th>14</th>
      <td>4-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>2023</td>
      <td>978</td>
      <td>309018.0</td>
      <td>3</td>
      <td>326.00</td>
      <td>103006.00</td>
    </tr>
    <tr>
      <th>3</th>
      <td>3-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>2024</td>
      <td>1189</td>
      <td>323768.0</td>
      <td>4</td>
      <td>297.25</td>
      <td>80942.00</td>
    </tr>
    <tr>
      <th>7</th>
      <td>3-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>2024</td>
      <td>2038</td>
      <td>536278.0</td>
      <td>8</td>
      <td>254.75</td>
      <td>67034.75</td>
    </tr>
    <tr>
      <th>11</th>
      <td>4-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>2024</td>
      <td>667</td>
      <td>175759.0</td>
      <td>2</td>
      <td>333.50</td>
      <td>87879.50</td>
    </tr>
    <tr>
      <th>15</th>
      <td>4-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>2024</td>
      <td>1017</td>
      <td>305748.0</td>
      <td>3</td>
      <td>339.00</td>
      <td>101916.00</td>
    </tr>
  </tbody>
</table>
</div>



Tabellen under viser en videre bearbeiding av tabellen ovenfor, gruppert på ekvipasje, aggregert på turer/km per kjøretøy, og delt på antall år.
Dersom man bruker "km per kjøretøy per år" og/eller "turer per kjøretøy per år" som et mål på hvilken ekvipasje som er foretrukket, kommer 4+5 (74T) best ut her.


```python
year_counts = df_grouped.groupby('ekvipasje')['år'].nunique().reset_index()
year_counts = year_counts.rename(columns={'år': 'num_years'})

df_grouped = df_grouped.merge(year_counts, on='ekvipasje', how='left')

df_grouped['turer per kjøretøy per år'] = df_grouped['turer per kjøretøy'] / df_grouped['num_years']
df_grouped['km per kjøretøy per år'] = df_grouped['km per kjøretøy'] / df_grouped['num_years']

df_pivot = df_grouped.pivot_table(
    index='ekvipasje', 
    values=['turer per kjøretøy per år', 'km per kjøretøy per år'], 
    aggfunc='sum'
).reset_index()

df_pivot.sort_values(by='ekvipasje', ascending=True).round(2)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>ekvipasje</th>
      <th>km per kjøretøy per år</th>
      <th>turer per kjøretøy per år</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>3-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>89474.81</td>
      <td>284.27</td>
    </tr>
    <tr>
      <th>1</th>
      <td>3-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>80120.02</td>
      <td>263.43</td>
    </tr>
    <tr>
      <th>2</th>
      <td>4-akslet trekkvogn med 4-akslet tilhenger</td>
      <td>59539.50</td>
      <td>236.00</td>
    </tr>
    <tr>
      <th>3</th>
      <td>4-akslet trekkvogn med 5-akslet tilhenger</td>
      <td>103083.00</td>
      <td>301.75</td>
    </tr>
  </tbody>
</table>
</div>


