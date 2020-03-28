from lxml import html as lh
import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from io import StringIO
from scipy import optimize
from scipy.optimize import curve_fit


 # define your function:
def gauss_func(x, height, mu, sigma): return height * np.exp(-((x-mu)**2/(2*sigma**2)))


def line_func(x, m, b): return (m * x) + b


def fetch_data_from_data_dot_gouv_website():
    try:
        saved_data = pd.read_pickle('raw_hospitalizations.pkl')
    except FileNotFoundError:
        saved_data = pd.DataFrame(index=[pd.to_datetime('9999-01-01')])

    max_saved_date = saved_data.date_de_passage.astype('datetime64').max()
    data_url = 'https://www.data.gouv.fr/fr/datasets/donnees-des-urgences-hospitalieres-et-de-sos-medecins-relatives-a-lepidemie-de-covid-19/'
    if (max_saved_date + pd.Timedelta('2 days')) < pd.to_datetime(datetime.today().strftime('%Y-%m-%d')):
        page = requests.get(data_url)
        # Store the contents of the website under doc
        doc = lh.fromstring(page.content)
        csv_link_element = doc.xpath('/html/body/section[3]/div/div/div/div[3]/article[1]/footer/div[2]/a[2]')
        csv_link = csv_link_element[0].attrib['href']
        with requests.Session() as s:
            download = s.get(csv_link)
        decoded_content = download.content.decode('utf-8')
        df = pd.read_csv(StringIO(decoded_content))
        df.to_pickle('raw_hospitalizations.pkl')
    else:
        print("didn't download anything")
        df = saved_data
    return df


def gaussian_fit_data(s):
    data = s.dropna().values
    data_x = s.dropna().index.astype('int').values
    popt, pcov = curve_fit(
        gauss_func,
        data_x,
        data,
        p0=[100, pd.Timestamp('2020-03-30').value, pd.to_timedelta('2 days').value]
    )
    return popt[0] * np.exp(-((s.index.astype('int') - popt[1]) ** 2 / (2 * popt[2] ** 2)))


raw = fetch_data_from_data_dot_gouv_website()
raw.date_de_passage = raw.date_de_passage.astype('datetime64')
raw.set_index('date_de_passage', inplace=True)

covid = pd.DataFrame()
covid['Paris'] = raw.where(raw.sursaud_cl_age_corona == '0')\
    .where(raw.dep == '75')\
    .nbre_hospit_corona.dropna()
covid['Marseilles'] = raw.where(raw.sursaud_cl_age_corona == '0')\
    .where(raw.dep == '13')\
    .nbre_hospit_corona.dropna()
covid['Bordeaux'] = raw.where(raw.sursaud_cl_age_corona == '0')\
    .where(raw.dep == '33')\
    .nbre_hospit_corona.dropna()
covid['Strasbourg'] = raw.where(raw.sursaud_cl_age_corona == '0')\
    .where(raw.dep == '67')\
    .nbre_hospit_corona.dropna()
covid['France'] = raw.where(raw.sursaud_cl_age_corona == '0').dropna().nbre_hospit_corona.resample('D').sum()
covid = covid.reindex(pd.date_range('2-24-2020', '5-1-2020'))


covid['Paris_fit'] = gaussian_fit_data(covid.Paris)
covid['Marseilles_fit'] = gaussian_fit_data(covid.Marseilles)
covid['Strasbourg_fit'] = gaussian_fit_data(covid.Strasbourg)
covid['Bordeaux_fit'] = gaussian_fit_data(covid.Bordeaux)
covid['France_fit'] = gaussian_fit_data(covid.France)

title = "Hospitalizations per day in France"
fig1, ax1 = plt.subplots()
covid.plot(y=['Paris', 'Marseilles', 'Strasbourg', 'Bordeaux'], ax=ax1, title=title, grid=True, figsize=(20, 15))
covid.plot(style='k--', y=['Paris_fit', 'Bordeaux_fit', 'Strasbourg_fit', 'Marseilles_fit'], ax=ax1)
covid.plot(style='k--', y=['France_fit', ], secondary_y=True, ax=ax1)
covid.plot(y="France", secondary_y=True, ax=ax1, lw=4, grid=True).get_figure().savefig('hospitalizations.png')
# covid.plot(y=["Paris_fit"], style='.', ax=ax1)

# raw.where(raw.sursaud_cl_age_corona == '0')\
#     .where(raw.dep == '75')\
#     .nbre_hospit_corona.dropna()\
#     .cumsum()\
#     .plot(
#     label='Paris',
#     # kind='bar',
#     legend=True,
#     figsize=(20, 15),
#     title='Hospitalizations per day'
#     )
#
# raw.where(raw.sursaud_cl_age_corona == '0')\
#     .where(raw.dep == '13')\
#     .nbre_hospit_corona.dropna()\
#     .plot(
#     label='Marseilles',
#     secondary_y=True,
#     legend=True
#     ).get_figure().savefig('hospitalizations.png')

