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


def fetch_data_from_data_dot_gouv_website(data_url):

    page = requests.get(data_url)
    # Store the contents of the website under doc
    doc = lh.fromstring(page.content)
    filename_element = doc.xpath('/html/body/section[3]/div/div/div/div[3]/article[1]/div/h4')
    filename = filename_element[0].text.split('-')
    print(filename)
    # current_data_date = datetime.strptime("".join(filename[3:7]), '%Y%m%d%Hh%M')
    csv_link_element = doc.xpath('/html/body/section[3]/div/div/div/div[3]/article[2]/footer/div[2]/a[2]')
    csv_link = csv_link_element[0].attrib['href']
    # if (max_saved_date + pd.Timedelta('0 days')) < pd.to_datetime(datetime.today().strftime('%Y-%m-%d')):
    with requests.Session() as s:
        download = s.get(csv_link)
    decoded_content = download.content.decode("utf-8")
    df = pd.read_csv(StringIO(decoded_content), sep=';')
    print(csv_link)
    df.to_pickle('raw_hospitalizations.pkl')

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

# data_url = 'https://www.data.gouv.fr/fr/datasets/donnees-des-urgences-hospitalieres-et-de-sos-medecins-relatives-a-lepidemie-de-covid-19/'
data_url = 'https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/'
raw = fetch_data_from_data_dot_gouv_website(data_url)
raw.jour = raw.jour.astype('datetime64')
raw.set_index('jour', inplace=True)

covid = pd.DataFrame()
covid['Paris_reanimation'] = raw.where(raw.sexe == 0)\
    .where(raw.dep == '75')\
    .rea.dropna()
covid['Marseilles_reanimation'] = raw.where(raw.sexe == 0)\
    .where(raw.dep == '13')\
    .rea.dropna()
covid['Lyon_reanimation'] = raw.where(raw.sexe == 0)\
    .where(raw.dep == '69')\
    .rea.dropna()
covid['Savoie_reanimation'] = raw.where(raw.sexe == 0)\
    .where(raw.dep == '74')\
    .rea.dropna()
covid['Paris_hospital'] = raw.where(raw.sexe == 0)\
    .where(raw.dep == '75')\
    .hosp.dropna()
covid['Marseilles_hospital'] = raw.where(raw.sexe == 0)\
    .where(raw.dep == '13')\
    .hosp.dropna()
covid['Lyon_hospital'] = raw.where(raw.sexe == 0)\
    .where(raw.dep == '69')\
    .hosp.dropna()
covid['Savoie_hospital'] = raw.where(raw.sexe == 0)\
    .where(raw.dep == '74')\
    .hosp.dropna()
# covid['Lyon'] = raw.where(raw.sexe == 0)\
#     .where(raw.dep == '69')\
#     .rad.dropna().diff()

covid['France'] = raw.where(raw.sexe == 0).dropna().hosp.resample('D').sum().diff()
# covid.reset_index(inplace=True)
# covid = covid.reindex(index=pd.date_range('3-18-2020', '8-1-2020'))

lockdown_start = pd.to_datetime('3-16-2020')
lockdown_end = pd.to_datetime('5-10-2020')
# lockdown_end = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))

lockdown2_start = pd.to_datetime('10-30-2020')
lockdown2_end = pd.to_datetime('12-1-2020')

lockdown3_start = pd.to_datetime('4-3-2021')
lockdown3_end = pd.to_datetime('4-25-2021')

title = "Currently in Hospital"
reanimations = ['Paris_reanimation', 'Marseilles_reanimation', 'Lyon_reanimation', 'Savoie_reanimation']
hospitals = ['Paris_hospital', 'Marseilles_hospital', 'Lyon_hospital', 'Savoie_hospital']
axes = covid.plot(y=reanimations, legend=True,
           title=title, grid=True, figsize=(20, 15), subplots=True, sharex=True, sharey=False)
hospital = 0
for ax1 in axes:
    ax1.axvspan(lockdown_start, lockdown_end, facecolor='0.1', alpha=0.2)
    ax1.axvspan(lockdown2_start, lockdown2_end, facecolor='0.1', alpha=0.2)
    ax1.axvspan(lockdown3_start, lockdown3_end, facecolor='0.1', alpha=0.2)
    covid.plot(y=hospitals[hospital], secondary_y=True, legend=True, ax=ax1, lw=5, sharey=True)#.\
    hospital += 1
    # get_figure().savefig('hospitalizations.png')
plt.tight_layout
plt.savefig('hospitalizations.png')


# covid.plot(style='k--', y=['Paris_fit', 'Bordeaux_fit', 'Strasbourg_fit', 'Marseilles_fit', 'Lyon_fit'], ax=ax1, legend=False).\
#     get_figure().savefig('hospitalizations.png')
# covid.plot(style='k--', y=['France_fit', ], secondary_y=True, ax=ax1, legend=False)

# covid.plot(y="France", legend=True, secondary_y=True, ax=ax1, lw=4, grid=True, style='r').get_figure().savefig('hospitalizations.png')

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

