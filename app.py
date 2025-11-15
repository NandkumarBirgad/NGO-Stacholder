import pymysql
from flask import Flask, render_template, jsonify, request
import decimal
import json
from datetime import date, datetime

# ---------- JSON Helper ----------
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        return super().default(o)

# ---------- Flask App ----------
app = Flask(__name__, template_folder='template', static_folder='static')

# ---------- MySQL Connection (WITH SSL for TiDB Cloud) ----------
def get_db_connection():
    return pymysql.connect(
        host='gateway01.ap-southeast-1.prod.aws.tidbcloud.com',
        user='4MtRB8TtYgRCw9d.root',
        port=4000,
        password='PTcrp6v3lYMq6hJd',
        database='test',
        cursorclass=pymysql.cursors.Cursor,
        ssl={"fake_flag_to_enable_tls": True},
        ssl_verify_cert=False
    )

# ---------- ROUTES ----------
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

# ---------- API ROUTES ----------
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

    cur.execute("""
        SELECT event_id AS project_id, event_name AS name, event_date AS start_date,
               location, description, budget, status
        FROM event
        ORDER BY event_date DESC
        LIMIT 100
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    projects = []
    for r in rows:
        projects.append({
            "project_id": r[0],
            "name": r[1],
            "start_date": r[2],
            "location": r[3],
            "description": r[4],
            "budget": r[5],
            "status": r[6]
        })

    return json.loads(json.dumps(projects, cls=DecimalEncoder))

@app.route('/api/activities')
def api_activities():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT event_id, event_name, event_date, location, description, budget, created_by, status
        FROM event
        ORDER BY event_date DESC
        LIMIT 100
    """)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    activities = []
    for r in rows:
        activities.append({
            "activity_id": r[0],
            "name": r[1],
            "start_date": r[2].isoformat() if r[2] else None,
            "location": r[3],
            "description": r[4],
            "budget": float(r[5]) if r[5] else 0,
            "created_by": r[6],
            "status": r[7],
            "activity_type": "Event"
        })

    return jsonify(activities)

@app.route('/api/donations')
def api_donations():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT d.donation_id, d.donor_id, donor.full_name AS donor_name,
               d.amount, d.donation_type, d.donation_date, d.notes
        FROM donation d
        LEFT JOIN donor ON d.donor_id = donor.donor_id
        ORDER BY d.donation_date DESC
        LIMIT 100
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    donations = []
    for r in rows:
        donations.append({
            "donation_id": r[0],
            "donor_id": r[1],
            "donor_name": r[2],
            "amount": float(r[3]) if r[3] else 0,
            "donation_type": r[4],
            "donation_date": r[5].isoformat() if r[5] else None,
            "notes": r[6]
        })

    return jsonify(donations)

@app.route('/api/add_donation', methods=['POST'])
def api_add_donation():
    try:
        data = request.get_json()
        donor_id = data.get("donorName")
        amount = data.get("amount")
        donation_date = data.get("date")
        payment_method = data.get("paymentMethod", "Online")
        notes = data.get("notes")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO donation (donor_id, amount, donation_type, donation_date, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (donor_id, amount, payment_method, donation_date, notes))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "Donation recorded successfully"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ---------- RECENT ENTRIES ----------
@app.route('/api/recent_entries')
def api_recent_entries():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 'Volunteer', full_name, join_date FROM volunteer
        UNION ALL
        SELECT 'Donor', full_name, created_at FROM donor
        UNION ALL
        SELECT 'Beneficiary', full_name, created_at FROM beneficiary
        UNION ALL
        SELECT 'Event', event_name, event_date FROM event
        UNION ALL
        SELECT 'Donation', CONCAT(IFNULL(donation_type,'Unknown'), ' - $', amount), donation_date FROM donation
        ORDER BY 3 DESC
        LIMIT 20
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "type": r[0],
            "name": r[1],
            "date": r[2].isoformat() if r[2] else None
        })

    return jsonify(result)

# ---------- ERROR HANDLER ----------
@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# ---------- RUN ----------
if __name__ == '__main__':
    app.run(debug=True)
