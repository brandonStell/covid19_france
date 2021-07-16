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
    # filename = filename_element[0].text.split('-')
    # current_data_date = datetime.strptime("".join(filename[3:7]), '%Y%m%d%Hh%M')
    csv_link_element = doc.xpath('/html/body/section/section[5]/div[2]/div[1]/article[1]/div/section/dl/div[2]/dd/a')
    csv_link = csv_link_element[0].attrib['href']
    # if (max_saved_date + pd.Timedelta('0 days')) < pd.to_datetime(datetime.today().strftime('%Y-%m-%d')):
    with requests.Session() as s:
        download = s.get(csv_link)
    decoded_content = download.content.decode('utf-8')
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

data_url = 'https://www.data.gouv.fr/fr/datasets/donnees-des-urgences-hospitalieres-et-de-sos-medecins-relatives-a-lepidemie-de-covid-19/'
# data_url = 'https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/'
raw = fetch_data_from_data_dot_gouv_website(data_url)
raw.date_de_passage = raw.date_de_passage.astype('datetime64')
raw.set_index('date_de_passage', inplace=True)

covid = pd.DataFrame()
covid['Paris'] = raw.where(raw.sursaud_cl_age_corona == '0')\
    .where(raw.dep == 75)\
    .nbre_hospit_corona.dropna()
covid['Marseille'] = raw.where(raw.sursaud_cl_age_corona == '0')\
    .where(raw.dep == 13)\
    .nbre_hospit_corona.dropna()
covid['Bordeaux'] = raw.where(raw.sursaud_cl_age_corona == '0')\
    .where(raw.dep == '33')\
    .nbre_hospit_corona.dropna()
covid['Strasbourg'] = raw.where(raw.sursaud_cl_age_corona == '0')\
    .where(raw.dep == 67)\
    .nbre_hospit_corona.dropna()
covid['Lyon'] = raw.where(raw.sursaud_cl_age_corona == '0')\
    .where(raw.dep == 69)\
    .nbre_hospit_corona.dropna()
covid['Haute Savoie'] = raw.where(raw.sursaud_cl_age_corona == '0')\
    .where(raw.dep == 74)\
    .nbre_hospit_corona.dropna()

covid['France'] = raw.where(raw.sursaud_cl_age_corona == '0').dropna().nbre_hospit_corona.resample('D').sum()
# covid = covid.reindex(pd.date_range('2-24-2020', '7-1-2020'))

lockdown_start = pd.to_datetime('3-16-2020')
lockdown_end = pd.to_datetime('5-10-2020')
# lockdown_end = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))
lockdown2_start = pd.to_datetime('10-30-2020')
lockdown2_end = pd.to_datetime('12-1-2020')
lockdown3_start = pd.to_datetime('4-3-2021')
lockdown3_end = pd.to_datetime('4-25-2021')

title = "COVID-19 hospital admissions per day"
# fig1, ax1 = plt.subplots()
axes = covid.plot(y=['Paris', 'Marseille', 'Strasbourg', 'Bordeaux', 'Lyon', 'Haute Savoie'],
           legend=True,
           title=title,
           grid=True,
           figsize=(20, 15), subplots=True, sharex=True, sharey=False)
for ax1 in axes:
    ax1.axvspan(lockdown_start, lockdown_end, facecolor='0.1', alpha=0.2)
    ax1.axvspan(lockdown2_start, lockdown2_end, facecolor='0.1', alpha=0.2)
    ax1.axvspan(lockdown3_start, lockdown3_end, facecolor='0.1', alpha=0.2)
plt.tight_layout()
plt.savefig('emergency_admissions.png')

