from flask import Blueprint, render_template, request, send_file, flash
import pandas as pd
import io
from database import connect_db

reports = Blueprint("reports", __name__)

@reports.route("/reports", methods=["GET", "POST"])
def show_reports():
    db = connect_db()
    cursor = db.cursor(dictionary=True)

    # Default to 'revenue' report
    report_type = request.form.get("report_type", "revenue")

    # Mapping report types to SQL queries
    query_map = {
        "revenue": "SELECT date, amount FROM revenue",
        "expenses": "SELECT date, amount FROM expenses",
        "salary": "SELECT date, amount FROM salary",
        "bills": "SELECT date, amount FROM bills"
    }

    # Choose the appropriate query based on the report type selected
    query = query_map.get(report_type, query_map["revenue"])
    
    try:
        cursor.execute(query)
        data = cursor.fetchall()

        if not data:
            flash(f"No data found for {report_type} report", "warning")
            return render_template("reports.html", report_type=report_type, table_data=[])

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(data)

        # Prepare graph data
        graph_labels = [row["date"].strftime("%Y-%m-%d") for row in data]
        graph_data = [float(row["amount"]) for row in data]

        return render_template("reports.html", 
                               report_type=report_type, 
                               labels=graph_labels, 
                               values=graph_data,
                               table_data=df.to_dict(orient="records"))
    except Exception as e:
        flash(f"Error fetching data for {report_type}: {str(e)}", "danger")
        return render_template("reports.html", report_type=report_type, table_data=[])


@reports.route("/download-report", methods=["POST"])
def download_report():
    report_type = request.form.get("report_type", "revenue")
    db = connect_db()
    cursor = db.cursor(dictionary=True)

    # Mapping report types to SQL queries
    query_map = {
        "revenue": "SELECT * FROM revenue",
        "expenses": "SELECT * FROM expenses",
        "salary": "SELECT * FROM salary",
        "bills": "SELECT * FROM bills"
    }

    # Choose the appropriate query based on the report type selected
    query = query_map.get(report_type, query_map["revenue"])

    try:
        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            flash(f"No data found for {report_type} report", "warning")
            return redirect(request.referrer)

        # Convert data to DataFrame
        df = pd.DataFrame(rows)

        # Prepare the Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name=report_type.capitalize())
        output.seek(0)

        # Send the Excel file as a download
        return send_file(output, download_name=f"{report_type}_report.xlsx", as_attachment=True)
    except Exception as e:
        flash(f"Error generating report: {str(e)}", "danger")
        return redirect(request.referrer)
