from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
import calendar
from decimal import Decimal
import json

from models import TaxRate, TaxFiling, connect_db

taxes = Blueprint("taxes", __name__)

# Helper function to get database connection from app
def get_db():
    from flask import current_app
    return current_app.db

@taxes.route("/taxes")
@login_required
def tax_dashboard():
    """Show tax management dashboard"""
    # Get pending tax filings
    pending_filings = TaxFiling.get_pending()
    overdue_filings = TaxFiling.get_overdue()
    
    # Get recent tax transactions
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT 
            tt.id, tt.transaction_type, tt.reference_type, 
            tt.taxable_amount, tt.tax_amount, tt.date,
            tr.name as tax_name, tr.rate as tax_rate
        FROM tax_transactions tt
        LEFT JOIN tax_rates tr ON tt.tax_rate_id = tr.id
        ORDER BY tt.date DESC
        LIMIT 10
    """)
    recent_transactions = cursor.fetchall()
    
    # Get tax statistics
    # Current month GST summary
    today = date.today()
    first_day = today.replace(day=1)
    last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN transaction_type = 'Collected' THEN tax_amount ELSE 0 END) as collected,
            SUM(CASE WHEN transaction_type = 'Paid' THEN tax_amount ELSE 0 END) as paid
        FROM tax_transactions
        WHERE date BETWEEN %s AND %s
    """, (first_day, last_day))
    tax_summary = cursor.fetchone()
    
    # Calculate tax liability
    gst_collected = tax_summary['collected'] if tax_summary['collected'] else 0
    gst_paid = tax_summary['paid'] if tax_summary['paid'] else 0
    gst_liability = gst_collected - gst_paid
    
    # Get tax rates
    tax_rates = TaxRate.get_active_rates()
    
    # Get tax settings
    cursor.execute("SELECT * FROM tax_settings WHERE id = 1")
    tax_settings = cursor.fetchone()
    
    cursor.close()
    
    return render_template("tax_dashboard.html", 
                           pending_filings=pending_filings,
                           overdue_filings=overdue_filings,
                           recent_transactions=recent_transactions,
                           tax_summary={'collected': gst_collected, 
                                       'paid': gst_paid, 
                                       'liability': gst_liability},
                           tax_rates=tax_rates,
                           tax_settings=tax_settings,
                           current_month=first_day.strftime('%B %Y'))

@taxes.route("/taxes/rates")
@login_required
def tax_rates():
    """Show tax rates page"""
    tax_rates = TaxRate.get_all()
    return render_template("tax_rates.html", tax_rates=tax_rates)

@taxes.route("/taxes/rates/add", methods=["GET", "POST"])
@login_required
def add_tax_rate():
    """Add new tax rate"""
    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        type = request.form.get("type")
        rate = request.form.get("rate")
        description = request.form.get("description")
        is_active = True if request.form.get("is_active") == "on" else False
        hsn_code = request.form.get("hsn_code")
        effective_from = request.form.get("effective_from")
        effective_to = request.form.get("effective_to") or None
        
        # Create new tax rate
        tax_rate = TaxRate(
            name=name,
            type=type,
            rate=float(rate),
            description=description,
            is_active=is_active,
            hsn_code=hsn_code,
            effective_from=effective_from,
            effective_to=effective_to
        )
        
        # Save tax rate
        try:
            tax_rate.save()
            flash("Tax rate added successfully", "success")
            return redirect(url_for("taxes.tax_rates"))
        except Exception as e:
            flash(f"Error adding tax rate: {str(e)}", "danger")
    
    return render_template("tax_rate_form.html", tax_rate=None, action="Add")

@taxes.route("/taxes/rates/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_tax_rate(id):
    """Edit tax rate"""
    tax_rate_data = TaxRate.get_by_id(id)
    
    if not tax_rate_data:
        flash("Tax rate not found", "danger")
        return redirect(url_for("taxes.tax_rates"))
    
    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        type = request.form.get("type")
        rate = request.form.get("rate")
        description = request.form.get("description")
        is_active = True if request.form.get("is_active") == "on" else False
        hsn_code = request.form.get("hsn_code")
        effective_from = request.form.get("effective_from")
        effective_to = request.form.get("effective_to") or None
        
        # Create tax rate object
        tax_rate = TaxRate(
            id=id,
            name=name,
            type=type,
            rate=float(rate),
            description=description,
            is_active=is_active,
            hsn_code=hsn_code,
            effective_from=effective_from,
            effective_to=effective_to
        )
        
        # Save tax rate
        try:
            tax_rate.save()
            flash("Tax rate updated successfully", "success")
            return redirect(url_for("taxes.tax_rates"))
        except Exception as e:
            flash(f"Error updating tax rate: {str(e)}", "danger")
    
    return render_template("tax_rate_form.html", tax_rate=tax_rate_data, action="Edit")

@taxes.route("/taxes/filings")
@login_required
def tax_filings():
    """Show tax filings page"""
    filings = TaxFiling.get_all()
    return render_template("tax_filings.html", filings=filings)

@taxes.route("/taxes/filings/add", methods=["GET", "POST"])
@login_required
def add_tax_filing():
    """Add new tax filing"""
    if request.method == "POST":
        # Get form data
        filing_type = request.form.get("filing_type")
        period_start = request.form.get("period_start")
        period_end = request.form.get("period_end")
        due_date = request.form.get("due_date")
        status = request.form.get("status")
        collected_amount = request.form.get("collected_amount", 0)
        paid_amount = request.form.get("paid_amount", 0)
        net_payable = float(collected_amount) - float(paid_amount)
        reference_number = request.form.get("reference_number")
        notes = request.form.get("notes")
        
        # Create new tax filing
        tax_filing = TaxFiling(
            filing_type=filing_type,
            period_start=period_start,
            period_end=period_end,
            due_date=due_date,
            status=status,
            collected_amount=float(collected_amount),
            paid_amount=float(paid_amount),
            net_payable=net_payable,
            reference_number=reference_number,
            notes=notes
        )
        
        # Save tax filing
        try:
            tax_filing.save()
            flash("Tax filing added successfully", "success")
            return redirect(url_for("taxes.tax_filings"))
        except Exception as e:
            flash(f"Error adding tax filing: {str(e)}", "danger")
    
    return render_template("tax_filing_form.html", filing=None, action="Add")

@taxes.route("/taxes/filings/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_tax_filing(id):
    """Edit tax filing"""
    filing_data = TaxFiling.get_by_id(id)
    
    if not filing_data:
        flash("Tax filing not found", "danger")
        return redirect(url_for("taxes.tax_filings"))
    
    if request.method == "POST":
        # Get form data
        filing_type = request.form.get("filing_type")
        period_start = request.form.get("period_start")
        period_end = request.form.get("period_end")
        due_date = request.form.get("due_date")
        filing_date = request.form.get("filing_date") or None
        status = request.form.get("status")
        collected_amount = request.form.get("collected_amount", 0)
        paid_amount = request.form.get("paid_amount", 0)
        net_payable = float(collected_amount) - float(paid_amount)
        reference_number = request.form.get("reference_number")
        notes = request.form.get("notes")
        
        # Create tax filing object
        tax_filing = TaxFiling(
            id=id,
            filing_type=filing_type,
            period_start=period_start,
            period_end=period_end,
            due_date=due_date,
            filing_date=filing_date,
            status=status,
            collected_amount=float(collected_amount),
            paid_amount=float(paid_amount),
            net_payable=net_payable,
            reference_number=reference_number,
            notes=notes
        )
        
        # Save tax filing
        try:
            tax_filing.save()
            flash("Tax filing updated successfully", "success")
            return redirect(url_for("taxes.tax_filings"))
        except Exception as e:
            flash(f"Error updating tax filing: {str(e)}", "danger")
    
    return render_template("tax_filing_form.html", filing=filing_data, action="Edit")

@taxes.route("/taxes/settings", methods=["GET", "POST"])
@login_required
def tax_settings():
    """Manage tax settings"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get current settings
    cursor.execute("SELECT * FROM tax_settings WHERE id = 1")
    settings = cursor.fetchone()
    
    # Get tax rates for dropdown
    tax_rates = TaxRate.get_active_rates()
    
    if request.method == "POST":
        # Get form data
        business_name = request.form.get("business_name")
        gstin = request.form.get("gstin")
        pan = request.form.get("pan")
        tax_period = request.form.get("tax_period")
        financial_year_start = request.form.get("financial_year_start")
        gst_filing_due_date = request.form.get("gst_filing_due_date")
        default_tax_rate_id = request.form.get("default_tax_rate_id")
        
        try:
            # Update settings
            cursor.execute("""
                UPDATE tax_settings
                SET business_name = %s, gstin = %s, pan = %s, 
                    tax_period = %s, financial_year_start = %s,
                    gst_filing_due_date = %s, default_tax_rate_id = %s
                WHERE id = 1
            """, (business_name, gstin, pan, tax_period, financial_year_start,
                  gst_filing_due_date, default_tax_rate_id))
            
            db.commit()
            flash("Tax settings updated successfully", "success")
            return redirect(url_for("taxes.tax_settings"))
        except Exception as e:
            db.rollback()
            flash(f"Error updating tax settings: {str(e)}", "danger")
        finally:
            cursor.close()
    
    return render_template("tax_settings.html", settings=settings, tax_rates=tax_rates)

@taxes.route("/api/taxes/summary")
@login_required
def tax_summary_api():
    """API endpoint for tax summary data"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get date range from query parameters
    date_range = request.args.get('date_range', 'month')
    start_date, end_date = get_date_range(date_range)
    
    # Format dates for SQL query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Get GST collected (on sales)
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN transaction_type = 'Collected' THEN tax_amount ELSE 0 END) as collected,
            SUM(CASE WHEN transaction_type = 'Paid' THEN tax_amount ELSE 0 END) as paid
        FROM tax_transactions
        WHERE date BETWEEN %s AND %s
    """, (start_date_str, end_date_str))
    
    tax_data = cursor.fetchone()
    collected = float(tax_data['collected'] or 0)
    paid = float(tax_data['paid'] or 0)
    liability = collected - paid
    
    # Get transaction counts
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN transaction_type = 'Collected' THEN 1 END) as collected_count,
            COUNT(CASE WHEN transaction_type = 'Paid' THEN 1 END) as paid_count
        FROM tax_transactions
        WHERE date BETWEEN %s AND %s
    """, (start_date_str, end_date_str))
    
    count_data = cursor.fetchone()
    
    # Get filing status
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN status = 'Pending' THEN 1 END) as pending,
            COUNT(CASE WHEN status = 'Filed' THEN 1 END) as filed,
            COUNT(CASE WHEN status = 'Late Filed' THEN 1 END) as late
        FROM tax_filing
        WHERE period_start >= %s AND period_end <= %s
    """, (start_date_str, end_date_str))
    
    filing_status = cursor.fetchone()
    
    cursor.close()
    
    return jsonify({
        'collected': round(collected, 2),
        'paid': round(paid, 2),
        'liability': round(liability, 2),
        'collected_count': count_data['collected_count'] or 0,
        'paid_count': count_data['paid_count'] or 0,
        'filing_status': {
            'pending': filing_status['pending'] or 0,
            'filed': filing_status['filed'] or 0,
            'late': filing_status['late'] or 0
        },
        'start_date': start_date_str,
        'end_date': end_date_str
    })

@taxes.route("/taxes/generate-filing", methods=["POST"])
@login_required
def generate_tax_filing():
    """Generate a new tax filing period"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Get tax settings
        cursor.execute("SELECT * FROM tax_settings WHERE id = 1")
        settings = cursor.fetchone()
        
        # Get period data from form
        filing_type = request.form.get("filing_type", "GST")
        period_type = request.form.get("period_type", "Monthly")
        
        # Calculate period dates
        today = date.today()
        
        if period_type == "Monthly":
            # Previous month
            if today.month == 1:
                period_month = 12
                period_year = today.year - 1
            else:
                period_month = today.month - 1
                period_year = today.year
                
            period_start = date(period_year, period_month, 1)
            period_end = date(period_year, period_month, calendar.monthrange(period_year, period_month)[1])
            
        elif period_type == "Quarterly":
            # Previous quarter
            quarter = (today.month - 1) // 3
            if quarter == 0:
                quarter = 4
                period_year = today.year - 1
            else:
                period_year = today.year
                
            quarter_month = (quarter - 1) * 3 + 1
            period_start = date(period_year, quarter_month, 1)
            
            end_month = quarter_month + 2
            period_end = date(period_year, end_month, calendar.monthrange(period_year, end_month)[1])
            
        else:  # Annually
            # Previous financial year
            fy_start_month = 4  # April (assuming fiscal year starts in April)
            if today.month < fy_start_month:
                period_start = date(today.year - 2, fy_start_month, 1)
                period_end = date(today.year - 1, 3, 31)  # March 31
            else:
                period_start = date(today.year - 1, fy_start_month, 1)
                period_end = date(today.year, 3, 31)  # March 31
        
        # Calculate due date (e.g., 20th of next month for GST)
        due_date = period_end + timedelta(days=settings['gst_filing_due_date'])
        
        # Calculate tax amounts from transactions
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN transaction_type = 'Collected' THEN tax_amount ELSE 0 END) as collected,
                SUM(CASE WHEN transaction_type = 'Paid' THEN tax_amount ELSE 0 END) as paid
            FROM tax_transactions
            WHERE date BETWEEN %s AND %s
        """, (period_start, period_end))
        
        tax_data = cursor.fetchone()
        collected = float(tax_data['collected'] or 0)
        paid = float(tax_data['paid'] or 0)
        liability = collected - paid
        
        # Create TaxFiling object
        filing = TaxFiling(
            filing_type=filing_type,
            period_start=period_start,
            period_end=period_end,
            due_date=due_date,
            collected_amount=collected,
            paid_amount=paid,
            net_payable=liability,
            status="Pending"
        )
        
        # Save filing
        filing.save()
        
        flash(f"Tax filing for {period_start.strftime('%b %Y')} to {period_end.strftime('%b %Y')} generated successfully", "success")
        
    except Exception as e:
        flash(f"Error generating tax filing: {str(e)}", "danger")
    
    return redirect(url_for("taxes.tax_filings"))

@taxes.route("/taxes/reports")
@login_required
def tax_reports():
    """Show tax reporting and analytics dashboard"""
    # Get database connection
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Set default date range - current financial year
    today = date.today()
    # Financial year in India starts from April 1
    if today.month >= 4:
        fy_start = date(today.year, 4, 1)
    else:
        fy_start = date(today.year - 1, 4, 1)
    fy_end = date(fy_start.year + 1, 3, 31)
    
    # Get tax summary by type
    cursor.execute("""
        SELECT 
            tr.name as tax_name, 
            tr.rate as tax_rate,
            SUM(CASE WHEN tt.transaction_type = 'Collected' THEN tt.tax_amount ELSE 0 END) as collected,
            SUM(CASE WHEN tt.transaction_type = 'Paid' THEN tt.tax_amount ELSE 0 END) as paid,
            COUNT(DISTINCT CASE WHEN tt.transaction_type = 'Collected' THEN tt.reference_id END) as collected_count,
            COUNT(DISTINCT CASE WHEN tt.transaction_type = 'Paid' THEN tt.reference_id END) as paid_count
        FROM tax_transactions tt
        LEFT JOIN tax_rates tr ON tt.tax_rate_id = tr.id
        WHERE tt.date BETWEEN %s AND %s
        GROUP BY tr.id, tr.name, tr.rate
        ORDER BY tr.rate DESC
    """, (fy_start, fy_end))
    
    tax_summary_by_type = cursor.fetchall()
    
    # Get monthly tax summary for chart
    cursor.execute("""
        SELECT 
            DATE_FORMAT(tt.date, '%Y-%m') as month,
            SUM(CASE WHEN tt.transaction_type = 'Collected' THEN tt.tax_amount ELSE 0 END) as collected,
            SUM(CASE WHEN tt.transaction_type = 'Paid' THEN tt.tax_amount ELSE 0 END) as paid
        FROM tax_transactions tt
        WHERE tt.date BETWEEN %s AND %s
        GROUP BY DATE_FORMAT(tt.date, '%Y-%m')
        ORDER BY month
    """, (fy_start, fy_end))
    
    monthly_tax_summary = cursor.fetchall()
    
    # Format chart data for JavaScript
    months = []
    collected_data = []
    paid_data = []
    liability_data = []
    
    for item in monthly_tax_summary:
        # Format month for display (yyyy-mm to MMM YYYY)
        year, month = item['month'].split('-')
        month_name = datetime(int(year), int(month), 1).strftime('%b %Y')
        months.append(month_name)
        
        collected = float(item['collected'] or 0)
        paid = float(item['paid'] or 0)
        liability = collected - paid
        
        collected_data.append(round(collected, 2))
        paid_data.append(round(paid, 2))
        liability_data.append(round(liability, 2))
    
    # Get tax filing statistics
    cursor.execute("""
        SELECT 
            filing_type,
            COUNT(*) as total_filings,
            SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'Filed' THEN 1 ELSE 0 END) as filed,
            SUM(CASE WHEN status = 'Late Filed' THEN 1 ELSE 0 END) as late_filed,
            SUM(CASE WHEN status = 'Under Query' THEN 1 ELSE 0 END) as under_query,
            SUM(net_payable) as total_paid
        FROM tax_filing
        WHERE period_start >= %s AND period_end <= %s
        GROUP BY filing_type
    """, (fy_start, fy_end))
    
    filing_stats = cursor.fetchall()
    
    # Get HSN code summary (for GST reports)
    cursor.execute("""
        SELECT 
            tt.hsn_code,
            SUM(tt.taxable_amount) as total_taxable,
            SUM(tt.tax_amount) as total_tax,
            COUNT(*) as transaction_count,
            tr.rate as tax_rate
        FROM tax_transactions tt
        LEFT JOIN tax_rates tr ON tt.tax_rate_id = tr.id
        WHERE tt.hsn_code IS NOT NULL AND tt.date BETWEEN %s AND %s
        GROUP BY tt.hsn_code, tr.rate
        ORDER BY total_taxable DESC
        LIMIT 10
    """, (fy_start, fy_end))
    
    hsn_summary = cursor.fetchall()
    
    # Convert to formatted currency values
    for summary in tax_summary_by_type:
        summary['collected'] = float(summary['collected'] or 0)
        summary['paid'] = float(summary['paid'] or 0)
        summary['net'] = summary['collected'] - summary['paid']
    
    # Calculate overall totals
    total_collected = sum(item['collected'] for item in tax_summary_by_type)
    total_paid = sum(item['paid'] for item in tax_summary_by_type)
    total_liability = total_collected - total_paid
    
    cursor.close()
    
    return render_template("tax_reports.html",
                          tax_summary_by_type=tax_summary_by_type,
                          hsn_summary=hsn_summary,
                          filing_stats=filing_stats,
                          months=months,
                          collected_data=collected_data,
                          paid_data=paid_data,
                          liability_data=liability_data,
                          fy_start=fy_start,
                          fy_end=fy_end,
                          total_collected=total_collected,
                          total_paid=total_paid,
                          total_liability=total_liability)

@taxes.route("/api/taxes/monthly_summary")
@login_required
def monthly_tax_summary_api():
    """API endpoint for monthly tax summary for chart"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get date range
    year = request.args.get('year', date.today().year)
    
    # Get monthly tax data
    cursor.execute("""
        SELECT 
            MONTH(date) as month,
            SUM(CASE WHEN transaction_type = 'Collected' THEN tax_amount ELSE 0 END) as collected,
            SUM(CASE WHEN transaction_type = 'Paid' THEN tax_amount ELSE 0 END) as paid
        FROM tax_transactions
        WHERE YEAR(date) = %s
        GROUP BY MONTH(date)
        ORDER BY month
    """, (year,))
    
    monthly_data = cursor.fetchall()
    cursor.close()
    
    # Format data for chart.js
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    collected = [0] * 12
    paid = [0] * 12
    liability = [0] * 12
    
    for item in monthly_data:
        month_idx = item['month'] - 1  # Convert to 0-based index
        collected[month_idx] = float(item['collected'] or 0)
        paid[month_idx] = float(item['paid'] or 0)
        liability[month_idx] = collected[month_idx] - paid[month_idx]
    
    return jsonify({
        'labels': months,
        'datasets': [
            {
                'label': 'GST Collected',
                'data': collected,
                'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                'borderColor': 'rgb(54, 162, 235)',
                'borderWidth': 1
            },
            {
                'label': 'GST Paid',
                'data': paid,
                'backgroundColor': 'rgba(75, 192, 192, 0.5)',
                'borderColor': 'rgb(75, 192, 192)',
                'borderWidth': 1
            },
            {
                'label': 'Net Liability',
                'data': liability,
                'backgroundColor': 'rgba(255, 99, 132, 0.5)',
                'borderColor': 'rgb(255, 99, 132)',
                'borderWidth': 1
            }
        ]
    })

def get_date_range(date_range_str):
    """Convert date range string to start and end dates"""
    today = date.today()
    
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
    elif date_range_str == 'last_month':
        if today.month == 1:
            start_date = date(today.year - 1, 12, 1)
            end_date = date(today.year - 1, 12, 31)
        else:
            month = today.month - 1
            start_date = date(today.year, month, 1)
            end_date = date(today.year, month, calendar.monthrange(today.year, month)[1])
        return start_date, end_date
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

@taxes.route("/taxes/export")
@login_required
def export_tax_data():
    """Export tax data for GST returns"""
    # Get request parameters
    report_type = request.args.get('type', 'gstr1')
    period = request.args.get('period', '')
    
    # Parse period (format: YYYY-MM)
    try:
        year, month = period.split('-')
        year = int(year)
        month = int(month)
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
    except (ValueError, AttributeError):
        # Default to current month if period is invalid
        today = date.today()
        start_date = date(today.year, today.month, 1)
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
    
    # Get database connection
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Export data based on report type
    if report_type == 'gstr1':
        # GSTR-1: Outward supplies (sales)
        cursor.execute("""
            SELECT 
                b.id as invoice_number,
                DATE_FORMAT(b.date, '%%d-%%m-%%Y') as invoice_date,
                b.customer_name as customer_name,
                IF(b.customer_number LIKE '%%GSTIN%%', b.customer_number, '') as customer_gstin,
                b.basic_amount as taxable_value,
                tr.name as tax_description,
                tr.rate as tax_rate,
                b.gst_amount as tax_amount,
                b.total_amount as invoice_value
            FROM bills b
            LEFT JOIN tax_transactions tt ON tt.reference_id = b.id AND tt.reference_type = 'Bill'
            LEFT JOIN tax_rates tr ON tt.tax_rate_id = tr.id
            WHERE DATE(b.date) BETWEEN %s AND %s
            ORDER BY b.date DESC
        """, (start_date, end_date))
        
        sales_data = cursor.fetchall()
        
        # Generate CSV content
        if sales_data:
            import csv
            import io
            
            output = io.StringIO()
            fieldnames = ['invoice_number', 'invoice_date', 'customer_name', 'customer_gstin', 
                         'taxable_value', 'tax_description', 'tax_rate', 'tax_amount', 'invoice_value']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for row in sales_data:
                writer.writerow(row)
            
            csv_content = output.getvalue()
            output.close()
            
            # Return CSV file
            response = make_response(csv_content)
            response.headers["Content-Disposition"] = f"attachment; filename=GSTR1_Export_{period}.csv"
            response.headers["Content-Type"] = "text/csv"
            return response
        
    elif report_type == 'gstr2':
        # GSTR-2: Inward supplies (purchases)
        cursor.execute("""
            SELECT 
                bp.id as invoice_number,
                DATE_FORMAT(bp.date, '%%d-%%m-%%Y') as invoice_date,
                bp.vendor_name as vendor_name,
                '' as vendor_gstin, -- Add GSTIN field to vendors in future
                bp.amount as taxable_value,
                CONCAT(bp.gst_type, ' ', bp.gst_percentage, '%%') as tax_description,
                bp.gst_percentage as tax_rate,
                (bp.amount * bp.gst_percentage / 100) as tax_amount,
                (bp.amount * (1 + bp.gst_percentage / 100)) as invoice_value
            FROM billed_purchases bp
            WHERE DATE(bp.date) BETWEEN %s AND %s
            ORDER BY bp.date DESC
        """, (start_date, end_date))
        
        purchase_data = cursor.fetchall()
        
        # Generate CSV content
        if purchase_data:
            import csv
            import io
            
            output = io.StringIO()
            fieldnames = ['invoice_number', 'invoice_date', 'vendor_name', 'vendor_gstin', 
                         'taxable_value', 'tax_description', 'tax_rate', 'tax_amount', 'invoice_value']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for row in purchase_data:
                writer.writerow(row)
            
            csv_content = output.getvalue()
            output.close()
            
            # Return CSV file
            response = make_response(csv_content)
            response.headers["Content-Disposition"] = f"attachment; filename=GSTR2_Export_{period}.csv"
            response.headers["Content-Type"] = "text/csv"
            return response
    
    elif report_type == 'gstr3b':
        # GSTR-3B: Summary report
        cursor.execute("""
            SELECT 
                tr.rate as tax_rate,
                SUM(CASE WHEN tt.transaction_type = 'Collected' THEN tt.taxable_amount ELSE 0 END) as outward_taxable,
                SUM(CASE WHEN tt.transaction_type = 'Collected' THEN tt.tax_amount ELSE 0 END) as outward_tax,
                SUM(CASE WHEN tt.transaction_type = 'Paid' THEN tt.taxable_amount ELSE 0 END) as inward_taxable,
                SUM(CASE WHEN tt.transaction_type = 'Paid' THEN tt.tax_amount ELSE 0 END) as inward_tax
            FROM tax_transactions tt
            LEFT JOIN tax_rates tr ON tt.tax_rate_id = tr.id
            WHERE tt.date BETWEEN %s AND %s
            GROUP BY tr.rate
            ORDER BY tr.rate
        """, (start_date, end_date))
        
        summary_data = cursor.fetchall()
        
        # Calculate totals
        total_outward_taxable = sum(float(row['outward_taxable'] or 0) for row in summary_data)
        total_outward_tax = sum(float(row['outward_tax'] or 0) for row in summary_data)
        total_inward_taxable = sum(float(row['inward_taxable'] or 0) for row in summary_data)
        total_inward_tax = sum(float(row['inward_tax'] or 0) for row in summary_data)
        net_tax = total_outward_tax - total_inward_tax
        
        # Add total row
        summary_data.append({
            'tax_rate': 'TOTAL',
            'outward_taxable': total_outward_taxable,
            'outward_tax': total_outward_tax,
            'inward_taxable': total_inward_taxable,
            'inward_tax': total_inward_tax
        })
        
        # Generate CSV content
        if summary_data:
            import csv
            import io
            
            output = io.StringIO()
            fieldnames = ['tax_rate', 'outward_taxable', 'outward_tax', 'inward_taxable', 'inward_tax']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for row in summary_data:
                writer.writerow(row)
            
            # Add net tax payable row
            writer.writerow({'tax_rate': 'NET TAX PAYABLE', 'outward_tax': net_tax})
            
            csv_content = output.getvalue()
            output.close()
            
            # Return CSV file
            response = make_response(csv_content)
            response.headers["Content-Disposition"] = f"attachment; filename=GSTR3B_Summary_{period}.csv"
            response.headers["Content-Type"] = "text/csv"
            return response
    
    # If no data or invalid report type, redirect back to reports page
    flash(f"No data available for {report_type.upper()} export for period {period}", "warning")
    return redirect(url_for('taxes.tax_reports'))

@taxes.route("/taxes/exports")
@login_required
def tax_exports():
    """GST Returns Export page"""
    return render_template("tax_exports.html") 