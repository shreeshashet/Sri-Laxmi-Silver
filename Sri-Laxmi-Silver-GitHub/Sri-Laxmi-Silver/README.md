# Sri Laxmi Silver online shop

## Local setup

Install the pinned dependencies, configure the environment, then create the shop tables:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m flask --app run:app db upgrade
.\.venv\Scripts\python.exe -m flask --app run:app seed-shop-demo
.\.venv\Scripts\python.exe run.py
```

For GitHub, upload the extracted project files rather than uploading the ZIP as the repository source. Keep `.env` private; configure your own environment values from `.env.example`.

The seed command adds four clearly marked sample listings. They have no real prices or stock and cannot be purchased. Replace them with confirmed products before publishing a live catalog.

## Store owner tools

Set `SHOP_ADMIN_EMAILS` in `.env` to the email used for the store owner's existing account (multiple emails may be comma-separated). Register or sign in with that account, then visit `/shop/admin` to manage products, named collections, stock, orders, coupons, and review approvals. The admin overview highlights unconfirmed orders, live products, low/out-of-stock items, and pending reviews; order search/status filters and inventory search/status filters are included. Product image URLs have a preview. Do not expose the admin email setting or development secret publicly.

The public site uses the Sri Laxmi Silver name and links to the official Instagram profile. It includes a storefront, an approximate store-location map, and dedicated About (`/shop/about`), Visit & Contact (`/shop/contact`), ordering-help/FAQ (`/shop/help`), and privacy notice (`/shop/privacy`) pages. Free search basics include structured business metadata, `robots.txt`, and a generated `sitemap.xml`.

Customers must sign in to check out and can see their submitted orders at `/shop/account`. Checkout saves an order and prepares a WhatsApp message; an order is not confirmed until the store replies. Store staff can create named collections at `/shop/admin`; published collections are available at `/shop/collections` and each collection has its own storefront page. Assign products to a collection from the add/edit product forms. Reviews are restricted to fulfilled purchases and appear publicly only after approval. Coupons can be fixed-amount or percentage discounts and can be disabled by the store owner.

Delivery is offered around 5 km from the store, but the site collects the address and leaves coverage and charges for the owner to confirm; it does not calculate distance automatically. The delivery estimate is within seven days. Online payments are intentionally not connected yet, so checkout remains a WhatsApp order request. Paid Instagram/Meta ads, ad tracking, automated customer emails, traffic analytics, and AI recommendations are not connected and must not be advertised as active features. The Instagram profile link is live; automated Instagram feeds require approved post URLs or official Meta integration credentials. The official Instagram profile is [@sri_laxmi_silver_](https://www.instagram.com/sri_laxmi_silver_/).