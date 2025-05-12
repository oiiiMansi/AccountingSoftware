import pandas as pd
import io
from datetime import datetime, timedelta
import mysql.connector

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
    else:
        # Default to current month
        start_date = today.replace(day=1)
        return start_date, today

def test_income_statement():
    print("="*50)
    print("TESTING INCOME STATEMENT REPORT GENERATION")
    print("="*50)
    
    # Connect to database
    try:
        print("Connecting to database...")
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="roxanne",
            database="accounting"
        )
        print("Database connection successful.")
        
        cursor = db.cursor(dictionary=True)
        
        # Get date range
        date_range = "month"
        start_date, end_date = get_date_range(date_range)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        print(f"Date range: {start_date_str} to {end_date_str}")
        
        # Execute the query
        print("Executing income statement query...")
        query = """
            SELECT 'Revenue' as Type, 'Billed Sales' as Category, COALESCE(SUM(total_amount), 0) as Amount
            FROM bills
            WHERE date BETWEEN %s AND %s
            UNION ALL
            SELECT 'Revenue' as Type, 'Non-Billed Sales' as Category, COALESCE(SUM(amount), 0) as Amount
            FROM non_billed_sales
            WHERE date BETWEEN %s AND %s
            UNION ALL
            SELECT 'Expenses' as Type, category as Category, COALESCE(SUM(amount), 0) as Amount
            FROM expenses
            WHERE date BETWEEN %s AND %s
            GROUP BY category
            UNION ALL
            SELECT 'Expenses' as Type, 'Salary' as Category, COALESCE(SUM(amount), 0) as Amount
            FROM salary
            WHERE date BETWEEN %s AND %s
            UNION ALL
            SELECT 'Expenses' as Type, 'Purchases' as Category, 
                COALESCE(SUM(amount * (1 + gst_percentage/100)), 0) as Amount
            FROM billed_purchases
            WHERE date BETWEEN %s AND %s
        """
        
        params = (start_date_str, end_date_str) * 5
        cursor.execute(query, params)
        
        data = cursor.fetchall()
        print(f"Query returned {len(data)} rows")
        
        if not data:
            print("No data returned!")
            return
        
        # Process data
        print("Processing data...")
        # Convert numeric values
        for row in data:
            if 'Amount' in row and row['Amount'] is not None:
                row['Amount'] = float(row['Amount'])
            else:
                row['Amount'] = 0.0
        
        # Create DataFrame
        df = pd.DataFrame(data)
        print(f"DataFrame created with shape: {df.shape}")
        print("DataFrame sample:")
        print(df.head())
        
        # Calculate totals
        revenue_total = df[df['Type'] == 'Revenue']['Amount'].sum()
        expenses_total = df[df['Type'] == 'Expenses']['Amount'].sum() 
        net_income = revenue_total - expenses_total
        
        print(f"Revenue: {revenue_total}, Expenses: {expenses_total}, Net Income: {net_income}")
        
        # Add totals rows
        totals_df = pd.DataFrame([
            {'Type': 'Total', 'Category': 'Total Revenue', 'Amount': revenue_total},
            {'Type': 'Total', 'Category': 'Total Expenses', 'Amount': expenses_total},
            {'Type': 'Total', 'Category': 'Net Income', 'Amount': net_income}
        ])
        
        df = pd.concat([df, totals_df], ignore_index=True)
        df['Amount'] = df['Amount'].fillna(0).astype(float).round(2)
        
        print("Final DataFrame:")
        print(df)
        
        # Try to write to Excel
        print("Writing to Excel...")
        output = io.BytesIO()
        
        try:
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Income_Statement')
            
            workbook = writer.book
            worksheet = writer.sheets['Income_Statement']
            
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#FFA500',
                'font_color': 'white',
                'border': 1
            })
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            for i, col in enumerate(df.columns):
                column_len = max([len(str(s)) for s in df[col].values] + [len(col)])
                column_width = min(max(column_len + 2, len(col) + 2), 50)
                worksheet.set_column(i, i, column_width)
            
            writer.close()
            print("Excel file created successfully!")
            
            # Save the file to disk for verification
            output.seek(0)
            with open('test_income_statement.xlsx', 'wb') as f:
                f.write(output.getvalue())
            
            print("Excel file saved to disk as 'test_income_statement.xlsx'")
            
        except Exception as e:
            print(f"Error creating Excel file: {str(e)}")
            import traceback
            print(traceback.format_exc())
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()
            print("Database connection closed.")
    
    print("="*50)

if __name__ == "__main__":
    test_income_statement() 