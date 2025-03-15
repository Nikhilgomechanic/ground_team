from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from oauth2client.service_account import ServiceAccountCredentials
import secrets
import gspread
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

app = Flask(__name__)

app.secret_key = secrets.token_hex(16)


# MySQL Connection
conn = mysql.connector.connect(
    host="personal-dashboard-nishantmehra604-93540.f.aivencloud.com",
    user="avnadmin",
    password="AVNS_Knc_8GDbs_S8H_f1liN",
    database="cr_detail",
    port=12654
)

cursor = conn.cursor()

# connect to google sheet
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_sheet_key.env", scope)
client = gspread.authorize(creds)

spreadsheet_url = "https://docs.google.com/spreadsheets/d/1tKH0bgVj2p3ZgahZrjTkbTLVSquOeuPy6J7PcDNcoG0/edit?gid=0"
sheet = client.open_by_url(spreadsheet_url)

worksheet = sheet.worksheet("Cr detail dump")


# Role-to-Table Mapping
ROLE_TABLES = {
    "CR": "cr",
    "Captain": "captain",
    "City Head": "city_head",
    "Region Head": "region_head"
}


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form["role"]
        mail_id = request.form["mail_id"].lower()
        id = request.form["id"]

        table_name = ROLE_TABLES.get(role)

        if table_name:
            query = f"SELECT id, name FROM {table_name} WHERE mail_id=%s AND id=%s"
            cursor.execute(query, (mail_id, id))
            user = cursor.fetchone()

            if user:
                session["mail_id"] = mail_id.lower()
                session["role"] = role
                session["user"] = {"id": user[0], "name": user[1]}

                return redirect(url_for("dashboard"))
            else:
                return "Invalid Credentials", 401

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    role = session["role"]
    if role == "CR":
        return redirect(url_for("cr_data"))
    elif role == "Captain":
        return redirect(url_for("caption_data"))
    elif role == "City Head":
        return redirect(url_for("city_head_data"))
    elif role == "Region Head":
        return redirect(url_for("region_head_data"))

    return "Unauthorized Access", 403

@app.route('/cr_data')
def cr_data():
    if "user" not in session:
        return redirect(url_for("login"))  # Ensure "login" exists

    user_id = str(session["user"]["id"])
    try:
        data = worksheet.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])  # Convert to DataFrame
    except Exception as e:
        return f"Error fetching data: {str(e)}", 500

    # Ensure "id" column exists
    if "id" not in df.columns:
        return "ID column not found in Google Sheets", 400

    # Filter data for logged-in CR
    cr_data = df[df["id"] == user_id]
    if cr_data.empty:
        return "No data found for this CR.", 404

    # Define required metrics
    metrics = ['Converted %', "Repeated Customer %", 'Service Conversion %', 'Online Payment %', 'NPS Weightage %']

    # Ensure all metric columns exist
    missing_cols = [col for col in metrics if col not in cr_data.columns]
    if missing_cols:
        return f"Missing columns: {', '.join(missing_cols)}", 400

    # Extract and clean values
    values = cr_data[metrics].astype(float).fillna(0).values.flatten().tolist()

    # Ensure circular data for radar chart
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    # Prepare radar chart labels
    labels = ['Conversion', "Repeated Customers", 'Service Conversion', 'Online Payment', 'NPS']

    # Create Radar Chart
    fig, ax = plt.subplots(figsize=(3, 3), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='red', alpha=0.3)
    ax.plot(angles, values, color='red', linewidth=2)

    # Add percentage labels at correct angles
    for angle, value in zip(angles[:-1], values[:-1]):
        ax.annotate(f"{int(value)}%",
                    (angle, value + 5),
                    ha='center', fontsize=9, color='white')

    # Style adjustments
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, color='white', fontsize=8)
    ax.set_yticklabels([])
    ax.grid(color='gray', linestyle='dashed', linewidth=0.5)
    ax.spines['polar'].set_visible(False)

    static_folder = Path("static")
    static_folder.mkdir(parents=True, exist_ok=True)

    # Define chart save path
    chart_path = static_folder / "radar_chart.png"

    # Save the chart with transparency
    plt.savefig(chart_path, bbox_inches='tight', transparent=True)
    plt.close()

    return render_template("cr_data.html", data=cr_data.to_dict(orient="records"), chart_path=chart_path)


@app.route("/caption_data")
def caption_data():
    if "user" not in session:
        return redirect(url_for("login"))

    data = worksheet.get_all_values()
    return render_template("caption_data.html", data=data)

@app.route("/city_head_data")
def city_head_data():
    if "user" not in session:
        return redirect(url_for("login"))

    data = worksheet.get_all_values()
    return render_template("city_head_data.html", data=data)

@app.route("/region_head_data")
def region_head_data():
    if "user" not in session:
        return redirect(url_for("login"))

    data = worksheet.get_all_values()
    return render_template("region_head_data.html", data=data)

@app.route("/add_data", methods=["GET", "POST"])
def add_data():
    if "user" not in session or session["role"] != "City Head":
        return "Unauthorized Access"

    if request.method == "POST":
        name = request.form["name"]
        id = request.form["id"]
        mail_id = request.form["mail_id"]
        cr_employee_id = request.form["cr_employee_id"]
        city = request.form["city"]

        cursor.execute("INSERT INTO cr_table (name, id, mail_id, employee_id, city) VALUES (%s, %s, %s, %s, %s)",
                       (name, id, mail_id, cr_employee_id, city))

        return redirect(url_for("city_head_data"))

    return render_template("add_data.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("mail_id", None)
    session.pop("role", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
