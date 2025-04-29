from flask import Blueprint, render_template, request, send_file, flash, jsonify, redirect, url_for
import pandas as pd
import io
from datetime import datetime, timedelta
import json
from decimal import Decimal
import calendar

reports = Blueprint("reports", __name__)

# Helper function to get database connection from app
def get_db():
    from flask import current_app
    return current_app.db

@reports.route("/reports")
def show_reports():
    return render_template("reports.html")

@reports.route("/api/report/summary")
def get_summary_data():
    """Get summary data for dashboard cards"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get date range from query parameters
    date_range = request.args.get('date_range', 'month')
    start_date, end_date = get_date_range(date_range)
    
    # Format dates for SQL query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    try:
        # Get total revenue (bills + non_billed_sales)
        cursor.execute("""
            SELECT COALESCE(SUM(b.total_amount), 0) as billed_revenue
            FROM bills b
            WHERE b.date BETWEEN %s AND %s
        """, (start_date_str, end_date_str))
        billed_revenue = cursor.fetchone()['billed_revenue'] or 0
        
        cursor.execute("""
            SELECT COALESCE(SUM(n.amount), 0) as non_billed_revenue
            FROM non_billed_sales n
            WHERE n.date BETWEEN %s AND %s
        """, (start_date_str, end_date_str))
        non_billed_revenue = cursor.fetchone()['non_billed_revenue'] or 0
        
        total_revenue = float(billed_revenue) + float(non_billed_revenue)
        
        # Get total expenses
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total_expenses
            FROM expenses
            WHERE date BETWEEN %s AND %s
        """, (start_date_str, end_date_str))
        total_expenses = float(cursor.fetchone()['total_expenses'] or 0)
        
        # Get total salary expenses
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total_salary
            FROM salary
            WHERE date BETWEEN %s AND %s
        """, (start_date_str, end_date_str))
        total_salary = float(cursor.fetchone()['total_salary'] or 0)
        
        # Get total purchases
        cursor.execute("""
            SELECT COALESCE(SUM(amount * (1 + gst_percentage/100)), 0) as total_billed_purchases
            FROM billed_purchases
            WHERE date BETWEEN %s AND %s
        """, (start_date_str, end_date_str))
        total_billed_purchases = float(cursor.fetchone()['total_billed_purchases'] or 0)
        
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total_purchases
            FROM purchases
            WHERE date BETWEEN %s AND %s
        """, (start_date_str, end_date_str))
        total_non_billed_purchases = float(cursor.fetchone()['total_purchases'] or 0)
        
        total_purchases = total_billed_purchases + total_non_billed_purchases
        
        # Calculate net profit
        net_profit = total_revenue - total_expenses - total_salary - total_purchases
        
        # Get accounts receivable (credit sales)
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as credit_sales
            FROM bills
            WHERE payment_status = 'Pending' AND date BETWEEN %s AND %s
        """, (start_date_str, end_date_str))
        accounts_receivable = float(cursor.fetchone()['credit_sales'] or 0)
        
        # Get accounts payable (credit purchases)
        cursor.execute("""
            SELECT COALESCE(SUM(amount * (1 + gst_percentage/100)), 0) as credit_purchases
            FROM billed_purchases
            WHERE payment_type = 'Credit' AND payment_status = 'Pending' 
            AND date BETWEEN %s AND %s
        """, (start_date_str, end_date_str))
        accounts_payable = float(cursor.fetchone()['credit_purchases'] or 0)
        
        summary = {
            'total_revenue': round(total_revenue, 2),
            'total_expenses': round(total_expenses, 2),
            'total_purchases': round(total_purchases, 2),
            'total_salary': round(total_salary, 2),
            'net_profit': round(net_profit, 2),
            'accounts_receivable': round(accounts_receivable, 2),
            'accounts_payable': round(accounts_payable, 2)
        }
        
        return jsonify(summary)
    except Exception as e:
        print(f"Error in get_summary_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports.route("/api/report/income-statement")
def get_income_statement():
    """Get income statement data"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get date range from query parameters
    date_range = request.args.get('date_range', 'month')
    start_date, end_date = get_date_range(date_range)
    
    # Format dates for SQL query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    try:
        # Get revenue data
        cursor.execute("""
            SELECT 'Billed Sales' as category, SUM(total_amount) as amount
            FROM bills
            WHERE date BETWEEN %s AND %s
            UNION ALL
            SELECT 'Non-Billed Sales' as category, SUM(amount) as amount
            FROM non_billed_sales
            WHERE date BETWEEN %s AND %s
        """, (start_date_str, end_date_str, start_date_str, end_date_str))
        revenue_data = cursor.fetchall()
        
        # Get expense data
        cursor.execute("""
            SELECT category, SUM(amount) as amount
            FROM expenses
            WHERE date BETWEEN %s AND %s
            GROUP BY category
            UNION ALL
            SELECT 'Salary' as category, SUM(amount) as amount
            FROM salary
            WHERE date BETWEEN %s AND %s
            UNION ALL
            SELECT 'Purchases' as category, SUM(amount * (1 + gst_percentage/100)) as amount
            FROM billed_purchases
            WHERE date BETWEEN %s AND %s
        """, (start_date_str, end_date_str, start_date_str, end_date_str, 
              start_date_str, end_date_str))
        expense_data = cursor.fetchall()
        
        # Convert to float for JSON serialization
        for item in revenue_data:
            if item['amount'] is not None:
                item['amount'] = float(item['amount'])
            else:
                item['amount'] = 0.0
                
        for item in expense_data:
            if item['amount'] is not None:
                item['amount'] = float(item['amount'])
            else:
                item['amount'] = 0.0
        
        return jsonify({
            'revenue': revenue_data,
            'expenses': expense_data,
            'start_date': start_date_str,
            'end_date': end_date_str
        })
    except Exception as e:
        print(f"Error in get_income_statement: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports.route("/api/report/cash-flow", methods=["GET"])
def get_cash_flow():
    """Get cash flow data"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get date range from query parameters
    date_range = request.args.get('date_range', 'month')
    start_date, end_date = get_date_range(date_range)
    
    # Format dates for SQL query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Get all transactions
    cursor.execute("""
        SELECT date, amount, transaction_type, description, reference_type 
        FROM transactions
        WHERE date BETWEEN %s AND %s
        ORDER BY date
    """, (start_date_str, end_date_str))
    transactions = cursor.fetchall()
    
    # Convert to float and format date for JSON
    for tx in transactions:
        tx['amount'] = float(tx['amount'])
        tx['date'] = tx['date'].strftime('%Y-%m-%d')
    
    return jsonify(transactions)

@reports.route("/api/report/sales", methods=["GET"])
def get_sales_report():
    """Get sales report data"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get date range from query parameters
    date_range = request.args.get('date_range', 'month')
    start_date, end_date = get_date_range(date_range)
    
    # Format dates for SQL query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Get billed sales
    cursor.execute("""
        SELECT date, customer_name, total_amount as amount, 
               payment_status as status, 'Billed' as type
        FROM bills
        WHERE date BETWEEN %s AND %s
    """, (start_date_str, end_date_str))
    billed_sales = cursor.fetchall()
    
    # Get non-billed sales
    cursor.execute("""
        SELECT date, customer_name, amount, 'Paid' as status, 'Non-Billed' as type
        FROM non_billed_sales
        WHERE date BETWEEN %s AND %s
    """, (start_date_str, end_date_str))
    non_billed_sales = cursor.fetchall()
    
    # Combine and convert to proper format for JSON
    sales_data = billed_sales + non_billed_sales
    for sale in sales_data:
        sale['amount'] = float(sale['amount'])
        sale['date'] = sale['date'].strftime('%Y-%m-%d')
    
    return jsonify(sales_data)

@reports.route("/api/report/expenses", methods=["GET"])
def get_expense_report():
    """Get expense report data"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get date range from query parameters
    date_range = request.args.get('date_range', 'month')
    start_date, end_date = get_date_range(date_range)
    
    # Format dates for SQL query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Get expense data
    cursor.execute("""
        SELECT date, expense_name as name, amount, category
        FROM expenses
        WHERE date BETWEEN %s AND %s
    """, (start_date_str, end_date_str))
    expense_data = cursor.fetchall()
    
    # Convert for JSON
    for expense in expense_data:
        expense['amount'] = float(expense['amount'])
        expense['date'] = expense['date'].strftime('%Y-%m-%d')
    
    return jsonify(expense_data)

@reports.route("/api/report/salary", methods=["GET"])
def get_salary_report():
    """Get salary report data"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get date range from query parameters
    date_range = request.args.get('date_range', 'month')
    start_date, end_date = get_date_range(date_range)
    
    # Format dates for SQL query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Get salary data
    cursor.execute("""
        SELECT date, employee_name, amount
        FROM salary
        WHERE date BETWEEN %s AND %s
    """, (start_date_str, end_date_str))
    salary_data = cursor.fetchall()
    
    # Convert for JSON
    for salary in salary_data:
        salary['amount'] = float(salary['amount'])
        salary['date'] = salary['date'].strftime('%Y-%m-%d')
    
    return jsonify(salary_data)

@reports.route("/api/report/receivables", methods=["GET"])
def get_receivables_report():
    """Get accounts receivable report"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get bills with pending payment
    cursor.execute("""
        SELECT date, customer_name, total_amount as amount, 
               'Pending' as status
        FROM bills
        WHERE payment_status = 'Pending'
        ORDER BY date
    """)
    receivables = cursor.fetchall()
    
    # Convert for JSON
    for item in receivables:
        item['amount'] = float(item['amount'])
        item['date'] = item['date'].strftime('%Y-%m-%d')
    
    return jsonify(receivables)

@reports.route("/api/report/payables", methods=["GET"])
def get_payables_report():
    """Get accounts payable report"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get purchases with pending payment
    cursor.execute("""
        SELECT date, vendor_name, amount * (1 + gst_percentage/100) as amount,
               'Pending' as status
        FROM billed_purchases
        WHERE payment_type = 'Credit' AND payment_status = 'Pending'
        ORDER BY date
    """)
    payables = cursor.fetchall()
    
    # Convert for JSON
    for item in payables:
        item['amount'] = float(item['amount'])
        item['date'] = item['date'].strftime('%Y-%m-%d')
    
    return jsonify(payables)

@reports.route("/download-report", methods=["POST"])
@reports.route("/reports/download-report", methods=["POST"])  # Adding alternate route to be safe
def download_report():
    """Generate Excel report for download"""
    print("Download report route hit")  # Debug logging
    try:
        report_type = request.form.get("report_type")
        print(f"Report type requested: {report_type}")  # Debug logging
        
        if not report_type:
            print("No report type provided")  # Debug logging
            flash("Report type is required", "danger")
            return redirect(url_for('reports.show_reports'))
            
        date_range = request.form.get("date_range", "month")
        print(f"Date range: {date_range}")  # Debug logging
        
        start_date, end_date = get_date_range(date_range)
        print(f"Start date: {start_date}, End date: {end_date}")  # Debug logging
        
        # Create dataframe based on report type
        df = generate_report_dataframe(report_type, start_date, end_date)
        
        if df.empty:
            print(f"No data found for {report_type}")  # Debug logging
            flash(f"No data found for {report_type} report", "warning")
            return redirect(url_for('reports.show_reports'))
            
        print(f"DataFrame created with {len(df)} rows")  # Debug logging
        
        # Prepare the Excel file in memory
        output = io.BytesIO()
        
        try:
            # Use xlsxwriter engine for better formatting
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name=report_type.capitalize())
            
            # Get workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets[report_type.capitalize()]
            
            # Add formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#FFA500',
                'color': 'white',
                'border': 1
            })
            
            # Format headers
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            # Adjust columns width
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col) + 2)
                worksheet.set_column(i, i, column_width)
            
            # Close the writer
            writer.close()
            
            print("Excel file created successfully")  # Debug logging
            
        except Exception as excel_error:
            print(f"Error creating Excel file: {str(excel_error)}")  # Debug logging
            raise excel_error
            
        output.seek(0)
        
        # Generate filename with current date
        filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        print(f"Sending file: {filename}")  # Debug logging
        
        response = send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
        # Add headers to prevent caching
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        print("File sent successfully")  # Debug logging
        return response
        
    except Exception as e:
        print(f"Error in download_report: {str(e)}")  # Debug logging
        import traceback
        print(traceback.format_exc())  # Print full error traceback
        flash(f"Error generating report: {str(e)}", "danger")
        return redirect(url_for('reports.show_reports'))

def get_date_range(date_range_str):
    """Convert date range string to start and end dates"""
    today = datetime.now().date()
    
    if date_range_str == 'today':
        return today, today
    elif date_range_str == 'week':
        start_date = today - timedelta(days=today.weekday())
        return start_date, today
    elif date_range_str == 'month':
        start_date = today.replace(day=1)
        return start_date, today
    elif date_range_str == 'quarter':
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=quarter_month, day=1)
        return start_date, today
    elif date_range_str == 'year':
        start_date = today.replace(month=1, day=1)
        return start_date, today
    else:
        # Parse custom range format YYYY-MM-DD_YYYY-MM-DD
        try:
            start_str, end_str = date_range_str.split('_')
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
            return start_date, end_date
        except:
            # Default to current month
            start_date = today.replace(day=1)
            return start_date, today

def generate_report_dataframe(report_type, start_date, end_date):
    """Generate pandas DataFrame for the given report type and date range"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    try:
        if report_type == 'income_statement':
            # Get revenue data
            cursor.execute("""
                SELECT 'Revenue' as Type, 'Billed Sales' as Category, SUM(total_amount) as Amount
                FROM bills
                WHERE date BETWEEN %s AND %s
                UNION ALL
                SELECT 'Revenue' as Type, 'Non-Billed Sales' as Category, SUM(amount) as Amount
                FROM non_billed_sales
                WHERE date BETWEEN %s AND %s
                UNION ALL
                SELECT 'Expenses' as Type, category as Category, SUM(amount) as Amount
                FROM expenses
                WHERE date BETWEEN %s AND %s
                GROUP BY category
                UNION ALL
                SELECT 'Expenses' as Type, 'Salary' as Category, SUM(amount) as Amount
                FROM salary
                WHERE date BETWEEN %s AND %s
                UNION ALL
                SELECT 'Expenses' as Type, 'Purchases' as Category, 
                       SUM(amount * (1 + gst_percentage/100)) as Amount
                FROM billed_purchases
                WHERE date BETWEEN %s AND %s
            """, (start_date_str, end_date_str) * 5)
            
            data = cursor.fetchall()
            if not data:
                return pd.DataFrame()
                
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Calculate totals
            revenue_total = df[df['Type'] == 'Revenue']['Amount'].sum()
            expenses_total = df[df['Type'] == 'Expenses']['Amount'].sum()
            net_income = revenue_total - expenses_total
            
            # Add totals
            totals_df = pd.DataFrame([
                {'Type': 'Total', 'Category': 'Total Revenue', 'Amount': revenue_total},
                {'Type': 'Total', 'Category': 'Total Expenses', 'Amount': expenses_total},
                {'Type': 'Total', 'Category': 'Net Income', 'Amount': net_income}
            ])
            
            df = pd.concat([df, totals_df], ignore_index=True)
            
            # Format amounts
            df['Amount'] = df['Amount'].fillna(0).round(2)
            
            return df
            
        elif report_type == 'cash_flow':
            cursor.execute("""
                SELECT date as Date, amount as Amount, 
                       transaction_type as Type, description as Description
                FROM transactions
                WHERE date BETWEEN %s AND %s
                ORDER BY date
            """, (start_date_str, end_date_str))
            data = cursor.fetchall()
            return pd.DataFrame(data if data else [])
            
        elif report_type == 'sales':
            cursor.execute("""
                SELECT date as Date, customer_name as Customer, 
                       total_amount as Amount, payment_status as Status,
                       'Billed' as Type
                FROM bills
                WHERE date BETWEEN %s AND %s
                UNION ALL
                SELECT date, customer_name, amount, 'Paid', 'Non-Billed'
                FROM non_billed_sales
                WHERE date BETWEEN %s AND %s
                ORDER BY Date
            """, (start_date_str, end_date_str) * 2)
            data = cursor.fetchall()
            return pd.DataFrame(data if data else [])
            
        elif report_type == 'expenses':
            cursor.execute("""
                SELECT date as Date, expense_name as Description,
                       amount as Amount, category as Category
                FROM expenses
                WHERE date BETWEEN %s AND %s
                ORDER BY date
            """, (start_date_str, end_date_str))
            data = cursor.fetchall()
            return pd.DataFrame(data if data else [])
            
        elif report_type == 'salary':
            cursor.execute("""
                SELECT date as Date, employee_name as Employee,
                       amount as Amount
                FROM salary
                WHERE date BETWEEN %s AND %s
                ORDER BY date
            """, (start_date_str, end_date_str))
            data = cursor.fetchall()
            return pd.DataFrame(data if data else [])
            
        elif report_type == 'receivables':
            cursor.execute("""
                SELECT date as Date, customer_name as Customer,
                       total_amount as Amount, 'Pending' as Status
                FROM bills
                WHERE payment_status = 'Pending'
                ORDER BY date
            """)
            data = cursor.fetchall()
            return pd.DataFrame(data if data else [])
            
        elif report_type == 'payables':
            cursor.execute("""
                SELECT date as Date, vendor_name as Vendor,
                       amount * (1 + gst_percentage/100) as Amount,
                       'Pending' as Status
                FROM billed_purchases
                WHERE payment_type = 'Credit' 
                AND payment_status = 'Pending'
                ORDER BY date
            """)
            data = cursor.fetchall()
            return pd.DataFrame(data if data else [])
        
        return pd.DataFrame()
        
    except Exception as e:
        print(f"Error in generate_report_dataframe: {str(e)}")
        return pd.DataFrame()
