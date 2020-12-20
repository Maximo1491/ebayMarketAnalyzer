# Initial Code: https://oaref.blogspot.com/2019/01/web-scraping-using-python-part-2.html

import time
import datetime
import matplotlib
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
from scipy import stats
import random
import requests_cache
import math


# XML Formatter: https://jsonformatter.org/xml-formatter

def get_quantity_hist(sold_hist_url, sold_list, sleep_len=0.4, verbose=False):
    time.sleep(
            sleep_len * random.uniform(0, 1))  # eBays servers will kill your connection if you hit them too frequently
    with requests_cache.disabled():  # We don't want to cache all the calls into the individual listings, they'll never be repeated
        source = requests.get(sold_hist_url).text
    soup = BeautifulSoup(source, 'lxml')

    # items = soup.find_all('tr')

    table = soup.find_all('table', attrs={'border': '0', 'cellpadding': '5', 'cellspacing': '0',
                                          'width' : '100%'})

    purchas_hist = table[0]

    trs = purchas_hist.find_all('tr')

    for r in trs:
        tds = r.find_all('td')
        if len(tds) > 0:
            # buyer = tds[1].text
            price = float(tds[2].text.replace('US $', '').replace(',', ''))
            quantity = int(tds[3].text)
            sold_date = tds[4].text.split()[0]
            sold_time = tds[4].text.split()[1]

            sold_datetime = datetime.datetime.strptime(sold_date + ' ' + sold_time, '%b-%d-%y %H:%M:%S')
            sold_datetime = sold_datetime.replace(second=0, microsecond=0)

            sold_date = datetime.datetime.strptime(tds[4].text.split()[0], '%b-%d-%y')
            if verbose: print(price, quantity, sold_datetime)

            sold_list.append([price, quantity, sold_date, sold_datetime])

    offer_hist = table[1]

    trs = offer_hist.find_all('tr')

    for r in trs:
        tds = r.find_all('td', )
        if len(tds) > 0:
            try:
                # buyer = tds[1].text
                accepted = tds[2].text
                quantity = int(tds[3].text)
                sold_date = tds[4].text.split()[0]
                sold_time = tds[4].text.split()[1]

                sold_datetime = datetime.datetime.strptime(sold_date + ' ' + sold_time, '%b-%d-%y %H:%M:%S')
                sold_datetime = sold_datetime.replace(second=0, microsecond=0)
                sold_date = datetime.datetime.strptime(tds[4].text.split()[0], '%b-%d-%y')

                if accepted == 'Accepted':
                    if verbose: print(accepted, quantity, sold_datetime)
                    sold_list.append(['', quantity, sold_date, sold_datetime])
            except Exception as e:
                accepted = 'None'
    return sold_list


def ebay_scrape(base_url, df, min_date='', feedback=False, quantity_hist=False, sleep_len=0.4, brand_list=[],
                model_list=[], verbose=False):
    for x in range(1, 5):

        time.sleep(
                sleep_len * random.uniform(0,
                                           1))  # eBays servers will kill your connection if you hit them too frequently
        url = base_url + str(x)

        if x == 4:
            source = requests.get(url).text
        else:
            with requests_cache.disabled():  # We don't want to cache all the calls into the individual listings, they'll never be repeated
                source = requests.get(url).text
        soup = BeautifulSoup(source, 'lxml')
        items = soup.find_all('li', attrs={'class': 's-item'})

        if verbose: print(x, len(items), url)

        for n, item in enumerate(items):
            if n > 0:
                try:
                    item_link = item.find('a', class_='s-item__link')['href']
                except Exception as e:
                    item_link = 'None'

                if verbose: print('URL:', item_link)

                try:
                    orig_item_datetime = '2020 ' + item.find('span', class_='s-item__endedDate').text
                    item_datetime = datetime.datetime.strptime(orig_item_datetime, '%Y %b-%d %H:%M')

                    # if UK: item_datetime = datetime.datetime.strptime(orig_item_datetime, '%Y %d-%b %H:%M')

                except Exception as e:
                    try:

                        orig_item_datetime = item.find('span', class_='s-item__title--tagblock__COMPLETED').text
                        orig_item_datetime = orig_item_datetime.replace('Sold item', '').replace('Sold', '').strip()
                        item_datetime = datetime.datetime.strptime(orig_item_datetime, '%d %b %Y')
                        item_datetime = item_datetime.replace(hour=0, minute=0, second=0, microsecond=0)

                    except Exception as e:
                        item_datetime = 'None'

                if verbose: print('Datetime:', item_datetime)

                # Only need to add new records
                if not df[['Link', 'Sold Datetime']].isin({'Link': [item_link], 'Sold Datetime': [item_datetime]}).all(
                        axis='columns').any():

                    try:
                        item_title = item.find('h3', class_='s-item__title').text
                    except Exception as e:
                        item_title = 'None'

                    if verbose: print('Title:', item_title)

                    try:
                        orig_item_date = '2020 ' + item.find('span', class_='s-item__endedDate').text
                        item_date = datetime.datetime.strptime(orig_item_date, '%Y %b-%d %H:%M')
                        # if UK: item_date = datetime.datetime.strptime(orig_item_date, '%Y %d-%b %H:%M')
                        item_date = item_date.replace(hour=0, minute=0, second=0, microsecond=0)

                    except Exception as e:
                        try:
                            orig_item_date = item.find('span', class_='s-item__title--tagblock__COMPLETED').text
                            orig_item_date = orig_item_date.replace('Sold item', '').replace('Sold', '').strip()
                            item_date = datetime.datetime.strptime(orig_item_date, '%d %b %Y')
                            item_date = item_date.replace(hour=0, minute=0, second=0, microsecond=0)

                        except Exception as e:

                            item_date = 'None'

                    if verbose: print('Date:', item_date)

                    try:
                        item_desc = item.find('div', class_='s-item__subtitle').text
                    except Exception as e:
                        item_desc = 'None'

                    if verbose: print('Desc: ', item_desc)

                    try:
                        item_price = item.find('span', class_='s-item__price').text
                        item_price = float(
                                item_price.replace('+', '').replace(' shipping', '').replace('postage', '').replace(
                                        '$', '').replace('£', '').strip())  # if UK: £
                    except Exception as e:
                        item_price = -1

                    if verbose: print('Price:', item_price)

                    try:
                        item_shipping = item.find('span', class_='s-item__shipping s-item__logisticsCost').text
                        if item_shipping.upper().find("FREE") == -1:
                            item_shipping = float(
                                    item_shipping.replace('+', '').replace(' shipping', '').replace('postage',
                                                                                                    '').replace(
                                            '$', '').replace('£', '').strip())  # if UK: £
                        else:
                            item_shipping = 0
                    except Exception as e:
                        item_shipping = 0

                    if verbose: print('Shipping:', item_shipping)

                    try:
                        item_tot = item_price + item_shipping
                    except Exception as e:
                        item_tot = 'None'

                    if verbose: print('Total:', item_tot)

                    quantity_sold = 1
                    sold_list = []
                    multi_list = False
                    store = False

                    if feedback or quantity_hist:
                        try:
                            time.sleep(sleep_len * random.uniform(0, 1))
                            with requests_cache.disabled():  # We don't want to cache all the calls into the individual listings, they'll never be repeated
                                source = requests.get(item_link).text
                            soup = BeautifulSoup(source, 'lxml')

                            try:
                                seller = soup.find_all('span', attrs={'class': 'mbg-nw'})
                                seller = seller[0].text

                                seller_fb = soup.find_all('span', attrs={'class': 'mbg-l'})
                                seller_fb = int(seller_fb[0].find('a').text)

                                store_id = soup.find_all('div', attrs={'id': 'storeSeller'})

                                if len(store_id[0].text) > 0:
                                    store = True

                                try:
                                    iitem = soup.find_all('a', attrs={'class': 'vi-txt-underline'})
                                    quantity_sold = int(iitem[0].text.split()[0])
                                    multi_list = True

                                    if quantity_hist:
                                        sold_hist_url = items[0]['href']
                                        sold_list = get_quantity_hist(sold_hist_url, sold_list, sleep_len=sleep_len,
                                                                      verbose=verbose)

                                except Exception as e:
                                    sold_hist_url = ''

                            except Exception as e:
                                try:
                                    oitems = soup.find_all('a',
                                                           attrs={'class': 'nodestar-item-card-details__view-link'})
                                    orig_link = oitems[0]['href']

                                    time.sleep(sleep_len * random.uniform(0, 1))
                                    with requests_cache.disabled():  # We don't want to cache all the calls into the individual listings, they'll never be repeated
                                        source = requests.get(orig_link).text
                                    soup = BeautifulSoup(source, 'lxml')

                                    seller = soup.find_all('span', attrs={'class': 'mbg-nw'})
                                    seller = seller[0].text

                                    seller_fb = soup.find_all('span', attrs={'class': 'mbg-l'})
                                    seller_fb = int(seller_fb[0].find('a').text)

                                    store_id = soup.find_all('div', attrs={'id': 'storeSeller'})

                                    if len(store_id[0].text) > 0:
                                        store = True

                                    try:
                                        nnitems = soup.find_all('a', attrs={'class': 'vi-txt-underline'})
                                        quantity_sold = int(nnitems[0].text.split()[0])
                                        multi_list = True

                                        if quantity_hist and quantity_sold > 1:
                                            sold_hist_url = nnitems[0]['href']
                                            sold_list = get_quantity_hist(sold_hist_url, sold_list, sleep_len=sleep_len,
                                                                          verbose=verbose)

                                    except Exception as e:
                                        sold_hist_url = ''
                                except Exception as e:
                                    # print(url)
                                    # print(e)
                                    seller = 'None'
                                    seller_fb = 'None'
                        except Exception as e:
                            seller = 'None'
                            seller_fb = 'None'
                    else:
                        seller = 'None'
                        seller_fb = 'None'

                    if verbose: print('Seller: ', seller)
                    if verbose: print('Seller Feedback: ', seller_fb)
                    if verbose: print('Quantity Sold: ', quantity_sold)
                    if verbose: print()

                    brand = ''
                    title = item_title
                    for b in brand_list:
                        if b in title:
                            b = b.replace(' ', '')
                            brand = b
                    if verbose: print('Brand', brand)

                    model = ''
                    for m in model_list:
                        if m in title:
                            m = m.replace(' ', '')
                            model = m
                    if verbose: print('Model', model)

                    sold_list = np.array(sold_list)

                    if sold_list.size == 0:
                        try:
                            cap_sum = df[(df['Link'] == item_link)]['Quantity'].sum()
                        except Exception as e:
                            cap_sum = 0

                        df__new = {'Title'          : item_title, 'Brand': brand, 'Model': model,
                                   'description'    : item_desc, 'Price': item_price,
                                   'Shipping'       : item_shipping, 'Total Price': item_tot, 'Sold Date': item_date,
                                   'Sold Datetime'  : item_datetime, 'Link': item_link, 'Seller': seller,
                                   'Multi Listing'  : multi_list, 'Quantity': quantity_sold - cap_sum,
                                   'Seller Feedback': seller_fb,
                                   'Ignore'         : 0, 'Store': store}

                        if verbose: print(df__new)

                        if not df[['Link', 'Sold Datetime']].isin(
                                {'Link': [item_link], 'Sold Datetime': [item_datetime]}).all(
                                axis='columns').any() and item_tot is not 'None' and (quantity_sold - cap_sum) > 0:
                            df = df.append(df__new, ignore_index=True)
                            # Considered processing as went along, more efficient to just remove duplicates in postprocessing
                    else:
                        for sale in sold_list:
                            sale_price = item_price
                            if sale[0]:
                                sale_price = sale[0]
                            df__new = {'Title'        : item_title, 'Brand': brand, 'Model': model,
                                       'description'  : item_desc, 'Price': sale_price,
                                       'Shipping'     : item_shipping, 'Total Price': item_tot, 'Sold Date': sale[2],
                                       'Sold Datetime': sale[2], 'Link': item_link, 'Seller': seller,
                                       'Multi Listing': multi_list, 'Quantity': sale[1], 'Seller Feedback': seller_fb,
                                       'Ignore'       : 0, 'Store': store}

                            # There's a chance when we get to multiitem listings we'd be reinserting data, this is to prevent it
                            if not df[['Link', 'Sold Datetime']].isin(
                                    {'Link': [item_link], 'Sold Datetime': [item_datetime]}).all(
                                    axis='columns').any() and item_tot is not 'None':
                                df = df.append(df__new, ignore_index=True)

                        tot_sale_quant = np.sum(sold_list[:, 1])

                        if tot_sale_quant < quantity_sold:
                            # On some listings the offer list has scrolled off (only shows latest 100) despite some beint accepted
                            # In order to not lose the data I just shove everything into one entry, assuming the regular price
                            # Not perfect, but no great alternatives
                            # The main issue here of course is that now I'm assigning a bunch of sales to a semi-arbitrary date
                            df__new = {'Title'        : item_title, 'Brand': brand, 'Model': model,
                                       'description'  : item_desc, 'Price': item_price,
                                       'Shipping'     : item_shipping, 'Total Price': item_tot,
                                       'Sold Date'    : item_date, 'Sold Datetime': item_datetime, 'Link': item_link,
                                       'Seller'       : seller, 'Quantity': quantity_sold - tot_sale_quant,
                                       'Multi Listing': multi_list, 'Seller Feedback': seller_fb, 'Ignore': 0,
                                       'Store'        : store}
                            # There's a chance when we get to multiitem listings we'd be reinserting data, this is to prevent it
                            if not df[['Link', 'Sold Datetime', 'Quantity']].isin(
                                    {'Link'    : [item_link], 'Sold Datetime': [item_datetime],
                                     'Quantity': [quantity_sold - tot_sale_quant]}).all(
                                    axis='columns').any() and item_tot is not 'None':
                                df = df.append(df__new, ignore_index=True)

        if len(items) < 201:
            break
    return df


def ebay_plot(query, msrp, df, extra_title_text=''):
    # Make Linear Regression Trend Line
    # https://stackoverflow.com/questions/59723501/plotting-a-linear-regression-with-dates-in-matplotlib-pyplot
    df_calc = df[df['Total Price'] > 0]

    med_price = df_calc.groupby(['Sold Date'])['Total Price'].median()
    max_price = df_calc.groupby(['Sold Date'])['Total Price'].max()
    min_price = df_calc.groupby(['Sold Date'])['Total Price'].min()
    max_med = max(med_price)
    max_max = max(max_price)
    min_min = min(min_price)
    median_price = int(df_calc['Total Price'].median())
    count_sold = df.groupby(['Sold Date'])['Quantity'].sum()
    est_break_even = 0
    min_break_even = 0

    fig, ax1 = plt.subplots(figsize=(10, 8))
    color = 'tab:blue'
    plt.title(query.replace("+", " ").split('-', 1)[0].strip() + extra_title_text + ' eBay Sold Prices Over Time')
    ax1.scatter(df['Sold Date'], df['Total Price'], s=10, label='Sold Listing', color=color)

    if msrp > 0:
        # Replace these percentages as need be based on your projections
        estimated_shipping = df.loc[df['Shipping'] > 0]
        estimated_shipping = estimated_shipping['Shipping'].median()
        if math.isnan(estimated_shipping):
            estimated_shipping = 0
        est_tax = 0.0625

        pp_flat_fee = 0.30
        pp_fee_per = 0.029

        est_ebay_fee = 0.1
        min_be_ebay_fee = 0.036  # Basically the best ebay fee percentage possible
        msrp_discount = 0.05  # If drop scalpers are buying off of Amazon with an Amazon Prime account and credit card, they
        # can get 5% cash back, so effectively the MSRP is 5% lower

        est_break_even = round(
                (msrp * (1 + est_tax)) / (1 - est_ebay_fee - pp_fee_per) + pp_flat_fee + estimated_shipping)
        min_break_even = round((msrp * (1 - msrp_discount)) / (1 - min_be_ebay_fee - pp_fee_per) + pp_flat_fee)

        ax1.axhline(y=est_break_even, label='Est. Scalper Break Even - $' + str(int(est_break_even)), color=color,
                    dashes=[2, 2])
        ax1.axhline(y=min_break_even, label='Min Scalper Break Even - $' + str(int(min_break_even)), color=color,
                    dashes=[4, 1])

        # Estimated assuming 6.25% tax, $15 shipping, and the multiplier for ebay/Paypal fees determined by
        # https://www.ebayfeescalculator.com/usa-ebay-calculator/ where not an eBay store, seller is above standard, and
        # paying with PayPal with Item Category being Computers/Tablets & Networking

        ax1.axhline(y=msrp, label='MSRP - $' + str(msrp), color=color)
    ax1.plot(med_price, color='cyan', label='Median Price - $' + str(median_price))
    # plt.plot(sold_date, m * sold_date + b)
    ax1.set_ylabel("Sold Price", color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.tick_params(axis='x', rotation=30)
    formatter = ticker.FormatStrFormatter('$%1.0f')
    ax1.yaxis.set_major_formatter(formatter)
    ax1.set_xlabel("Sold Date")
    ax1.set_ylim(top=min(1.5 * max_med, max_max), bottom=min(min_min * 0.95, msrp * 0.95))

    color = 'tab:red'
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    ax2.set_ylabel("Quantity Sold", color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    tot_sold = int(df['Quantity'].sum())
    ax2.plot(count_sold[:-1], color=color, label='Total Sold - ' + str(tot_sold))

    # Plotting Trendline
    y = df['Total Price']
    x = [i.toordinal() for i in df['Sold Date']]

    slope, intercept, r, p, std_err = stats.linregress(x, y)

    def myfunc(x):
        return slope * x + intercept

    mymodel = list(map(myfunc, x))

    ax3 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    if msrp > 0:
        est_msrp = datetime.datetime.fromordinal(int((msrp - intercept) / slope)).strftime("%y-%m-%d")

    if slope >= 0:
        ax3.plot(x, mymodel, dashes=[4, 1], label='Linear Trend Line')
    elif msrp > 0:
        ax3.plot(x, mymodel, dashes=[4, 1], label='Linear Trend Line - Est MSRP Date - ' + str(est_msrp))

    ax3.set_ylim(top=min(1.5 * max_med, max_max), bottom=min(min_min * 0.95, msrp * 0.95))
    ax3.set(yticklabels=[])
    ax3.set(ylabel=None)
    ax3.tick_params(left=False, right=False)

    # instruct matplotlib on how to convert the numbers back into dates for the x-axis
    l = matplotlib.dates.AutoDateLocator()
    f = matplotlib.dates.AutoDateFormatter(l)

    ax3.xaxis.set_major_locator(l)
    ax3.xaxis.set_major_formatter(f)

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines3, labels3 = ax3.get_legend_handles_labels()
    ax1.legend(lines + lines2 + lines3, labels + labels2 + labels3)

    plt.savefig('Images/' + query + extra_title_text)
    plt.show()

    return median_price, est_break_even, min_break_even, tot_sold


def ebay_search(query, msrp=0, min_price=0, max_price=10000, min_date=datetime.datetime(2020, 1, 1), verbose=False,
                extra_title_text='', run_cached=False, feedback=False, quantity_hist=False, sleep_len=0.4,
                brand_list=[], model_list=[], sacat=0):
    start = time.time()
    requests_cache.clear()
    print(query)

    # https://stackoverflow.com/questions/35807605/create-a-file-if-it-doesnt-exist?lq=1
    try:
        df = pd.read_excel('Spreadsheets/' + query + extra_title_text + '.xlsx', index_col=0)
        df = df.astype({'Brand': 'object'})

    except:
        # if file does not exist, create it
        dict = {'Title'      : [], 'Brand': [], 'Model': [], 'description': [], 'Price': [], 'Shipping': [],
                'Total Price': [],
                'Sold Date'  : [], 'Sold Datetime': [], 'Quantity': [], 'Multi Listing': [],
                'Seller'     : [], 'Seller Feedback': [], 'Link': [], 'Store': []}
        df = pd.DataFrame(dict)
        df = df.astype({'Brand': 'object'})
        df = df.astype({'Model': 'object'})

    if not run_cached:
        price_ranges = [min_price, max_price]

        # Determine price ranges to search with
        i = 0
        while i != len(price_ranges) - 1:
            time.sleep(
                    sleep_len * random.uniform(0,
                                               1))  # eBays servers will kill your connection if you hit them too frequently
            url = 'https://www.ebay.com/sch/i.html?_from=R40&_nkw=' + str(
                    query.replace(" ", "+").replace(',', '%2C').replace('(', '%28').replace(')',
                                                                                            '%29')) + '&_sacat=' + str(
                    sacat) + '&LH_PrefLoc=1&LH_Sold=1&LH_Complete=1&_udlo=' + str(
                    price_ranges[i]) + '&_udhi=' + str(
                    price_ranges[i + 1]) + '&rt=nc&_ipg=200&_pgn=4'

            source = requests.get(url).text
            soup = BeautifulSoup(source, 'lxml')
            items = soup.find_all('li', attrs={'class': 's-item'})
            if verbose: print(price_ranges, len(items), i, price_ranges[i], price_ranges[i + 1], url)

            if len(items) == 201 and round(price_ranges[i + 1] - price_ranges[i], 2) > 0.01:
                # If there's only one cent difference between the two just increment, we need to do some special logic below
                midpoint = round((price_ranges[i] + price_ranges[i + 1]) / 2, 2)
                price_ranges = price_ranges[:i + 1] + [midpoint] + price_ranges[i + 1:]
            elif len(items) == 201 and round(price_ranges[i + 1] - price_ranges[i], 2) == 0.01:
                # If there is a one cent difference between the two, we can have eBay just return that specific price to get a little bit finer detail
                price_ranges = price_ranges[:i + 1] + [price_ranges[i]] + [price_ranges[i + 1]] + price_ranges[i + 1:]
                i += 2
            else:
                i += 1
        print(price_ranges)
        for i in range(len(price_ranges) - 1):
            url = 'https://www.ebay.com/sch/i.html?_from=R40&_nkw=' + str(
                    query.replace(" ", "+").replace(',', '%2C').replace('(', '%28').replace(')',
                                                                                            '%29')) + '&_sacat=' + str(
                    sacat) + '&LH_PrefLoc=1&LH_Sold=1&LH_Complete=1&_udlo=' + str(
                    price_ranges[i]) + '&_udhi=' + str(
                    price_ranges[i + 1]) + '&rt=nc&_ipg=200&_pgn='
            if verbose: print(price_ranges[i], price_ranges[i + 1], url)
            print(price_ranges[i], price_ranges[i + 1], url)
            df = ebay_scrape(url, df, min_date, feedback=feedback, quantity_hist=quantity_hist, sleep_len=sleep_len,
                             brand_list=brand_list, model_list=model_list, verbose=verbose)

            # Best to save semiregularly in case eBay kills the connection
            df = pd.DataFrame.drop_duplicates(df)
            df.to_excel('Spreadsheets/' + str(query) + extra_title_text + '.xlsx')
            requests_cache.remove_expired_responses()

    df = df[df['Ignore'] == 0]

    median_price, est_break_even, min_break_even, tot_sold = ebay_plot(query, msrp, df, extra_title_text)

    last_week = df.loc[
        df['Sold Date'] >= (datetime.datetime.now() - datetime.timedelta(days=7)).replace(hour=0, minute=0, second=0,
                                                                                          microsecond=0)]
    tot_sales = (df['Total Price'] * df['Quantity']).sum()
    tot_ini_sales = (df['Price'] * df['Quantity']).sum()

    ebay_profit = float(tot_sales) * 0.08
    # Estimate, eBay can take up to 10% for a fairly "new" seller and as little as 3.6% for a top selling store
    # I assume most scalpers are "new" sellers so 8% seems fair

    pp_profit = float(tot_sold) * 0.30 + float(tot_ini_sales) * 0.029

    print('Past Week Median Price: $' + str(last_week['Total Price'].median()))
    print('Median Price: $' + str(median_price))
    print('Past Week Average Price: $' + str(round(last_week['Total Price'].mean(), 2)))
    print('Average Price: $' + str(round(df['Total Price'].mean(), 2)))
    print('Total Sold: ' + str(tot_sold))
    print('Total Sales: $' + str(round(tot_sales, 2)))
    print('PayPal Profit: $' + str(int(pp_profit)))
    print('Est eBay Profit: $' + str(int(ebay_profit)))
    if msrp > 0:
        total_scalp_val = round(tot_sales - tot_sold * msrp, 2)
        print('Total Scalpers/eBay Profit: $' + str(total_scalp_val))
        print('Estimated Break Even Point for Scalpers: $' + str(est_break_even))
        print('Minimum Break Even Point for Scalpers: $' + str(min_break_even))
    elapsed = time.time() - start
    print("Runtime: %02d:%02d:%02d" % (elapsed // 3600, elapsed // 60 % 60, elapsed % 60))
    print('')
    return df


def median_plotting(dfs, names, title, msrps=[]):
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
    min_msrp = 100
    plt.figure()  # In this example, all the plots will be in one figure.
    plt.ylabel("% of MSRP")
    plt.xlabel("Sale Date")
    plt.tick_params(axis='y')
    plt.tick_params(axis='x', rotation=30)
    plt.title(title)
    for i in range(len(dfs)):
        ci = i % (len(colors) - 1)
        med_price = dfs[i].groupby(['Sold Date'])['Total Price'].median() / msrps[i] * 100
        min_msrp = min(100, min(med_price))
        plt.plot(med_price, colors[ci], label=names[i])
    plt.ylim(bottom=min_msrp)
    plt.legend()
    plt.tight_layout()
    plt.savefig("Images/" + title)
    plt.show()


run_all_feedback = True
run_all_hist = True
run_cached = True
sleep_len = 0.5
brand_list = ['FOUNDERS', 'ASUS', 'MSI', 'EVGA', 'GIGABYTE', 'ZOTAC', 'INNO3D', 'PNY', 'SAPPHIRE', 'COLORFUL', 'ASROCK',
              'POWERCOLOR', 'XFX', 'POWER COLOR']
model_list = ['XC3', 'TRINITY', 'FTW3', 'FOUNDERS', 'STRIX', 'EKWB', 'TUF', 'SUPRIM', 'VENTUS', 'MECH', 'EVOKE', 'TRIO',
              'FTW3', 'KINGPIN', 'K|NGP|N', 'AORUS', 'WATERFORCE', 'XTREME', 'MASTER', 'TRINITY', 'AMP']

requests_cache.install_cache('main_cache', backend='sqlite', expire_after=300)

# raise SystemExit(0)



# https://realpython.com/caching-external-api-requests/

df_darkhero = ebay_search('ASUS Dark Hero -image -jpeg -img -picture -pic -jpg', 399, 400, 1000, run_cached=run_cached,
                          feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='',
                          sleep_len=sleep_len, brand_list=brand_list, model_list=model_list)

# Zen 3 Analysis
df_5950x = ebay_search('5950X -image -jpeg -img -picture -pic -jpg', 799, 400, 2200, feedback=run_all_feedback,
                       run_cached=run_cached, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len)
df_5900x = ebay_search('5900X -image -jpeg -img -picture -pic -jpg', 549, 499, 2050, feedback=run_all_feedback,
                       run_cached=run_cached, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len)
df_5800x = ebay_search('5800X -image -jpeg -img -picture -pic -jpg', 449, 400, 1000, feedback=run_all_feedback,
                       run_cached=run_cached, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len)
df_5600x = ebay_search('5600X -image -jpeg -img -picture -pic -jpg', 299, 250, 1000, feedback=run_all_feedback,
                       run_cached=run_cached, quantity_hist=run_all_hist, min_date=datetime.datetime(2020, 11, 1),
                       sleep_len=sleep_len)
median_plotting([df_5950x, df_5900x, df_5800x, df_5600x], ['5950X', '5900X', '5800X', '5600X'], 'Zen 3 Median Pricing',
                [799, 549, 449, 299])

# Big Navi Analysis
df_6800 = ebay_search('RX 6800 -XT -image -jpeg -img -picture -pic -jpg', 579, 400, 2500, feedback=run_all_feedback,
                      run_cached=run_cached, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len,
                      brand_list=brand_list, model_list=model_list)
df_6800xt = ebay_search('RX 6800 XT -image -jpeg -img -picture -pic -jpg', 649, 850, 2000, feedback=run_all_feedback,
                        run_cached=run_cached, quantity_hist=run_all_hist,
                        extra_title_text='', sleep_len=sleep_len, brand_list=brand_list,
                        model_list=model_list)  # There are some $5000+, but screw with graphs
df_6900 = ebay_search('RX 6900 -image -jpeg -img -picture -pic -jpg', 999, 100, 999999, feedback=run_all_feedback,
                      run_cached=run_cached, quantity_hist=run_all_hist, min_date=datetime.datetime(2020, 12, 8),
                      extra_title_text='', sleep_len=sleep_len, brand_list=brand_list,
                      model_list=model_list)  # Not out until December 8
median_plotting([df_6800, df_6800xt, df_6900], ['RX 6800', 'RX 6800 XT', 'RX 6900'], 'Big Navi Median Pricing',
                [579, 649, 999])

# RTX 30 Series Analysis
df_3060 = ebay_search('RTX 3060 -image -jpeg -img -picture -pic -jpg', 399, 200, 1300, feedback=run_all_feedback,
                      run_cached=run_cached, quantity_hist=run_all_hist, min_date=datetime.datetime(2020, 12, 1),
                      extra_title_text='', sleep_len=sleep_len, brand_list=brand_list, model_list=model_list)
df_3070 = ebay_search('RTX 3070 -image -jpeg -img -picture -pic -jpg', 499, 499, 1300, feedback=run_all_feedback,
                      run_cached=run_cached, quantity_hist=run_all_hist, min_date=datetime.datetime(2020, 10, 29),
                      extra_title_text='', sleep_len=sleep_len, brand_list=brand_list, model_list=model_list)
df_3080 = ebay_search('RTX 3080 -image -jpeg -img -picture -pic -jpg', 699, 550, 10000, feedback=run_all_feedback,
                      run_cached=run_cached, quantity_hist=run_all_hist, min_date=datetime.datetime(2020, 9, 17),
                      extra_title_text='', sleep_len=sleep_len, brand_list=brand_list, model_list=model_list)
df_3090 = ebay_search('RTX 3090 -image -jpeg -img -picture -pic -jpg', 1499, 550, 10000, feedback=run_all_feedback,
                      run_cached=run_cached, quantity_hist=run_all_hist, min_date=datetime.datetime(2020, 9, 17),
                      extra_title_text='', sleep_len=sleep_len, brand_list=brand_list, model_list=model_list)
median_plotting([df_3060, df_3070, df_3080, df_3090], ['3060', '3070', '3080', '3090'], 'RTX 30 Series Median Pricing',
                [399, 499, 699, 1499])

# PS5 Analysis (All time)
df_ps5_digital = ebay_search('PS5 Digital -image -jpeg -img -picture -pic -jpg', 399, 300, 11000, run_cached=run_cached,
                             feedback=run_all_feedback, quantity_hist=run_all_hist,
                             min_date=datetime.datetime(2020, 9, 16), extra_title_text='', sleep_len=sleep_len,
                             sacat=139971)
df_ps5_disc = ebay_search('PS5 -digital -image -jpeg -img -picture -pic -jpg', 499, 450, 11000, run_cached=run_cached,
                          feedback=run_all_feedback, quantity_hist=run_all_hist,
                          min_date=datetime.datetime(2020, 9, 16), extra_title_text='', sleep_len=sleep_len,
                          sacat=139971)
median_plotting([df_ps5_digital, df_ps5_disc], ['PS5 Digital', 'PS5 Disc'], 'PS5 Median Pricing', [299, 499])

# Xbox Analysis (All time)
df_xbox_s = ebay_search('Xbox Series S -image -jpeg -img -picture -pic -jpg', 299, 250, 11000, run_cached=run_cached,
                        feedback=run_all_feedback, quantity_hist=run_all_hist, min_date=datetime.datetime(2020, 9, 22),
                        extra_title_text='', sleep_len=sleep_len, sacat=139971)
df_xbox_x = ebay_search('Xbox Series X -image -jpeg -img -picture -pic -jpg', 499, 350, 11000, run_cached=run_cached,
                        feedback=run_all_feedback, quantity_hist=run_all_hist, min_date=datetime.datetime(2020, 9, 22),
                        extra_title_text='', sleep_len=sleep_len, sacat=139971)
median_plotting([df_xbox_s, df_xbox_x], ['Xbox Series S', 'Xbox Series X'], 'Xbox Median Pricing',
                [299, 499])

# Zen 2 data
df_3300X = ebay_search('3300X -combo -custom', 120, 160, 250, run_cached=run_cached,
                       feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len)

df_3950X = ebay_search('3950X -image -jpeg -img -picture -pic -jpg', 749, 350, 1200, run_cached=run_cached,
                       feedback=run_all_feedback, quantity_hist=False, extra_title_text='', sleep_len=sleep_len)

df_3900X = ebay_search('3900X -combo -custom', 499, 230, 920, run_cached=run_cached,
                       feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len)

df_3900XT = ebay_search('3900XT -combo -custom', 499, 200, 800, run_cached=run_cached,
                        feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len)

df_3800XT = ebay_search('3800XT -combo -custom', 399, 60, 800, run_cached=run_cached,
                        feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len)

df_3800X = ebay_search('3800X -combo -custom', 399, 60, 600, run_cached=run_cached,
                       feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len)

df_3700X = ebay_search('3700X -combo -custom', 329, 100, 551, run_cached=run_cached,
                       feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len)

df_3600XT = ebay_search('3600XT -combo -custom', 249, 149, 600, run_cached=run_cached,
                        feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len)

df_3600X = ebay_search('3600X -combo -custom -roku', 249, 40, 520, run_cached=run_cached,
                       feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len)

df_3600 = ebay_search('(AMD, Ryzen) 3600 -combo -custom -roku -3600x -3600xt', 249, 30, 361, run_cached=run_cached,
                      feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len)

df_3100 = ebay_search('(AMD, Ryzen) 3100 -combo -custom -radeon', 99, 79, 280, run_cached=run_cached,
                      feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len)

# Turing GPUs

df_2060 = ebay_search('rtx 2060 -super', 299, 100, 650, run_cached=run_cached, feedback=run_all_feedback,
                      quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len,
                      brand_list=brand_list, model_list=model_list)

df_2060S = ebay_search('rtx 2060 super', 399, 79, 10008, run_cached=run_cached, feedback=run_all_feedback,
                       quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len,
                       brand_list=brand_list, model_list=model_list)

df_2070 = ebay_search('rtx 2070 -super', 499, 79, 280, run_cached=run_cached, feedback=run_all_feedback,
                      quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len,
                      brand_list=brand_list, model_list=model_list)

df_2070S = ebay_search('rtx 2070 super', 499, 79, 1600, run_cached=run_cached, feedback=run_all_feedback,
                       quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len,
                       brand_list=brand_list, model_list=model_list)

df_2080 = ebay_search('rtx 2080 -super -ti', 699, 250, 1300, run_cached=run_cached, feedback=run_all_feedback,
                      quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len,
                      brand_list=brand_list, model_list=model_list)

df_2080S = ebay_search('rtx 2080 super -ti', 699, 299, 1600, run_cached=run_cached, feedback=run_all_feedback,
                       quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len,
                       brand_list=brand_list, model_list=model_list)

#df_2080Ti = ebay_search('rtx 2080 ti -super', 999, 400, 3800, run_cached=run_cached,                        feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len,                        brand_list=brand_list, model_list=model_list)

# Radeon RX 5000 Series (not bothering to separate out 4 vs 8 GB models nor the 50th anniversary
df_5500XT = ebay_search('rx 5500 xt', 169, 80, 400, run_cached=run_cached, feedback=run_all_feedback,
                        quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len,
                        brand_list=brand_list, model_list=model_list)

df_5600XT = ebay_search('rx 5600 xt', 279, 200, 750, run_cached=run_cached, feedback=run_all_feedback,
                        quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len,
                        brand_list=brand_list, model_list=model_list)

df_5700 = ebay_search('rx 5700 -xt', 349, 250, 550, run_cached=run_cached, feedback=run_all_feedback,
                      quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len,
                      brand_list=brand_list, model_list=model_list)

df_5700XT = ebay_search('rx 5700 xt', 499, 150, 850, run_cached=run_cached, feedback=run_all_feedback,
                        quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len,
                        brand_list=brand_list, model_list=model_list)

# PS4 Analysis
df_ps4 = ebay_search('ps4 -pro -repair -box -broken -parts -bad', 399, 60, 5000, run_cached=run_cached,
                     feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='', sleep_len=sleep_len,
                     sacat=139971)
df_ps4_pro = ebay_search('PS4 pro -repair -box -broken -parts -bad', 399, 60, 5000, run_cached=run_cached,
                         feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='',
                         sleep_len=sleep_len, sacat=139971)

# Xbox One Analysis
df_xbox_one_s = ebay_search('xbox one s -pro -repair -box -broken -parts -bad', 299, 250, 11000, run_cached=run_cached,
                            feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='',
                            sleep_len=sleep_len, sacat=139971)
df_xbox_one_x = ebay_search('xbox one x -repair -box -broken -parts -bad', 499, 350, 11000, run_cached=run_cached,
                            feedback=run_all_feedback, quantity_hist=run_all_hist, extra_title_text='',
                            sleep_len=sleep_len, sacat=139971)

# Xbox Analysis (Post Launch)
df_xbox_s_ld = ebay_search('Xbox Series S -image -jpeg -img -picture -pic -jpg', 299, 250, 11000,
                           min_date=datetime.datetime(2020, 11, 10), run_cached=True, extra_title_text=' (Post Launch)')
df_xbox_x_ld = ebay_search('Xbox Series X -image -jpeg -img -picture -pic -jpg', 499, 350, 11000,
                           min_date=datetime.datetime(2020, 11, 10), run_cached=True, extra_title_text=' (Post Launch)')
median_plotting([df_xbox_s_ld, df_xbox_x_ld], ['Xbox Series S', 'Xbox Series X'], 'Xbox Median Pricing (Post Launch)',
                [299, 499])

# PS5 Analysis (Post Launch)
df_ps5_digital_ld = ebay_search('PS5 Digital -image -jpeg -img -picture -pic -jpg', 399, 300, 11000,
                                min_date=datetime.datetime(2020, 11, 12), run_cached=True,
                                extra_title_text=' (Post Launch)')
df_ps5_disc_ld = ebay_search('PS5 -digital -image -jpeg -img -picture -pic -jpg', 499, 450, 11000,
                             min_date=datetime.datetime(2020, 11, 12), run_cached=True,
                             extra_title_text=' (Post Launch)')
median_plotting([df_ps5_disc_ld, df_ps5_digital_ld], ['PS5 Digital', 'PS5 Disc'], 'PS5 Median Pricing (Post Launch)',
                [299, 499])