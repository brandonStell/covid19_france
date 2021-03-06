from lxml import html as lh
import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
# from pandas.plotting import register_matplotlib_converters
import matplotlib.dates as mdates
from scipy.stats import norm

# register_matplotlib_converters()


# class Parameter:
#     def __init__(self, value):
#             self.value = value
#
#     def set(self, value):
#             self.value = value
#
#     def __call__(self):
#             return self.value
#
#
# def fit(function, parameters, y, x=None):
#     def f(params):
#         i = 0
#         for p in parameters:
#             p.set(params[i])
#             i += 1
#         return y - function(x)
#
#     if x is None: x = np.arange(y.shape[0])
#     p = [param() for param in parameters]
#     return optimize.leastsq(f, p)


# define your function:
def f(x): return height() * np.exp(-((x-mu())/sigma())**2)


def fetch_data_from_sante_publique_website():
    page = requests.get('https://www.santepubliquefrance.fr/maladies-et-traumatismes/maladies-et-infections-respiratoires/infection-a-coronavirus/articles/infection-au-nouveau-coronavirus-sars-cov-2-covid-19-france-et-monde')
    # Store the contents of the website under doc
    doc = lh.fromstring(page.content)

    tr_elements = doc.xpath('//tr')
    date_element = doc.xpath('//*[@id="block-236243"]/div[2]/div/h4')
    date_element2 = doc.xpath('/html/body/div[1]/div[1]/div/div/div/div[2]/div[1]/div/div[4]/div[1]/h4/span[1]')
    return tr_elements, date_element


def get_data_from_tr_elements(tr_elements):
    # Create empty list
    col = []
    i = 0
    # For each row, store each first element (header) and an empty list
    for t in tr_elements[0]:
        i += 1
        name = t.text_content().replace(' ', '')
        print('%d:"%s"' % (i, name))
        col.append((name, []))

    # Since out first row is the header, data is stored on the second row onwards
    for j in range(1, len(tr_elements)):
        # T is our j'th row
        T = tr_elements[j]

        # If row is not of size 10, the //tr data is not from our table
        if len(T) != 2:
            break

        # i is the index of our column
        i = 0

        # Iterate through each element of the row
        for t in T.iterchildren():
            data = t.text_content().replace(' ', '')
            # print(data)
            # Check if row is empty
            if i > 0:
                # Convert any numerical value to integers
                try:
                    data = int(data)
                except:
                    pass
            # Append the data to the empty list of the i'th column
            col[i][1].append(data)
            # Increment i for the next column
            i += 1
        dict = {title: column for (title, column) in col}
        df = pd.DataFrame(dict)

    return df


def reorganize_new_data(df, data_date_object):
    df.set_index('Régiondenotification', inplace=True)
    df = df.T
    df['date'] = data_date_object.strftime('%Y-%m-%d')
    df.date = df.date.astype('datetime64')
    df.reset_index(inplace=True)
    return df


def get_date_from_sp_website_element(date_element):
    data_date = date_element[0].text_content()
    data_date = data_date.replace('Nombre de cas rapportés par région au ', '')
    data_date = data_date.split('h ', 1)[0]
    data_date_object = datetime.strptime(data_date, '%d/%m/%Y à %Hh')  # might need to remove h
    return data_date_object


def save_new_data(df):
    df.to_pickle(new_data.date.iloc[0].date().strftime('%Y%m%d'))


def load_cumulative_date():
    df = pd.read_pickle('cumulative.pkl')
    return df


def add_new_data_to_cumulative(new_df, cum_df):
    cum_df = cum_df.set_index('date').append(new_df.set_index('date'), sort=True).reset_index()
    cum_df.drop(columns='index', inplace=True)
    # cum_df.drop(columns='level_0', inplace=True)
    # cum_df = cum_df.merge(new_df, on='date', how='outer')
    cum_df.fillna(0, inplace=True)
    return cum_df.drop_duplicates().sort_values(by='date').reset_index(drop=True)


def save_cumulative_data(cum_df):
    cum_df.to_pickle('cumulative.pkl')


# def update_readme():



sante_publique_table_elements, data_date_element = fetch_data_from_sante_publique_website()
new_data = get_data_from_tr_elements(sante_publique_table_elements)
new_data_date = get_date_from_sp_website_element(data_date_element)
new_data = reorganize_new_data(new_data, new_data_date)
save_new_data(new_data)
cumulative_data = load_cumulative_date()
cumulative_data = add_new_data_to_cumulative(new_data, cumulative_data)
save_cumulative_data(cumulative_data)

# gaussian starting guesses
height = Parameter(50000)
mu = Parameter(pd.Timestamp('2020-05-01').value)
sigma = Parameter(pd.to_timedelta('60 days').value)
# data = cumulative_data['Ile-de-France'].values
data = cumulative_data['TotalMétropole'].diff().values
data_x = cumulative_data.date.astype('int').values
# fit! (given that data is an array with the data to fit)
popt, pcov = curve_fit(f, data_x, data)
# predictions, dunno = fit(f, [mu, sigma, height], data, x=data_x)
# print('Predicted peak:', pd.to_datetime(predictions[0]))
# print('Max simultaneous infections:', format(predictions[2], '4.2e'))
title = 'Predicted peak:' + \
        str(pd.to_datetime(predictions[0])) + \
        ', Max infections / day:' + \
        format(predictions[2], '4.2e')

fig, ax = plt.subplots()
cumulative_data.set_index('date').plot(
    # x='date',
    y={'GrandEst', 'Ile-de-France', 'TotalMétropole'},
    kind='bar',
    ax=ax,
    rot=30,
    # title=title,
    figsize=(20, 15),
    # subplots=True,
    # x_compact=True,
    grid=True)\
    .get_figure().savefig('summary.png')

test = pd.DataFrame(pd.date_range(start='2/1/2020', end='06/01/2020'), columns=['date'])
test['fit'] = predictions[2] * np.exp(-((test.date.astype('int') - predictions[0])/predictions[1])**2)
fig2, ax2 = plt.subplots()
test.set_index('date').fit.plot(x='date',
                                ax=ax2,
                                label='Gaussian Fit',
                                legend=True,
                                figsize=(20, 15),
                                title=title
                                ).get_figure().savefig('fit.png')
fig3, ax3 = plt.subplots()
cumulative_data.set_index('date')['TotalMétropole'].diff().plot(ax=ax3,
                                                                figsize=(20, 15),
                                                                title='New Infections in France',
                                                                label='France',
                                                                # kind='bar',
                                                                # secondary_y='TotalMétropole',
                                                                grid=True,
                                                                legend=True
                                                                )
cumulative_data.set_index('date')['Ile-de-France'].diff().plot(ax=ax3,
                                                               label='Paris',
                                                               legend=True,
                                                               grid=True,
                                                               # kind='bar',
                                                               # secondary_y='TotalMétropole',
                                                               ).get_figure().savefig('new_infections.png')
# test.fit.plot(x='date', ax=ax)
# height() * np.exp(-((x-mu())/sigma())**2)
