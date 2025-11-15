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
    cur.execute("SELECT event_id AS project_id, event_name AS name, event_date AS start_date, location, description, budget, status FROM event ORDER BY event_date DESC LIMIT 100")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # Convert rows to list of dicts
    projects = []
    for row in rows:
        project = {
            'project_id': row[0],
            'name': row[1],
            'start_date': row[2],
            'location': row[3],
            'description': row[4],
            'budget': row[5],
            'status': row[6]
        }
        projects.append(project)
    return json.loads(json.dumps(projects, cls=DecimalEncoder))
@app.route('/api/activities')
def api_activities():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            event_id,
            event_name,
            event_date,
            location,
            description,
            budget,
            created_by,
            status
        FROM event
        ORDER BY event_date DESC
        LIMIT 100
    """)

    rows = cur.fetchall()

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

            # Frontend-required fields that are NOT in your table
            "activity_type": "Event"   # default value
        })

    cur.close()
    conn.close()

    return jsonify(activities)

@app.route('/api/donations')
def api_donations():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT 
        d.donation_id,
        d.donor_id,
        donor.full_name AS donor_name,
        d.amount,
        d.donation_type,
        d.donation_date,
        d.notes
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
        "donor_name": r[2],         # 🔥 FIXED
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
        """, (donor_id,amount, payment_method, donation_date, notes))

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
@app.route('/api/recent_entries')
def api_recent_entries():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 'Volunteer' AS type, full_name AS name, join_date AS date
        FROM volunteer
        WHERE join_date IS NOT NULL AND full_name IS NOT NULL
        
        UNION ALL
        
        SELECT 'Donor' AS type, full_name AS name, created_at AS date
        FROM donor
        WHERE created_at IS NOT NULL AND full_name IS NOT NULL
        
        UNION ALL
        
        SELECT 'Beneficiary' AS type, full_name AS name, created_at AS date
        FROM beneficiary
        WHERE created_at IS NOT NULL AND full_name IS NOT NULL
        
        UNION ALL
        
        SELECT 'Event' AS type, event_name AS name, event_date AS date
        FROM event
        WHERE event_date IS NOT NULL AND event_name IS NOT NULL
        
        UNION ALL
        
        SELECT 'Donation' AS type, 
               CONCAT(COALESCE(donation_type, 'Unknown'), ' - $', COALESCE(amount, 0)) AS name, 
               donation_date AS date
        FROM donation
        WHERE donation_date IS NOT NULL
        
        ORDER BY date DESC
        LIMIT 20
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Convert each row (tuple) → dict
    recent_entries = []
    for r in rows:
        recent_entries.append({
            "type": r[0],
            "name": r[1],
            "date": r[2].isoformat() if r[2] else None
        })

    return jsonify(recent_entries)

@app.route('/api/total_counts')
def api_total_counts():
    """
    Get total counts of all entries for analytics page.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Count stakeholders
    cur.execute("SELECT COUNT(*) FROM volunteer")
    total_volunteers = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM donor")
    total_donors = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM beneficiary")
    total_beneficiaries = cur.fetchone()[0]
    
    total_stakeholders = total_volunteers + total_donors + total_beneficiaries
    
    # Count projects/events
    cur.execute("SELECT COUNT(*) FROM event")
    total_projects = cur.fetchone()[0]
    
    # Count donations
    cur.execute("SELECT COUNT(*) FROM donation")
    total_donations = cur.fetchone()[0]
    
    # Count activities (same as events in current schema)
    total_activities = total_projects
    
    cur.close()
    conn.close()
    
    return jsonify({
        "total_stakeholders": int(total_stakeholders),
        "total_volunteers": int(total_volunteers),
        "total_donors": int(total_donors),
        "total_beneficiaries": int(total_beneficiaries),
        "total_projects": int(total_projects),
        "total_activities": int(total_activities),
        "total_donations": int(total_donations),
        "total_entries": int(total_stakeholders + total_projects + total_donations)
    })

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
                INSERT INTO donor (full_name, email, phone, address, uri, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (full_name, email, phone, address_full, notes, joined_date or None))
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

    cur.execute("""
        SELECT 'volunteer' AS type, volunteer_id AS id, full_name, email, phone, status, address, join_date AS join_date, uri
        FROM volunteer
        UNION ALL
        SELECT 'donor' AS type, donor_id AS id, full_name, email, phone, 'Active' AS status, address, created_at AS join_date, uri
        FROM donor
        UNION ALL
        SELECT 'beneficiary' AS type, beneficiary_id AS id, full_name, NULL AS email, NULL AS phone, status, address, created_at AS join_date, uri
        FROM beneficiary
        ORDER BY id DESC LIMIT 100
    """)

    rows = cur.fetchall()

    # Convert each row → dict
    result = []
    for r in rows:
        result.append({
            "type": r[0],
            "id": r[1],
            "full_name": r[2],
            "email": r[3],
            "phone": r[4],
            "status": r[5],
            "address": r[6],
            "join_date": r[7].isoformat() if r[7] else None,
            "uri": r[8]
        })

    cur.close()
    conn.close()

    return jsonify(result)

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
            INSERT INTO event (event_name, event_date, location, description, budget, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (event_name, start_date, location, description, budget, status, 1))  # Assuming created_by is 1 for now

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
