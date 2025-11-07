from flask import Flask, render_template, jsonify, request
from flask_mysqldb import MySQL
import decimal
import json
import MySQLdb
from datetime import date, datetime

# Helper to convert Decimal and date to JSON serializable
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        return super().default(o)

app = Flask(__name__, template_folder='template', static_folder='static')

app.config.from_object('config.Config')

mysql = MySQL(app)

# Initialize MySQL connection
def get_db_connection():
    return MySQLdb.connect(
        host='localhost',
        user='root',
        password='sagar123',
        database='ngo_management_system'
    )

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
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM volunteer WHERE status='Active'")
    active_volunteers = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM event")
    total_projects = cur.fetchone()[0]

    cur.execute("SELECT IFNULL(SUM(amount), 0) FROM donation")
    total_donations = cur.fetchone()[0] or 0

    cur.close()
    conn.close()
    return jsonify({
        "active_volunteers": int(active_volunteers),
        "total_projects": int(total_projects),
        "total_donations": float(total_donations)
    })

@app.route('/api/volunteers')
def api_volunteers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT volunteer_id, full_name, email, phone, status, join_date FROM volunteer ORDER BY join_date DESC LIMIT 100")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

@app.route('/api/projects')
def api_projects():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT event_id AS project_id, event_name AS name, event_date AS start_date, location, description, budget FROM event ORDER BY event_date DESC LIMIT 100")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return json.loads(json.dumps(rows, cls=DecimalEncoder))

@app.route('/api/activities')
def api_activities():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT event_id AS activity_id, event_name AS name, event_date AS start_date, location, description, budget FROM event ORDER BY event_date DESC LIMIT 100")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return json.loads(json.dumps(rows, cls=DecimalEncoder))

@app.route('/api/donations')
def api_donations():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""SELECT donation_id, donor_id, amount, donation_type, donation_date, notes
                   FROM donation ORDER BY donation_date DESC LIMIT 100""")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return json.loads(json.dumps(rows, cls=DecimalEncoder))

@app.route('/api/add_donation', methods=['POST'])
def api_add_donation():
    try:
        data = request.get_json()
        donor_id = data.get('donorName')
        amount = data.get('amount')
        donation_date = data.get('date')
        payment_method = data.get('paymentMethod', 'Online')
        category = data.get('category', 'General')
        project = data.get('project')
        notes = data.get('notes')
        is_recurring = data.get('recurring', False)
        tax_receipt_sent = data.get('taxReceipt', False)

        conn = get_db_connection()
        cur = conn.cursor()

        # Insert into donation table
        cur.execute("""
            INSERT INTO donation (donor_id, amount, donation_type, donation_date, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (donor_id, amount, payment_method, donation_date, notes))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "Donation recorded successfully"})

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/analytics/donations_trend')
def api_donations_trend():
    """
    Simple donations by month (last 6 months).
    """
    conn = get_db_connection()
    cur = conn.cursor()
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
    conn.close()
    # Ensure sequential months - frontend can handle missing months, but we'll return rows
    return json.loads(json.dumps(rows, cls=DecimalEncoder))

# Simple search endpoints (optional)
@app.route('/api/search/stakeholders')
def api_search_stakeholders():
    q = request.args.get('q', '')
    conn = get_db_connection()
    cur = conn.cursor()
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
    conn.close()
    return jsonify(rows)

# API endpoint to add stakeholder
@app.route('/api/add_stakeholder', methods=['POST'])
def api_add_stakeholder():
    try:
        data = request.get_json()
        stakeholder_type = data.get('type')
        full_name = data.get('fullName')
        email = data.get('email')
        phone = data.get('phone')
        status = data.get('status', 'Active')
        city = data.get('city')
        joined_date = data.get('joinedDate')
        address = data.get('address')
        notes = data.get('notes')

        # Combine city and address
        address_full = f"{city or ''} {address or ''}".strip() or None

        conn = get_db_connection()
        cur = conn.cursor()

        # Check for duplicate email if email is provided
        if email:
            if stakeholder_type == 'volunteer':
                cur.execute("SELECT COUNT(*) FROM volunteer WHERE email = %s", (email,))
            elif stakeholder_type == 'donor':
                cur.execute("SELECT COUNT(*) FROM donor WHERE email = %s", (email,))
            elif stakeholder_type == 'beneficiary':
                cur.execute("SELECT COUNT(*) FROM beneficiary WHERE email = %s", (email,))

            if cur.fetchone()[0] > 0:
                conn.close()
                return jsonify({"success": False, "message": f"Email '{email}' already exists for {stakeholder_type}"}), 400

        if stakeholder_type == 'volunteer':
            # Insert into volunteer table
            cur.execute("""
                INSERT INTO volunteer (full_name, email, phone, status, join_date, address, uri)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (full_name, email, phone, status, joined_date, address_full, notes))
        elif stakeholder_type == 'donor':
            # Insert into donor table
            cur.execute("""
                INSERT INTO donor (full_name, email, phone, address, uri)
                VALUES (%s, %s, %s, %s, %s)
            """, (full_name, email, phone, address_full, notes))
        elif stakeholder_type == 'beneficiary':
            # Insert into beneficiary table
            cur.execute("""
                INSERT INTO beneficiary (full_name, email, phone, status, address, need_description, uri)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (full_name, email, phone, status, address_full, notes, None))
        else:
            conn.close()
            return jsonify({"success": False, "message": "Invalid stakeholder type"}), 400

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "Stakeholder added successfully"})

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/stakeholders')
def api_stakeholders():
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch all stakeholders from different tables
    cur.execute("""
        SELECT 'volunteer' AS type, volunteer_id AS id, full_name, email, phone, status, address, join_date, uri
        FROM volunteer
        UNION ALL
        SELECT 'donor' AS type, donor_id AS id, full_name, email, phone, 'Active' AS status, address, NULL AS join_date, uri
        FROM donor
        UNION ALL
        SELECT 'beneficiary' AS type, beneficiary_id AS id, full_name, NULL AS email, phone, status, address, NULL AS join_date, uri
        FROM beneficiary
        ORDER BY id DESC LIMIT 100
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return json.loads(json.dumps(rows, cls=DecimalEncoder))

# API endpoint to add project
@app.route('/api/add_project', methods=['POST'])
def api_add_project():
    try:
        data = request.get_json()
        event_name = data.get('projectName')
        description = data.get('description')
        category = data.get('category')
        status = data.get('status', 'Planning')
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        budget = data.get('budget', 0)
        target_beneficiaries = data.get('targetBeneficiaries', 0)
        volunteers_needed = data.get('volunteersNeeded', 0)
        location = data.get('location')
        project_manager = data.get('projectManager')

        conn = get_db_connection()
        cur = conn.cursor()

        # Insert into event table (projects are stored as events)
        cur.execute("""
            INSERT INTO event (event_name, event_date, location, description, budget, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (event_name, start_date, location, description, budget, 1))  # Assuming created_by is 1 for now

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "Project added successfully"})

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": str(e)}), 500

# API endpoint to add activity
@app.route('/api/add_activity', methods=['POST'])
def api_add_activity():
    try:
        data = request.get_json()
        activity_name = data.get('activityName')
        description = data.get('description')
        activity_type = data.get('activityType')
        status = data.get('status', 'Planning')
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        location = data.get('location')
        expected_attendees = data.get('expectedAttendees', 0)
        budget = data.get('budget', 0)
        volunteers_needed = data.get('volunteersNeeded', 0)
        organizer = data.get('organizer')
        notes = data.get('notes')

        conn = get_db_connection()
        cur = conn.cursor()

        # Insert into event table (activities are stored as events)
        cur.execute("""
            INSERT INTO event (event_name, event_date, location, description, budget, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (activity_name, start_date, location, description, budget, 1))  # Assuming created_by is 1 for now

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "Activity added successfully"})

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": str(e)}), 500

# Error handler
@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
