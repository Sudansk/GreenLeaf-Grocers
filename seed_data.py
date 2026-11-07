import os
import random
from datetime import datetime, timedelta
from app import create_app, db
from app.models.user import User
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.sale import Sale

def seed():
    app = create_app()
    with app.app_context():
        print("Initializing database schema...")
        db.init_db()

        # 1. Seed Users
        print("Seeding users...")
        users_data = [
            ('admin', 'admin123', 'Arthur Pendelton (Store Manager)', 'admin'),
            ('cashier', 'cashier123', 'Elena Rodriguez', 'cashier'),
            ('sarah', 'cashier123', 'Sarah Jenkins', 'cashier')
        ]
        user_ids = {}
        for username, password, full_name, role in users_data:
            existing = User.get_by_username(username)
            if not existing:
                uid = User.create(username, password, full_name, role)
                user_ids[username] = uid
                print(f"  Created user: {username} ({role})")
            else:
                user_ids[username] = existing['id']

        admin_id = user_ids.get('admin')
        cashier_ids = [user_ids.get('cashier'), user_ids.get('sarah')]

        # 2. Seed Suppliers
        print("Seeding suppliers...")
        suppliers_data = [
            ("SunFresh Organic Farms", "Marcus Vance", "marcus@sunfresh.com", "+1-555-0101", "742 Evergreen Terrace, Farmville, CA"),
            ("Meadow Valley Dairy Co.", "Brenda Miller", "orders@meadowvalleydairy.com", "+1-555-0102", "12 Dairy Lane, Madison, WI"),
            ("Golden Crust Artisan Bakery", "Pierre Dubois", "pierre@goldencrust.com", "+1-555-0103", "88 Baker Street, Portland, OR"),
            ("Apex Beverage Distributors", "Kenji Sato", "sales@apexbev.com", "+1-555-0104", "500 Harbor Blvd, Seattle, WA"),
            ("Harvest Best Staples Ltd.", "Amara Patel", "amara@harvestbest.com", "+1-555-0105", "104 Grain Mill Road, Chicago, IL"),
            ("PureClean Home Supplies", "David Chen", "dchen@pureclean.com", "+1-555-0106", "320 Industrial Parkway, Newark, NJ")
        ]
        
        supplier_id_map = {}
        for name, contact, email, phone, addr in suppliers_data:
            existing = db.query_db("SELECT id FROM suppliers WHERE name = ?", (name,), one=True)
            if not existing:
                sid = Supplier.create(name, contact, email, phone, addr)
                supplier_id_map[name] = sid
                print(f"  Created supplier: {name}")
            else:
                supplier_id_map[name] = existing['id']

        # 3. Seed Products
        print("Seeding products...")
        today = datetime.now().date()

        products_data = [
            # Produce (SunFresh Organic Farms)
            ("Organic Hass Avocados (Pack of 3)", "PROD-AVO-001", "Fresh Produce", 2.20, 4.50, 45, 15, today + timedelta(days=7), "pack", "SunFresh Organic Farms"),
            ("Crisp Gala Apples (1kg)", "PROD-APP-002", "Fresh Produce", 1.80, 3.20, 60, 20, today + timedelta(days=12), "kg", "SunFresh Organic Farms"),
            ("Organic Baby Spinach (250g)", "PROD-SPN-003", "Fresh Produce", 1.10, 2.49, 8, 15, today + timedelta(days=4), "pack", "SunFresh Organic Farms"), # Low stock & Expiring soon
            ("Fresh Cavendish Bananas (1kg)", "PROD-BAN-004", "Fresh Produce", 0.90, 1.89, 75, 20, today + timedelta(days=5), "kg", "SunFresh Organic Farms"), # Expiring soon
            ("Vine-Ripened Roma Tomatoes (1kg)", "PROD-TOM-005", "Fresh Produce", 1.50, 2.99, 35, 15, today + timedelta(days=9), "kg", "SunFresh Organic Farms"),
            ("Organic Baby Carrots (500g)", "PROD-CAR-006", "Fresh Produce", 0.85, 1.79, 4, 10, today + timedelta(days=14), "pack", "SunFresh Organic Farms"), # Low stock & Expiring soon
            ("Fresh Sweet Strawberries (400g)", "PROD-STR-007", "Fresh Produce", 2.40, 4.99, 0, 10, today - timedelta(days=2), "pack", "SunFresh Organic Farms"), # Out of stock & Expired

            # Dairy & Eggs (Meadow Valley Dairy)
            ("Whole Farm Fresh Milk (1 Gallon)", "DAIR-MLK-001", "Dairy & Eggs", 2.10, 3.89, 40, 15, today + timedelta(days=8), "gallon", "Meadow Valley Dairy Co."),
            ("Grass-Fed Salted Butter (250g)", "DAIR-BTR-002", "Dairy & Eggs", 2.00, 3.99, 30, 12, today + timedelta(days=45), "pack", "Meadow Valley Dairy Co."),
            ("Free-Range Grade A Brown Eggs (Dozen)", "DAIR-EGG-003", "Dairy & Eggs", 2.20, 4.29, 50, 15, today + timedelta(days=20), "dozen", "Meadow Valley Dairy Co."),
            ("Greek Style Plain Yogurt (1kg)", "DAIR-YOG-004", "Dairy & Eggs", 2.60, 4.80, 6, 12, today + timedelta(days=10), "tub", "Meadow Valley Dairy Co."), # Low stock & Expiring soon
            ("Aged Sharp Cheddar Block (400g)", "DAIR-CHD-005", "Dairy & Eggs", 3.20, 5.99, 25, 10, today + timedelta(days=90), "block", "Meadow Valley Dairy Co."),
            ("Almond Unsweetened Milk (1L)", "DAIR-ALM-006", "Dairy & Eggs", 1.70, 3.29, 35, 10, today + timedelta(days=60), "carton", "Meadow Valley Dairy Co."),

            # Bakery (Golden Crust Artisan Bakery)
            ("Artisan Sourdough Boule (600g)", "BAKE-SDR-001", "Bakery", 2.10, 4.50, 18, 10, today + timedelta(days=3), "loaf", "Golden Crust Artisan Bakery"), # Expiring soon
            ("Whole Grain Seeded Bread (700g)", "BAKE-WGB-002", "Bakery", 1.80, 3.75, 22, 10, today + timedelta(days=4), "loaf", "Golden Crust Artisan Bakery"), # Expiring soon
            ("French All-Butter Croissants (4-Pack)", "BAKE-CRS-003", "Bakery", 2.40, 4.95, 5, 8, today + timedelta(days=2), "pack", "Golden Crust Artisan Bakery"), # Low stock & Expiring soon
            ("Brioche Burger Buns (6-Pack)", "BAKE-BUN-004", "Bakery", 1.90, 3.99, 15, 8, today + timedelta(days=6), "pack", "Golden Crust Artisan Bakery"),
            ("Blueberry Streusel Muffins (4-Pack)", "BAKE-MUF-005", "Bakery", 2.50, 5.25, 3, 10, today - timedelta(days=1), "pack", "Golden Crust Artisan Bakery"), # Expired & Low stock

            # Beverages (Apex Beverage Distributors)
            ("100% Pure Valencia Orange Juice (1.5L)", "BEV-ORJ-001", "Beverages", 2.50, 4.79, 30, 12, today + timedelta(days=14), "bottle", "Apex Beverage Distributors"),
            ("Sparkling Mineral Water (6x500ml)", "BEV-SPK-002", "Beverages", 2.80, 5.50, 45, 15, today + timedelta(days=180), "pack", "Apex Beverage Distributors"),
            ("Cold Brew Organic Black Coffee (330ml)", "BEV-CBW-003", "Beverages", 1.60, 3.49, 40, 15, today + timedelta(days=45), "can", "Apex Beverage Distributors"),
            ("Natural Spring Water (24x500ml Case)", "BEV-WTR-004", "Beverages", 3.00, 6.99, 50, 20, today + timedelta(days=365), "case", "Apex Beverage Distributors"),
            ("Organic Green Tea Citrus (1L)", "BEV-TEA-005", "Beverages", 1.40, 2.89, 28, 10, today + timedelta(days=120), "bottle", "Apex Beverage Distributors"),

            # Pantry & Staples (Harvest Best Staples Ltd.)
            ("Extra Virgin Cold Pressed Olive Oil (750ml)", "PAN-OIL-001", "Pantry", 5.50, 9.99, 32, 10, today + timedelta(days=300), "bottle", "Harvest Best Staples Ltd."),
            ("Royal Basmati Jasmine Rice (5kg)", "PAN-RCE-001", "Pantry", 6.80, 12.99, 28, 10, today + timedelta(days=400), "bag", "Harvest Best Staples Ltd."),
            ("Organic Whole Wheat Flour (2kg)", "PAN-FLR-001", "Pantry", 2.10, 4.25, 25, 10, today + timedelta(days=240), "bag", "Harvest Best Staples Ltd."),
            ("Italian Penne Rigate Pasta (500g)", "PAN-PST-001", "Pantry", 0.90, 1.99, 70, 20, today + timedelta(days=360), "box", "Harvest Best Staples Ltd."),
            ("Organic Marinara Tomato Sauce (680g)", "PAN-SAU-001", "Pantry", 1.80, 3.69, 42, 15, today + timedelta(days=280), "jar", "Harvest Best Staples Ltd."),
            ("Natural Organic Rolled Oats (1kg)", "PAN-OAT-001", "Pantry", 2.00, 3.99, 35, 12, today + timedelta(days=200), "bag", "Harvest Best Staples Ltd."),
            ("Specialty Himalayan Pink Salt Grinder", "PAN-SLT-002", "Pantry", 3.20, 6.50, 20, 5, today + timedelta(days=500), "unit", "Harvest Best Staples Ltd."), # Slow mover

            # Snacks & Confectionery
            ("Artisan Roasted Almonds Salted (250g)", "SNK-ALM-001", "Snacks", 3.10, 5.99, 30, 10, today + timedelta(days=90), "pack", "Harvest Best Staples Ltd."),
            ("Organic Dark Chocolate 72% (100g)", "SNK-CHO-001", "Snacks", 1.70, 3.49, 45, 15, today + timedelta(days=150), "bar", "Golden Crust Artisan Bakery"),
            ("Non-GMO Sea Salt Tortilla Chips (300g)", "SNK-CHP-001", "Snacks", 1.50, 3.29, 38, 12, today + timedelta(days=75), "bag", "Harvest Best Staples Ltd."),
            ("Gourmet Truffle Flavored Popcorn (150g)", "SNK-POP-002", "Snacks", 2.90, 5.50, 15, 5, today + timedelta(days=60), "bag", "Harvest Best Staples Ltd."), # Slow mover

            # Household & Personal Care (PureClean Home Supplies)
            ("Eco-Friendly Liquid Dish Soap (750ml)", "HOU-DSH-001", "Household", 2.10, 3.99, 25, 10, today + timedelta(days=500), "bottle", "PureClean Home Supplies"),
            ("Recycled Paper Bath Tissue (12 Rolls)", "HOU-PPR-001", "Household", 4.50, 8.99, 35, 10, today + timedelta(days=700), "pack", "PureClean Home Supplies"),
            ("All-Purpose Surface Disinfectant Spray (500ml)", "HOU-SPR-001", "Household", 2.20, 4.49, 28, 10, today + timedelta(days=600), "bottle", "PureClean Home Supplies"),
            ("Heavy Duty Kitchen Trash Bags (30 Pack)", "HOU-BAG-001", "Household", 3.60, 6.99, 22, 8, today + timedelta(days=700), "box", "PureClean Home Supplies"),
            ("Premium Lavender Aromatherapy Linen Mist", "HOU-LAV-002", "Household", 4.50, 9.99, 12, 5, today + timedelta(days=400), "bottle", "PureClean Home Supplies") # Slow mover
        ]

        created_products = []
        for name, sku, cat, cost, price, qty, reorder, exp, unit, sup_name in products_data:
            existing = Product.get_by_sku(sku)
            if not existing:
                sup_id = supplier_id_map.get(sup_name)
                pid = Product.create(
                    name=name, sku=sku, category=cat, cost_price=cost, selling_price=price,
                    quantity=qty, reorder_level=reorder, expiry_date=exp, unit=unit,
                    supplier_id=sup_id, user_id=admin_id
                )
                print(f"  Created product: {name} ({sku})")
                created_products.append({'id': pid, 'name': name, 'price': price, 'cost': cost, 'qty': qty})
            else:
                created_products.append({'id': existing['id'], 'name': existing['name'], 'price': existing['selling_price'], 'cost': existing['cost_price'], 'qty': existing['quantity']})

        # 4. Seed Historical Sales
        sales_count = db.query_db("SELECT COUNT(*) as cnt FROM sales", one=True)['cnt']
        if sales_count == 0:
            print("Seeding realistic historical sales for analytics...")
            customer_names = [
                "Olivia Smith", "Liam Johnson", "Emma Davis", "Noah Wilson", "Sophia Brown",
                "James Anderson", "Isabella Taylor", "Lucas Martinez", "Mia Thomas", "Ethan White",
                "Charlotte Harris", "Benjamin Clark", "Amelia Lewis", "Alexander Robinson", "Harper Walker"
            ]
            payment_methods = ['Cash', 'Card', 'UPI']

            # High volume products: Avocados, Milk, Eggs, Sourdough, Apples, Orange Juice, Pasta
            popular_indices = [0, 1, 3, 7, 9, 13, 18, 25, 29, 31]
            moderate_indices = [2, 4, 8, 11, 14, 19, 20, 23, 24, 27, 33, 34]
            # Notice items at index 28 (Specialty Himalayan Salt), 32 (Truffle Popcorn), 36 (Lavender Mist) will have almost no sales -> Slow moving!

            random.seed(42)
            cur_date = datetime.now()

            # Generate sales across the past 30 days
            for day_offset in range(30, -1, -1):
                sale_day = cur_date - timedelta(days=day_offset)
                # 2 to 4 sales per day
                daily_transactions = random.randint(2, 4)
                for _ in range(daily_transactions):
                    sale_time = sale_day.replace(
                        hour=random.randint(9, 20),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
                    )
                    cashier_id = random.choice(cashier_ids)
                    cust_name = random.choice(customer_names) if random.random() > 0.3 else "Walk-in Customer"
                    cust_phone = f"+1-555-0{random.randint(100, 999)}" if cust_name != "Walk-in Customer" else ""
                    pay_method = random.choice(payment_methods)
                    discount_pct = random.choice([0.0, 0.0, 0.0, 5.0, 10.0])

                    # Select 1 to 4 items for this cart
                    num_items = random.randint(1, 4)
                    chosen_pids = set()
                    cart_items = []
                    subtotal = 0.0

                    for _ in range(num_items):
                        if random.random() < 0.7:
                            idx = random.choice(popular_indices)
                        else:
                            idx = random.choice(moderate_indices)

                        if idx in chosen_pids or idx >= len(created_products):
                            continue
                        chosen_pids.add(idx)

                        p = created_products[idx]
                        qty = random.randint(1, 3)
                        line_total = round(p['price'] * qty, 2)
                        subtotal += line_total
                        cart_items.append({
                            'product_id': p['id'],
                            'name': p['name'],
                            'unit_price': p['price'],
                            'cost_price': p['cost'],
                            'quantity': qty,
                            'line_total': line_total
                        })

                    if not cart_items:
                        continue

                    subtotal = round(subtotal, 2)
                    discount_amount = round((subtotal * discount_pct) / 100.0, 2)
                    grand_total = round(subtotal - discount_amount, 2)
                    inv_num = f"INV-{sale_time.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

                    # Directly insert sale with historical timestamp
                    db.get_db().execute(
                        """INSERT INTO sales (invoice_number, cashier_id, customer_name, customer_phone,
                                              subtotal, discount_percent, discount_amount, tax_amount,
                                              grand_total, payment_method, notes, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, ?, ?, 'Seed Historical Sale', ?)""",
                        (inv_num, cashier_id, cust_name, cust_phone, subtotal, discount_pct, discount_amount,
                         grand_total, pay_method, sale_time.strftime('%Y-%m-%d %H:%M:%S'))
                    )
                    cur_sale_id = db.get_db().execute("SELECT last_insert_rowid()").fetchone()[0]

                    for item in cart_items:
                        db.get_db().execute(
                            """INSERT INTO sale_items (sale_id, product_id, product_name, unit_price, cost_price, quantity, line_total)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (cur_sale_id, item['product_id'], item['name'], item['unit_price'],
                             item['cost_price'], item['quantity'], item['line_total'])
                        )
                        db.get_db().execute(
                            """INSERT INTO stock_movements (product_id, movement_type, quantity, previous_quantity, new_quantity, reference_id, notes, created_by, created_at)
                               VALUES (?, 'SALE', ?, ?, ?, ?, 'Historical sales seed', ?, ?)""",
                            (item['product_id'], item['quantity'], item['quantity'] + 50, 50, inv_num, cashier_id, sale_time.strftime('%Y-%m-%d %H:%M:%S'))
                        )

            db.get_db().commit()
            print("  Seeded 80+ historical sales transactions successfully!")

        print("\nSeed data setup completed successfully!")

if __name__ == '__main__':
    seed()
