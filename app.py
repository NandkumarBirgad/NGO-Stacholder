from flask import Flask, render_template, jsonify, request
from flask_mysqldb import MySQL
import decimal
import json

# Helper to convert Decimal to JSON serializable
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super().default(o)

app = Flask(__name__, template_folder='template', static_folder='static')

app.config.from_object('config.Config')

mysql = MySQL(app)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/stakeholders')
def stakeholders():
    return render_template('stakeholders.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/activities')
def activities():
    return render_template('activities.html')

@app.route('/donations')
def donations():
    return render_template('donations.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

# ---------- API ROUTES (Backend Data) ----------
@app.route('/api/summary')
def api_summary():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM volunteer WHERE status='Active'")
    active_volunteers = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM event")
    total_projects = cur.fetchone()[0]

    cur.execute("SELECT IFNULL(SUM(amount), 0) FROM donation")
    total_donations = cur.fetchone()[0] or 0

    cur.close()
    return jsonify({
        "active_volunteers": int(active_volunteers),
        "total_projects": int(total_projects),
        "total_donations": float(total_donations)
    })

@app.route('/api/volunteers')
def api_volunteers():
    cur = mysql.connection.cursor()
    cur.execute("SELECT volunteer_id, full_name, email, phone, status, join_date FROM volunteer ORDER BY join_date DESC LIMIT 100")
    rows = cur.fetchall()
    cur.close()
    return jsonify(rows)

@app.route('/api/projects')
def api_projects():
    cur = mysql.connection.cursor()
    cur.execute("SELECT event_id AS project_id, event_name AS name, event_date AS start_date, location, description FROM event ORDER BY event_date DESC LIMIT 100")
    rows = cur.fetchall()
    cur.close()
    return jsonify(rows)

@app.route('/api/donations')
def api_donations():
    cur = mysql.connection.cursor()
    cur.execute("""SELECT donation_id, donor_id, amount, donation_type, donation_date, notes
                   FROM donation ORDER BY donation_date DESC LIMIT 100""")
    rows = cur.fetchall()
    cur.close()
    return json.loads(json.dumps(rows, cls=DecimalEncoder))

@app.route('/api/analytics/donations_trend')
def api_donations_trend():
    """
    Simple donations by month (last 6 months).
    """
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT DATE_FORMAT(donation_date, '%%Y-%%m') AS month, 
               IFNULL(SUM(amount),0) AS total
        FROM donation
        WHERE donation_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY month
        ORDER BY month;
    """)
    rows = cur.fetchall()
    cur.close()
    # Ensure sequential months - frontend can handle missing months, but we'll return rows
    return json.loads(json.dumps(rows, cls=DecimalEncoder))

# Simple search endpoints (optional)
@app.route('/api/search/stakeholders')
def api_search_stakeholders():
    q = request.args.get('q', '')
    cur = mysql.connection.cursor()
    likeq = f"%{q}%"
    cur.execute("""
        SELECT 'volunteer' AS type, volunteer_id AS id, full_name AS name, email, phone
        FROM volunteer
        WHERE full_name LIKE %s OR email LIKE %s
        UNION
        SELECT 'donor' AS type, donor_id AS id, full_name AS name, email, phone
        FROM donor
        WHERE full_name LIKE %s OR email LIKE %s
        LIMIT 100
    """, (likeq, likeq, likeq, likeq))
    rows = cur.fetchall()
    cur.close()
    return jsonify(rows)

# API endpoint to add stakeholder
@app.route('/api/add_stakeholder', methods=['POST'])
def api_add_stakeholder():
    try:
        data = request.get_json()
        stakeholder_type = data.get('type')
        full_name = data.get('full_name')
        email = data.get('email')
        phone = data.get('phone')
        status = data.get('status', 'Active')
        join_date = data.get('join_date')

        cur = mysql.connection.cursor()

        if stakeholder_type == 'volunteer':
            # Insert into volunteer table
            cur.execute("""
                INSERT INTO volunteer (full_name, email, phone, status, join_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (full_name, email, phone, status, join_date))
        elif stakeholder_type == 'donor':
            # Insert into donor table
            cur.execute("""
                INSERT INTO donor (full_name, email, phone)
                VALUES (%s, %s, %s)
            """, (full_name, email, phone))
        elif stakeholder_type == 'beneficiary':
            # For beneficiary, we might need a separate table or handle differently
            # For now, we'll treat it as a volunteer
            cur.execute("""
                INSERT INTO volunteer (full_name, email, phone, status, join_date)
                VALUES (%s, %s, %s, 'Active', CURDATE())
            """, (full_name, email, phone))
        else:
            return jsonify({"success": False, "message": "Invalid stakeholder type"}), 400

        mysql.connection.commit()
        cur.close()

        return jsonify({"success": True, "message": "Stakeholder added successfully"})

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# Error handler
@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
