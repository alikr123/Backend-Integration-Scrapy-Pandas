import os

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship, sessionmaker
from models import BranchProduct, Product, Base

engine = create_engine("sqlite:///db.sqlite")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = PROJECT_DIR.replace("integrations\\richart_wholesale_club",'')
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
PRODUCTS_PATH = os.path.join(ASSETS_DIR, "PRODUCTS.csv")
PRICES_STOCK_PATH = os.path.join(ASSETS_DIR, "PRICES-STOCK.csv")


def process_csv_files():
    products_df = pd.read_csv(filepath_or_buffer=PRODUCTS_PATH, sep="|",)
    prices_stock_df = pd.read_csv(filepath_or_buffer=PRICES_STOCK_PATH, sep="|",)

    #Filter Stock Prices df with Greater than 0 Stock and 'MM' 'RHSM' Branches
    prices_stock_df_filtered = prices_stock_df.loc[prices_stock_df['STOCK']>0]
    prices_stock_df_filtered = prices_stock_df_filtered.loc[prices_stock_df_filtered['BRANCH'].isin(['MM', 'RHSM'])]
    final_prices_stock_df = prices_stock_df_filtered[['SKU', 'BRANCH', 'STOCK', 'PRICE']]
    final_prices_stock_df.columns=['sku', 'branch', 'stock', 'price']

    #Removing HTML Tags
    products_df['New Description'] = products_df['DESCRIPTION'].replace({'<p>':'','</p>':''}, regex=True)
    #Combining Categories
    products_df['New Category'] = products_df['CATEGORY'] +	'|' + products_df['SUB_CATEGORY'] + '|' + products_df['SUB_SUB_CATEGORY']

    #Getting Package information from Description
    conditions = [products_df['New Description'].str.contains('KG'),
    products_df['New Description'].str.contains('1UN'),
    products_df['New Description'].str.contains('GRS'),
    products_df['New Description'].str.contains('PZA'),
    products_df['New Description'].str.contains('2UN'),
    products_df['New Description'].str.contains('LT'),
    products_df['New Description'].str.contains('MG'),
    products_df['New Description'].str.contains('OZ'),
    products_df['New Description'].str.contains('GAL'),
    products_df['New Description'].str.contains('ML'),
    products_df['New Description'].str.contains('MILI')]
    choices = ['KG','1UN','GRS','PZA','2UN','LT','MG','OZ','GAL','ML','MILI']
    products_df['package'] = np.select(conditions, choices, default='N/A')

    products_df['store'] = "Richart's"
    products_df['url'] = ''


    final_products = products_df[['store', 'SKU', 'BARCODES', 'BRAND', 'NAME', 'New Description', 'package', 'IMAGE_URL', 'New Category', 'url']]
    final_products.columns=['store' , 'sku', 'barcodes', 'brand', 'name', 'description', 'package', 'image_url', 'category', 'url']
    final_products['name'].fillna('N/A', inplace=True)
    final_products = final_products.drop_duplicates() #Removing Duplicates

    session = Session()

    #------VERY SLOW ------ THERE MUST BE A BETTER APPROACH
    '''
    for index, p in final_products.iterrows():
        product = Product(store=p['store'],
        sku = p['sku'],
        barcodes = p['barcodes'],
        brand = p['brand'],
        name = p['name'],
        description = p['description'],
        package = p['package'],
        image_url = p['image_url'],
        category = p['category'],
        url = p['url'])
        session.add(product)

        bp_rows = final_prices_stock_df.loc[final_prices_stock_df['sku'] == p['sku']]
        for index1, bp in bp_rows.iterrows():
            branchproduct = BranchProduct(branch = bp['branch'], stock = bp['stock'], price = bp['price'], product=product)
            session.add(branchproduct)
    '''

    #------ FASTER APPROACH ------ BUT UNABLE TO MAP PRODUCT_ID
    # session.bulk_insert_mappings(Product, final_products.to_dict(orient='records'))
    # session.bulk_insert_mappings(Product, final_prices_stock_df.to_dict(orient='records'))

    #--------------Realized this after submission-------------#
    final_products['id'] = final_products.index
    final_products =final_products[['id', 'store' , 'sku', 'barcodes', 'brand', 'name', 'description', 'package', 'image_url', 'category', 'url']]
    #Merging on SKU
    final_prices_stock_df_pid = pd.merge(final_prices_stock_df, final_products, how='inner', left_on='sku', right_on='sku')
    final_prices_stock_df_pid = final_prices_stock_df_pid[['id', 'branch', 'stock', 'price']]
    final_prices_stock_df_pid.columns = ['product_id', 'branch', 'stock', 'price']

    #Bulk Insert to both tables
    session.bulk_insert_mappings(Product, final_products.to_dict(orient='records'))
    session.bulk_insert_mappings(BranchProduct, final_prices_stock_df_pid.to_dict(orient='records'))


    session.commit()
    session.close()

if __name__ == "__main__":
    process_csv_files()
