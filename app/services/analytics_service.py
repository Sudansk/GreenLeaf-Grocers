import json
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.db import get_db

class AnalyticsService:
    @staticmethod
    def get_dashboard_metrics():
        """
        Calculate KPI cards:
        - Total revenue
        - Total sales (transaction count)
        - Average bill value
        - Total active products
        - Low-stock count
        - Stock turnover ratio
        """
        db = get_db()

        # Sales KPIs
        sales_df = pd.read_sql_query("SELECT id, grand_total, created_at FROM sales", db)
        if not sales_df.empty:
            total_revenue = float(sales_df['grand_total'].sum())
            total_sales_count = int(len(sales_df))
            avg_bill_value = round(float(sales_df['grand_total'].mean()), 2)
        else:
            total_revenue = 0.0
            total_sales_count = 0
            avg_bill_value = 0.0

        # Product & Inventory KPIs
        prod_df = pd.read_sql_query("SELECT id, quantity, cost_price, selling_price, reorder_level FROM products", db)
        if not prod_df.empty:
            total_products = int(len(prod_df))
            low_stock_count = int((prod_df['quantity'] <= prod_df['reorder_level']).sum())
            current_inventory_cost = float((prod_df['quantity'] * prod_df['cost_price']).sum())
        else:
            total_products = 0
            low_stock_count = 0
            current_inventory_cost = 0.0

        # Stock turnover = Total COGS / Current Inventory Cost
        cogs_df = pd.read_sql_query("SELECT (cost_price * quantity) as item_cogs FROM sale_items", db)
        if not cogs_df.empty and current_inventory_cost > 0:
            total_cogs = float(cogs_df['item_cogs'].sum())
            stock_turnover = round(total_cogs / current_inventory_cost, 2)
        else:
            stock_turnover = 0.0

        return {
            'total_revenue': total_revenue,
            'total_sales_count': total_sales_count,
            'avg_bill_value': avg_bill_value,
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'stock_turnover': stock_turnover
        }

    @staticmethod
    def get_daily_revenue_trend(days=30):
        """Analyze daily revenue trend using Pandas."""
        db = get_db()
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query = """
            SELECT DATE(created_at) as sale_date, SUM(grand_total) as daily_revenue, COUNT(id) as transaction_count
            FROM sales
            WHERE DATE(created_at) >= ?
            GROUP BY DATE(created_at)
            ORDER BY sale_date ASC
        """
        df = pd.read_sql_query(query, db, params=(cutoff_date,))
        if df.empty:
            # Generate empty series for the period so chart renders cleanly
            date_range = pd.date_range(end=datetime.today(), periods=7).strftime('%Y-%m-%d')
            df = pd.DataFrame({'sale_date': date_range, 'daily_revenue': [0.0]*7, 'transaction_count': [0]*7})
        return df

    @staticmethod
    def get_monthly_revenue_trend():
        """Analyze monthly revenue using Pandas."""
        db = get_db()
        query = """
            SELECT strftime('%Y-%m', created_at) as sale_month, SUM(grand_total) as monthly_revenue, COUNT(id) as transaction_count
            FROM sales
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY sale_month ASC
        """
        df = pd.read_sql_query(query, db)
        return df

    @staticmethod
    def get_top_selling_products(limit=10):
        """Top selling products by volume and revenue using Pandas."""
        db = get_db()
        query = """
            SELECT p.name as product_name, p.category,
                   SUM(si.quantity) as units_sold,
                   SUM(si.line_total) as total_revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            GROUP BY p.id, p.name, p.category
            ORDER BY units_sold DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, db, params=(limit,))
        return df

    @staticmethod
    def get_category_sales_share():
        """Analyze category-wise revenue share using Pandas."""
        db = get_db()
        query = """
            SELECT p.category, SUM(si.line_total) as category_revenue, SUM(si.quantity) as category_units
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            GROUP BY p.category
            ORDER BY category_revenue DESC
        """
        df = pd.read_sql_query(query, db)
        return df

    @staticmethod
    def get_slow_moving_products(days=30, sales_threshold=2):
        """
        Identify products with little or no sales in the last N days.
        """
        db = get_db()
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # All active products
        products_df = pd.read_sql_query(
            "SELECT id, name, sku, category, quantity, selling_price, cost_price FROM products",
            db
        )
        if products_df.empty:
            return pd.DataFrame()

        # Sales in last 30 days
        sales_query = """
            SELECT si.product_id, SUM(si.quantity) as sold_in_period
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.created_at) >= ?
            GROUP BY si.product_id
        """
        sales_df = pd.read_sql_query(sales_query, db, params=(cutoff_date,))

        # Merge
        merged = pd.merge(products_df, sales_df, left_on='id', right_on='product_id', how='left')
        merged['sold_in_period'] = merged['sold_in_period'].fillna(0).astype(int)
        
        # Filter where sold <= sales_threshold and stock > 0
        slow_df = merged[(merged['sold_in_period'] <= sales_threshold) & (merged['quantity'] > 0)].copy()
        slow_df['inventory_value'] = (slow_df['quantity'] * slow_df['selling_price']).round(2)
        slow_df = slow_df.sort_values(by=['sold_in_period', 'quantity'], ascending=[True, False])

        return slow_df

    @staticmethod
    def get_payment_method_stats():
        """Breakdown of sales by payment method."""
        db = get_db()
        query = """
            SELECT payment_method, COUNT(id) as count, SUM(grand_total) as total_amount
            FROM sales
            GROUP BY payment_method
            ORDER BY total_amount DESC
        """
        return pd.read_sql_query(query, db)

    # Plotly interactive chart builders
    @staticmethod
    def build_daily_revenue_chart(df):
        """Build Plotly daily revenue trend chart."""
        if df.empty or 'sale_date' not in df:
            fig = go.Figure()
            fig.update_layout(title="No sales data available yet")
            return json.loads(fig.to_json())

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['sale_date'],
            y=df['daily_revenue'],
            mode='lines+markers',
            name='Daily Revenue ($)',
            line=dict(color='#10b981', width=3, shape='spline'),
            marker=dict(size=7, color='#047857'),
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.12)'
        ))

        fig.update_layout(
            title={'text': 'Daily Revenue Trend (Last 30 Days)', 'x': 0.05, 'font': {'size': 16, 'color': '#064e3b'}},
            xaxis_title="Date",
            yaxis_title="Revenue ($)",
            plot_bgcolor='rgba(255, 255, 255, 1)',
            paper_bgcolor='rgba(255, 255, 255, 1)',
            hovermode='x unified',
            height=430,
            margin=dict(l=45, r=30, t=45, b=45),
            xaxis=dict(showgrid=True, gridcolor='#f3f4f6', automargin=True),
            yaxis=dict(showgrid=True, gridcolor='#f3f4f6', automargin=True)
        )
        return json.loads(fig.to_json())

    @staticmethod
    def build_top_products_chart(df):
        """Build Plotly horizontal bar chart for top 10 products with ample margin and visible values."""
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="No product sales recorded yet")
            return json.loads(fig.to_json())

        # Sort ascending so the top product is at the top of the horizontal bar chart
        df_sorted = df.sort_values(by='units_sold', ascending=True)
        max_val = float(df_sorted['units_sold'].max()) if not df_sorted.empty else 10.0

        fig = go.Figure(go.Bar(
            x=df_sorted['units_sold'],
            y=df_sorted['product_name'],
            orientation='h',
            marker=dict(
                color=df_sorted['units_sold'],
                colorscale=[[0, '#6ee7b7'], [1, '#059669']],
                line=dict(color='#047857', width=1)
            ),
            text=df_sorted['units_sold'].apply(lambda x: f"{x} units"),
            textposition='outside',
            cliponaxis=False,
            textfont=dict(size=11, color='#065f46'),
            hovertemplate="<b>%{y}</b><br>Units Sold: %{x}<extra></extra>"
        ))

        fig.update_layout(
            title={'text': 'Top 10 Selling Products by Volume', 'x': 0.05, 'font': {'size': 16, 'color': '#064e3b'}},
            xaxis_title="Units Sold",
            yaxis_title="",
            plot_bgcolor='rgba(255, 255, 255, 1)',
            paper_bgcolor='rgba(255, 255, 255, 1)',
            height=430,
            margin=dict(l=190, r=45, t=45, b=45),
            bargap=0.22,
            xaxis=dict(
                showgrid=True,
                gridcolor='#f3f4f6',
                range=[0, max_val * 1.22],
                automargin=True,
                tickfont=dict(size=11, color='#4b5563')
            ),
            yaxis=dict(
                showgrid=False,
                automargin=True,
                tickfont=dict(size=11, color='#1f2937')
            )
        )
        return json.loads(fig.to_json())

    @staticmethod
    def build_category_share_chart(df):
        """Build Plotly centered donut chart for category share with clean legend positioning."""
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="No category sales recorded yet")
            return json.loads(fig.to_json())

        total_rev = float(df['category_revenue'].sum()) if not df.empty else 0.0
        if total_rev > 0:
            legend_labels = [f"{cat} ({rev/total_rev*100:.1f}%)" for cat, rev in zip(df['category'], df['category_revenue'])]
        else:
            legend_labels = df['category'].tolist()

        palette = ['#059669', '#10b981', '#34d399', '#6ee7b7', '#047857', '#065f46', '#14b8a6', '#0d9488', '#a7f3d0']

        fig = go.Figure(data=[go.Pie(
            labels=legend_labels,
            values=df['category_revenue'],
            hole=0.52,
            domain=dict(x=[0.05, 0.95], y=[0.18, 0.98]),
            marker=dict(colors=palette, line=dict(color='#ffffff', width=2)),
            textinfo='percent',
            textposition='inside',
            insidetextorientation='horizontal',
            textfont=dict(size=12, color='#ffffff'),
            customdata=list(zip(df['category'], df['category_revenue'])),
            hovertemplate="<b>%{customdata[0]}</b><br>Revenue: $%{customdata[1]:,.2f}<br>Share: %{percent}<extra></extra>"
        )])

        fig.update_layout(
            title={'text': 'Category-wise Sales Share', 'x': 0.05, 'font': {'size': 16, 'color': '#064e3b'}},
            plot_bgcolor='rgba(255, 255, 255, 1)',
            paper_bgcolor='rgba(255, 255, 255, 1)',
            height=390,
            margin=dict(l=20, r=20, t=45, b=25),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=0.14,
                xanchor="center",
                x=0.5,
                font=dict(size=11, color='#334155')
            )
        )
        return json.loads(fig.to_json())

    @staticmethod
    def build_payment_method_chart(df):
        """Build Plotly pie/bar chart for payment distribution."""
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="No payment records yet")
            return json.loads(fig.to_json())

        colors = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6']
        fig = go.Figure(data=[go.Pie(
            labels=df['payment_method'],
            values=df['total_amount'],
            hole=0.48,
            domain=dict(x=[0.05, 0.95], y=[0.18, 0.98]),
            marker=dict(colors=colors, line=dict(color='#ffffff', width=2)),
            textinfo='label+percent',
            textposition='inside',
            insidetextorientation='horizontal',
            textfont=dict(size=12, color='#ffffff'),
            hovertemplate="<b>%{label}</b><br>Total: $%{value:,.2f}<br>Transactions: %{percent}<extra></extra>"
        )])

        fig.update_layout(
            title={'text': 'Revenue by Payment Method', 'x': 0.05, 'font': {'size': 16, 'color': '#064e3b'}},
            plot_bgcolor='rgba(255, 255, 255, 1)',
            paper_bgcolor='rgba(255, 255, 255, 1)',
            height=390,
            margin=dict(l=20, r=20, t=45, b=25),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=0.14,
                xanchor="center",
                x=0.5,
                font=dict(size=11, color='#334155')
            )
        )
        return json.loads(fig.to_json())
