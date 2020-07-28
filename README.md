- **Case 1**: Scraping a product department at Walmart Canada's website
- **Case 2**: Processing CSV files to extract clean information

### Product
The Product model contains basic product information:

*Product*

- Store
- Barcodes (a list of UPC/EAN barcodes)
- SKU (the product identifier in the store)
- Brand
- Name
- Description
- Package
- Image URL
- Category
- URL

### BranchProduct
The BranchProduct model contains the attributes of a product that are specific for a store's branch. The same product can be available/unavailable or have different prices at different branches.

*BranchProduct*

- Branch
- Product
- Stock
- Price

## Case 1

The product information needed:

*Product*

- Store `Walmart`
- Barcodes `60538887928`
- SKU `10295446`
- Brand `Great Value`
- Name `Spring Water`
- Description `Convenient and refreshing, Great Value Spring Water is a healthy option...`
- Package `24 x 500ml`
- Image URL `["https://i5.walmartimages.ca/images/Large/887/928/999999-60538887928.jpg", "https://i5.walmartimages.ca/images/Large/089/6_1/400896_1.jpg", "https://i5.walmartimages.ca/images/Large/88_/nft/605388879288_NFT.jpg"]`
- Category `Grocery|Pantry, Household & Pets|Drinks›Water|Bottled Water`
- URL `https://www.walmart.ca/en/ip/great-value-24pk-spring-water/6000143709667`

*BranchProduct*
 - Product `<product_id>`
 - Branch `3124`
 - Stock `426`
 - Price `2.27`

For now, we are only interested in the [Fruits](https://www.walmart.ca/en/grocery/fruits-vegetables/fruits/N-3852) category.

## Case 2

- **PRODUCTS.csv**: Contains the product's basic information.
- **PRICES-STOCK.csv**: Contains information about the prices and stock.

Put together all the data, process it, and store it in our database. 
