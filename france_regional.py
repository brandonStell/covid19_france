from lxml import html as lh
import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
# from pandas.plotting import register_matplotlib_converters
from scipy import optimize
import matplotlib.dates as mdates
from scipy.stats import norm

# register_matplotlib_converters()


class Parameter:
    def __init__(self, value):
            self.value = value

    def set(self, value):
            self.value = value

    def __call__(self):
            return self.value


def fit(function, parameters, y, x = None):
    def f(params):
        i = 0
        for p in parameters:
            p.set(params[i])
            i += 1
        return y - function(x)

    if x is None: x = np.arange(y.shape[0])
    p = [param() for param in parameters]
    return optimize.leastsq(f, p)


# define your function:
def f(x): return height() * np.exp(-((x-mu())/sigma())**2)


def fetch_data_from_sante_publique_website():
    page = requests.get('https://www.santepubliquefrance.fr/maladies-et-traumatismes/maladies-et-infections-respiratoires/infection-a-coronavirus/articles/infection-au-nouveau-coronavirus-sars-cov-2-covid-19-france-et-monde')
    # Store the contents of the website under doc
    doc = lh.fromstring(page.content)

    tr_elements = doc.xpath('//tr')
    date_element = doc.xpath('//*[@id="block-236243"]/div[2]/div/h4')
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
    data_date_object = datetime.strptime(data_date, '%d/%m/%Y à %H')
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
height = Parameter(5000)
mu = Parameter(pd.Timestamp('2020-04-01').value)
sigma = Parameter(pd.to_timedelta('10 days').value)
# data = cumulative_data['Ile-de-France'].values
data = cumulative_data['TotalMétropole'].values
data_x = cumulative_data.date.astype('int').values


# fit! (given that data is an array with the data to fit)
predictions, dunno = fit(f, [mu, sigma, height], data, x=data_x)
# print('Predicted peak:', pd.to_datetime(predictions[0]))
# print('Max simultaneous infections:', format(predictions[2], '4.2e'))
title = 'Predicted peak:' + \
        str(pd.to_datetime(predictions[0])) + \
        ', Max simultaneous infections:' + \
        format(predictions[2], '4.2e')

# fig, ax = plt.subplots()
cumulative_data.plot(
    x='date',
    y={'GrandEst', 'Ile-de-France', 'TotalMétropole'},
    kind='bar',
    # ax=ax,
    rot=30,
    title=title,
    figsize=(20, 15),
    grid=True
).get_figure().savefig('summary.png')
