from lxml import html as lh
import requests
import pandas as pd
from datetime import datetime


page = requests.get('https://www.santepubliquefrance.fr/maladies-et-traumatismes/maladies-et-infections-respiratoires/infection-a-coronavirus/articles/infection-au-nouveau-coronavirus-sars-cov-2-covid-19-france-et-monde')
# Store the contents of the website under doc
doc = lh.fromstring(page.content)

# tree = html.fromstring(page.content)
# france_regional_table = tree.xpath('//*[@id="block-236243"]/div[2]/div/div/table/tbody')
tr_elements = doc.xpath('//tr')
date_element = doc.xpath('//*[@id="block-236243"]/div[2]/div/h4')
data_date = date_element[0].text_content()
data_date = data_date.replace('Nombre de cas rapportés par région au ', '')
data_date = data_date.split('h ', 1)[0]
data_date_object = datetime.strptime(data_date, '%d/%m/%Y à %H')

# Create empty list
col = []
i = 0
# For each row, store each first element (header) and an empty list
for t in tr_elements[0]:
    i += 1
    name = t.text_content()
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
        data = t.text_content()
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

Dict = {title: column for (title, column) in col}
df = pd.DataFrame(Dict)
df.to_pickle(data_date_object.strftime('%Y%m%d_%H'))
