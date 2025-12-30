import os
import json
import pymysql
import decimal
import logging
from datetime import date, datetime

import pymysql
import requests

from flask import (
    Flask, render_template, jsonify, request, redirect, url_for,
    session, flash, send_from_directory
)
from flask_mail import Mail, Message
from flask_cors import CORS

# Firebase Admin
import firebase_admin
from firebase_admin import credentials, auth, firestore


# -------------------------
# CONFIG
# -------------------------
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")


# Firebase Web API Key (for REST signInWithPassword)
FIREBASE_WEB_API_KEY = "AIzaSyAnJssmodtiYIfmmalhvtug7IjncXVedhI"  # <-- replace if needed

# Uploaded image path (local)
UPLOADED_IMAGE_PATH = "/mnt/data/6507ba89-768b-43e0-91fc-58d70aca4d08.png"

# Flask app
app = Flask(__name__, template_folder='template', static_folder='static')
app.secret_key = os.environ.get("FLASK_SECRET", "CHANGE_THIS_SECRET")
CORS(app)

# Optional: mail config (uncomment and fill to enable sending)
# app.config.update(
#     MAIL_SERVER='smtp.gmail.com',
#     MAIL_PORT=587,
#     MAIL_USE_TLS=True,
#     MAIL_USERNAME='youremail@gmail.com',
#     MAIL_PASSWORD='your-email-password-or-app-password'
# )
mail = None
if app.config.get("MAIL_SERVER"):
    mail = Mail(app)

# -------------------------
# JSON helper
# -------------------------
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        return super().default(o)

# -------------------------
# MySQL connection helper
# -------------------------
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

# -------------------------
# Initialize Firebase Admin & Firestore
# -------------------------
firestore_db = None
try:
    firebase_json = os.getenv("FIREBASE_KEY_JSON")

    if not firebase_json:
        raise RuntimeError("FIREBASE_KEY_JSON environment variable not set")

    cred = credentials.Certificate(json.loads(firebase_json))
    firebase_admin.initialize_app(cred)
    firestore_db = firestore.client()

    logging.info("Firebase Admin initialized using ENV JSON.")
except Exception as e:
    logging.error("Firebase initialization failed: %s", e)
    firestore_db = None


# -------------------------
# Serve uploaded image (local path)
# -------------------------
@app.route('/uploaded-image')
def uploaded_image():
    folder, filename = os.path.split(UPLOADED_IMAGE_PATH)
    if not os.path.exists(UPLOADED_IMAGE_PATH):
        return "Uploaded image not found on server.", 404
    return send_from_directory(folder or '/', filename)

# -------------------------
# UI routes: register/login/dashboard/logout
# -------------------------
@app.route('/')
def home():
    # Open register page first
    return redirect(url_for('register_user'))

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """
    Register:
      - Create Firebase Auth user via Admin SDK
      - Store profile + role in Firestore (collection 'Users')
      - Redirect to /login on success
    """
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        role = (request.form.get('role') or '').lower()

        if not username or not email or not password or not role:
            flash("Please fill all required fields.", "danger")
            return render_template('register.html')

        if role not in ("donor", "volunteer", "beneficiary"):
            flash("Invalid role selected.", "danger")
            return render_template('register.html')

        if firestore_db is None:
            flash("Server misconfigured: Firestore not available. Contact admin.", "danger")
            return render_template('register.html')

        # Create Firebase user
        try:
            user = auth.create_user(email=email, password=password, display_name=username)
        except Exception as e:
            logging.exception("Firebase create_user error")
            flash(f"Firebase error creating user: {e}", "danger")
            return render_template('register.html')

        # Store profile in Firestore
        try:
            firestore_db.collection('Users').document(user.uid).set({
                'username': username,
                'email': email,
                'role': role,
                'created_at': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logging.exception("Firestore write error")
            # rollback Firebase user if Firestore write fails
            try:
                auth.delete_user(user.uid)
            except Exception:
                pass
            flash(f"Error saving user profile: {e}", "danger")
            return render_template('register.html')

        # Also save user to MySQL stakeholders tables so SQL and Firestore stay in sync
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            now = datetime.utcnow()
            if role == 'volunteer':
                cur.execute("""
                    INSERT INTO volunteer (full_name, email, phone, address, status, join_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (username, email, None, None, 'Active', now))
            elif role == 'donor':
                cur.execute("""
                    INSERT INTO donor (full_name, email, phone, address, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, email, None, None, now))
            elif role == 'beneficiary':
                cur.execute("""
                    INSERT INTO beneficiary (full_name, email, phone, address, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (username, email, None, None, 'Active', now))
            else:
                # unknown role, do nothing
                cur.close()
                conn.close()
                flash("Invalid role selected.", "danger")
                return render_template('register.html')

            conn.commit()
        except Exception as e:
            # If MySQL insert fails, rollback Firestore and Firebase user to avoid inconsistent state
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            logging.exception("MySQL insert error during registration")
            # cleanup Firestore and Firebase
            try:
                if firestore_db:
                    firestore_db.collection('Users').document(user.uid).delete()
            except Exception:
                pass
            try:
                auth.delete_user(user.uid)
            except Exception:
                pass
            flash(f"Registration failed while saving to database: {e}", "danger")
            return render_template('register.html')
        finally:
            try:
                cur.close()
                conn.close()
            except Exception:
                pass

        flash("Registration successful. Please login.", "success")
        return redirect(url_for('login_page'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """
    Login via Firebase REST API (signInWithPassword).
    On success read user profile from Firestore and set session (uid, username, role).
    """
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template('login.html')

        # Authenticate via Firebase REST API
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
            payload = {"email": email, "password": password, "returnSecureToken": True}
            r = requests.post(url, json=payload, timeout=8)
        except Exception as e:
            logging.exception("Firebase REST request error")
            flash(f"Authentication service error: {e}", "danger")
            return render_template('login.html')

        if r.status_code != 200:
            try:
                err = r.json().get('error', {}).get('message', '')
                flash(f"Login failed: {err}", "danger")
            except Exception:
                flash("Invalid credentials.", "danger")
            return render_template('login.html')

        data = r.json()
        uid = data.get('localId')
        if not uid:
            flash("Login failed: missing user id.", "danger")
            return render_template('login.html')

        # Read Firestore profile to get role and username
        if firestore_db is None:
            flash("Server misconfigured: Firestore not available. Contact admin.", "danger")
            return render_template('login.html')

        try:
            doc = firestore_db.collection('Users').document(uid).get()
        except Exception as e:
            logging.exception("Firestore read error")
            flash(f"Error reading user profile: {e}", "danger")
            return render_template('login.html')

        if not doc.exists:
            flash("User profile not found. Please register.", "danger")
            return render_template('login.html')

        profile = doc.to_dict()
        role = (profile.get('role') or '').lower()
        username = profile.get('username') or profile.get('email')

        # Save session
        session['uid'] = uid
        session['username'] = username
        session['role'] = role

        flash("Login successful.", "success")
        # Redirect based on role
        if role == 'admin':
            return redirect(url_for('dashboard'))
        elif role == 'donor':
            return redirect(url_for('donor_dashboard'))
        elif role == 'volunteer':
            return redirect(url_for('volunteer_dashboard'))
        else:
            flash("Unknown role. Contact admin.", "danger")
            return redirect(url_for('login_page'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('login_page'))


@app.route('/dashboard')
def dashboard():
    if 'uid' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login_page'))

    # ensure role in session; if missing, attempt to refresh from Firestore
    if 'role' not in session or not session['role']:
        try:
            if firestore_db:
                doc = firestore_db.collection('Users').document(session['uid']).get()
                if doc.exists:
                    session['role'] = doc.to_dict().get('role')
        except Exception:
            pass

    if 'role' not in session or not session['role']:
        flash("User role missing; please contact admin.", "warning")
        return redirect(url_for('login_page'))

    return render_template('dashboard.html', username=session.get('username'), role=session.get('role'))


# -------------------------
# Simple role-specific pages (protected)
# -------------------------
@app.route('/donor')
def donor_page():
    if 'uid' not in session:
        return redirect(url_for('login_page'))
    if session.get('role') != 'donor':
        flash("Access denied: donor only page.", "danger")
        return redirect(url_for('dashboard'))
    return render_template('donations.html')


@app.route('/donor-dashboard')
def donor_dashboard():
    if 'uid' not in session or session.get('role') != 'donor':
        flash("Access denied: donor only dashboard.", "danger")
        return redirect(url_for('login_page'))
    return render_template('donor_dashboard.html', username=session.get('username'))

@app.route('/volunteer-dashboard')
def volunteer_dashboard():
    if 'uid' not in session or session.get('role') != 'volunteer':
        flash("Access denied: volunteer only dashboard.", "danger")
        return redirect(url_for('login_page'))
    return render_template('volunteer_dashboard.html', username=session.get('username'))

# ...existing code...
@app.route('/api/donor/summary')
def api_donor_summary():
    if 'uid' not in session or session.get('role') != 'donor':
        return jsonify({"error": "Unauthorized"}), 401
    donor_id = session['uid']

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Sum of all donations by this donor (match donor_id with email from firestore?)
        # Note: donations table links donor_id to donor table's donor_id, which is numeric
        # Firestore uid and donor_id in MySQL may not be the same, must find donor by email
        # Need donor email from session or Firestore
        # Firestore is used for user profiles, including emails, so get email first

        # Fetch email from Firestore by uid
        email = None
        if firestore_db:
            doc = firestore_db.collection('Users').document(donor_id).get()
            if doc.exists:
                email = doc.to_dict().get('email')

        if not email:
            return jsonify({"error": "Email not found for user"}), 404

        # Lookup donor_id in MySQL donor table by email
        cur.execute("SELECT donor_id FROM donor WHERE email = %s", (email,))
        res = cur.fetchone()
        if not res:
            total_donated = 0
            donation_count = 0
        else:
            donor_mysql_id = res['donor_id']
            # Sum donations and count donations by donor_mysql_id
            cur.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM donation WHERE donor_id = %s", (donor_mysql_id,))
            total_donated = cur.fetchone()['total'] or 0
            cur.execute("SELECT COUNT(*) AS count FROM donation WHERE donor_id = %s", (donor_mysql_id,))
            donation_count = cur.fetchone()['count'] or 0

    finally:
        cur.close()
        conn.close()

    return jsonify({
        "totalDonated": total_donated,
        "donationCount": donation_count
    })

@app.route('/api/donor/donations')
def api_donor_donations():
    if 'uid' not in session or session.get('role') != 'donor':
        return jsonify({"error": "Unauthorized"}), 401
    donor_id = session['uid']

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Same firestore email lookup logic as above
        email = None
        if firestore_db:
            doc = firestore_db.collection('Users').document(donor_id).get()
            if doc.exists:
                email = doc.to_dict().get('email')

        if not email:
            return jsonify({"error": "Email not found for user"}), 404

        cur.execute("SELECT donor_id FROM donor WHERE email = %s", (email))
        res = cur.fetchone()
        if not res:
            donations = []
        else:
            donor_mysql_id = res['donor_id']
            cur.execute("""
                SELECT donation_id, amount, donation_type, donation_date, notes
                FROM donation
                WHERE donor_id = %s
                ORDER BY donation_date DESC
                LIMIT 50
            """, (donor_mysql_id,))
            donations = cur.fetchall()
            for d in donations:
                if d.get('donation_date'):
                    d['donation_date'] = d['donation_date'].isoformat()
    finally:
        cur.close()
        conn.close()

    return jsonify(donations)

@app.route('/volunteer')
def volunteer_page():
    if 'uid' not in session:
        return redirect(url_for('login_page'))
    if session.get('role') != 'volunteer':
        flash("Access denied: volunteer only page.", "danger")
        return redirect(url_for('dashboard'))
    return render_template('activities.html',role=session.get("role"),
    username=session.get("username"))

@app.route('/beneficiary')
def beneficiary_page():
    if 'uid' not in session:
        return redirect(url_for('login_page'))
    if session.get('role') != 'beneficiary':
        flash("Access denied: beneficiary only page.", "danger")
        return redirect(url_for('dashboard'))
    return render_template('projects.html')


# -------------------------
# MySQL API Routes (kept from your original file)
# -------------------------
@app.route('/stakeholders')
def stakeholders_page():
    if "uid" not in session:
        return redirect(url_for('login_page'))
    return render_template('stakeholders.html', role=session.get("role"), username=session.get("username"))

@app.route('/projects')
def projects_page():
    if "uid" not in session:
        return redirect(url_for('login_page'))
    return render_template('projects.html', role=session.get("role"), username=session.get("username"))

@app.route('/activities')
def activities_page():
    if "uid" not in session:
        return redirect(url_for('login_page'))
    return render_template('activities.html', role=session.get("role"), username=session.get("username"))

@app.route('/donations')
def donations_page():
    if "uid" not in session:
        return redirect(url_for('login_page'))
    return render_template('donations.html', role=session.get("role"), username=session.get("username"))

@app.route('/analytics')
def analytics_page():
    if "uid" not in session:
        return redirect(url_for('login_page'))
    return render_template('analytics.html', role=session.get("role"), username=session.get("username"))


@app.route('/api/summary')
def api_summary():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) AS c FROM volunteer WHERE status='Active'")
        active_volunteers = cur.fetchone()['c'] or 0

        cur.execute("SELECT COUNT(*) AS c FROM event")
        total_projects = cur.fetchone()['c'] or 0

        cur.execute("SELECT COALESCE(SUM(amount), 0) AS s FROM donation")
        total_donations = cur.fetchone()['s'] or 0.0
    finally:
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
    try:
        cur.execute("SELECT volunteer_id, full_name, email, phone, status, join_date FROM volunteer ORDER BY join_date DESC LIMIT 100")
        rows = cur.fetchall()
        for r in rows:
            if r.get("join_date"):
                r["join_date"] = r["join_date"].isoformat()
    finally:
        cur.close()
        conn.close()
    return jsonify(rows)


@app.route('/api/projects')
def api_projects():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT event_id AS project_id, event_name AS name, event_date AS start_date,
                   location, description, budget, status
            FROM event
            ORDER BY event_date DESC
            LIMIT 100
        """)
        rows = cur.fetchall()
        for r in rows:
            if r.get("start_date"):
                r["start_date"] = r["start_date"].isoformat()
    finally:
        cur.close()
        conn.close()
    return json.loads(json.dumps(rows, cls=DecimalEncoder))


@app.route('/api/activities')
def api_activities():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT event_id, event_name AS name, event_date AS start_date, location, description,
                   budget, created_by, status
            FROM event
            ORDER BY event_date DESC
            LIMIT 100
        """)
        rows = cur.fetchall()
        for r in rows:
            if r.get("start_date"):
                r["start_date"] = r["start_date"].isoformat()
            r["activity_type"] = "Event"
    finally:
        cur.close()
        conn.close()
    return jsonify(rows)


@app.route('/api/donations')
def api_donations():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT d.donation_id, d.donor_id, donor.full_name AS donor_name,
                   d.amount, d.donation_type, d.donation_date, d.notes
            FROM donation d
            LEFT JOIN donor ON d.donor_id = donor.donor_id
            ORDER BY d.donation_date DESC
            LIMIT 100
        """)
        rows = cur.fetchall()
        for r in rows:
            if r.get("donation_date"):
                r["donation_date"] = r["donation_date"].isoformat()
    finally:
        cur.close()
        conn.close()
    return jsonify(rows)


@app.route('/api/add_donation', methods=['POST'])
def api_add_donation():
    data = request.get_json() or {}
    required = ["donorName", "amount", "date"]
    for k in required:
        if k not in data:
            return jsonify({"success": False, "message": f"Missing field: {k}"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO donation (donor_id, amount, donation_type, donation_date, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data.get("donorName"),
            data.get("amount"),
            data.get("paymentMethod", "Cash"),
            data.get("date"),
            data.get("notes")
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()

    return jsonify({"success": True, "message": "Donation recorded successfully"})


@app.route('/api/stakeholders')
def api_stakeholders():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 'volunteer' AS type, volunteer_id AS id, full_name, email, phone, status, address, join_date
            FROM volunteer
            UNION ALL
            SELECT 'donor' AS type, donor_id AS id, full_name, email, phone, 'Active' AS status, address, created_at
            FROM donor
            UNION ALL
            SELECT 'beneficiary' AS type, beneficiary_id AS id, full_name, email, phone, status, address, created_at
            FROM beneficiary
            ORDER BY id DESC
            LIMIT 100
        """)
        rows = cur.fetchall()
        for r in rows:
            for k in ("join_date", "created_at"):
                if r.get(k):
                    r[k] = r[k].isoformat()
    finally:
        cur.close()
        conn.close()
    return jsonify(rows)


@app.route('/api/add_stakeholder', methods=['POST'])
def api_add_stakeholder():
    data = request.get_json() or {}
    if "type" not in data or "fullName" not in data:
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    stakeholder_type = data["type"]
    full_name = data["fullName"]
    email = data.get("email")
    phone = data.get("phone")
    address = data.get("address")
    status = data.get("status", "Active")
    joined_date = data.get("joinedDate")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if stakeholder_type == "volunteer":
            cur.execute("""
                INSERT INTO volunteer (full_name, email, phone, address, status, join_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (full_name, email, phone, address, status, joined_date))
        elif stakeholder_type == "donor":
            cur.execute("""
                INSERT INTO donor (full_name, email, phone, address, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (full_name, email, phone, address, joined_date))
        elif stakeholder_type == "beneficiary":
            cur.execute("""
                INSERT INTO beneficiary (full_name, email, phone, address, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (full_name, email, phone, address, status, joined_date))
        else:
            return jsonify({"success": False, "message": "Invalid stakeholder type"}), 400

        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()

    return jsonify({"success": True, "message": f"{stakeholder_type} added"})


@app.route('/api/add_activity', methods=['POST'])
def api_add_activity():
    data = request.get_json() or {}
    # Only admins (or non-volunteers) should be able to create activities via API
    if 'uid' not in session or session.get('role') != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO event (event_name, event_date, location, description, budget, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get("activityName"),
            data.get("startDate"),
            data.get("location"),
            data.get("description"),
            data.get("budget", 0),
            data.get("status", "Planning"),
            1
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()
    return jsonify({"success": True, "message": "Activity added"})


@app.route('/api/join_activity', methods=['POST'])
def api_join_activity():
    # Allow volunteers to join an event/activity
    if 'uid' not in session or session.get('role') != 'volunteer':
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    event_id = data.get('eventId')
    if not event_id:
        return jsonify({"success": False, "message": "Missing eventId"}), 400

    # Resolve volunteer_id by matching email from Firestore user profile
    email = None
    try:
        if firestore_db:
            doc = firestore_db.collection('Users').document(session['uid']).get()
            if doc.exists:
                email = doc.to_dict().get('email')
    except Exception:
        email = None

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        volunteer_id = None
        if email:
            cur.execute("SELECT volunteer_id FROM volunteer WHERE email = %s", (email,))
            res = cur.fetchone()
            if res:
                volunteer_id = res.get('volunteer_id')

        if not volunteer_id:
            # create a minimal volunteer record using session username
            try:
                cur.execute("INSERT INTO volunteer (full_name, email, join_date, status) VALUES (%s, %s, %s, %s)", (
                    session.get('username'), email, datetime.utcnow().date(), 'Active'
                ))
                volunteer_id = cur.lastrowid
            except Exception:
                conn.rollback()
                return jsonify({"success": False, "message": "Unable to create volunteer record"}), 500

        # Check if already joined
        cur.execute("SELECT participation_id FROM participation WHERE volunteer_id = %s AND event_id = %s", (volunteer_id, event_id))
        if cur.fetchone():
            return jsonify({"success": False, "message": "Already joined"}), 400

        cur.execute("INSERT INTO participation (volunteer_id, event_id, role, hours_worked) VALUES (%s, %s, %s, %s)", (volunteer_id, event_id, None, None))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.exception('Error joining activity')
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()

    return jsonify({"success": True, "message": "Joined activity"})


@app.route('/api/volunteer/activities')
def api_volunteer_activities():
    # Return activities the logged-in volunteer has joined
    if 'uid' not in session or session.get('role') != 'volunteer':
        return jsonify([]), 200

    email = None
    try:
        if firestore_db:
            doc = firestore_db.collection('Users').document(session['uid']).get()
            if doc.exists:
                email = doc.to_dict().get('email')
    except Exception:
        email = None

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        volunteer_id = None
        if email:
            cur.execute("SELECT volunteer_id FROM volunteer WHERE email = %s", (email,))
            res = cur.fetchone()
            if res:
                volunteer_id = res.get('volunteer_id')

        if not volunteer_id:
            return jsonify([])

        cur.execute("""
            SELECT p.participation_id, p.hours_worked, p.feedback, e.event_id, e.event_name AS name, e.event_date AS date, e.location, e.description
            FROM participation p
            JOIN event e ON p.event_id = e.event_id
            WHERE p.volunteer_id = %s
            ORDER BY e.event_date DESC
        """, (volunteer_id,))
        rows = cur.fetchall()
        for r in rows:
            if r.get('date'):
                r['date'] = r['date'].isoformat()
            # normalize keys expected by frontend
            r['hours'] = r.get('hours_worked')
            r['notes'] = r.get('feedback')
    finally:
        cur.close()
        conn.close()

    return jsonify(rows)


@app.route('/api/volunteer/summary')
def api_volunteer_summary():
    # Simple summary for volunteer dashboard
    if 'uid' not in session or session.get('role') != 'volunteer':
        return jsonify({"error": "Unauthorized"}), 401

    email = None
    try:
        if firestore_db:
            doc = firestore_db.collection('Users').document(session['uid']).get()
            if doc.exists:
                email = doc.to_dict().get('email')
    except Exception:
        email = None

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        volunteer_id = None
        if email:
            cur.execute("SELECT volunteer_id FROM volunteer WHERE email = %s", (email,))
            res = cur.fetchone()
            if res:
                volunteer_id = res.get('volunteer_id')

        if not volunteer_id:
            return jsonify({"totalHours": 0, "upcomingActivities": 0})

        cur.execute("SELECT COALESCE(SUM(hours_worked), 0) AS total FROM participation WHERE volunteer_id = %s", (volunteer_id,))
        total_hours = cur.fetchone().get('total') or 0

        cur.execute("SELECT COUNT(*) AS c FROM participation p JOIN event e ON p.event_id = e.event_id WHERE p.volunteer_id = %s AND e.event_date >= CURDATE()", (volunteer_id,))
        upcoming = cur.fetchone().get('c') or 0
    finally:
        cur.close()
        conn.close()

    return jsonify({"totalHours": float(total_hours), "upcomingActivities": int(upcoming)})


@app.route('/api/add_project', methods=['POST'])
def api_add_project():
    data = request.get_json() or {}
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO event (event_name, event_date, location, description, budget, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get("projectName"),
            data.get("startDate"),
            data.get("location"),
            data.get("description"),
            data.get("budget", 0),
            data.get("status", "Planning"),
            1
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()
    return jsonify({"success": True, "message": "Project added"})


@app.route('/api/send_message', methods=['POST'])
def api_send_message():
    data = request.get_json() or {}
    beneficiary_id = data.get("beneficiaryId")
    subject = data.get("subject")
    message_body = data.get("message")

    if not beneficiary_id or not subject or not message_body:
        return jsonify({"success": False, "message": "Missing beneficiaryId, subject or message"}), 400

    # Fetch beneficiary email
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT full_name, email FROM beneficiary WHERE beneficiary_id = %s", (beneficiary_id,))
        beneficiary = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if not beneficiary or not beneficiary.get("email"):
        return jsonify({"success": False, "message": "Beneficiary not found or no email"}), 404

    if not app.config.get("MAIL_SERVER") or not mail:
        return jsonify({"success": False, "message": "Mail not configured on server. Set MAIL_* in app.config to enable sending."}), 500

    try:
        msg = Message(subject, recipients=[beneficiary["email"]])
        msg.body = message_body
        mail.send(msg)
        return jsonify({"success": True, "message": "Message sent successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/total_counts')
def api_total_counts():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) AS c FROM volunteer")
        total_volunteers = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM donor")
        total_donors = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM beneficiary")
        total_beneficiaries = cur.fetchone()["c"]

        total_stakeholders = total_volunteers + total_donors + total_beneficiaries

        cur.execute("SELECT COUNT(*) AS c FROM event")
        total_projects = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM event")
        total_activities = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM donation")
        total_donation_entries = cur.fetchone()["c"]

        total_entries = (
            total_volunteers + total_donors +
            total_beneficiaries + total_projects + total_donation_entries
        )

        return jsonify({
            "total_volunteers": total_volunteers,
            "total_donors": total_donors,
            "total_beneficiaries": total_beneficiaries,
            "total_stakeholders": total_stakeholders,
            "total_projects": total_projects,
            "total_activities": total_activities,
            "total_entries": total_entries
        })
    finally:
        cur.close()
        conn.close()


@app.route('/api/recent_entries')
def api_recent_entries():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 'Volunteer' AS type, full_name AS name, join_date AS date FROM volunteer
            UNION ALL
            SELECT 'Donor', full_name, created_at FROM donor
            UNION ALL
            SELECT 'Beneficiary', full_name, created_at FROM beneficiary
            UNION ALL
            SELECT 'Event', event_name, event_date FROM event
            UNION ALL
            SELECT 'Donation', CONCAT(donation_type, ' - ', amount), donation_date FROM donation
            ORDER BY date DESC LIMIT 20
        """)
        rows = cur.fetchall()
        for r in rows:
            if r.get("date"):
                r["date"] = r["date"].isoformat()
    finally:
        cur.close()
        conn.close()
    return jsonify(rows)


# -------------------------
# Error handler & run
# -------------------------
@app.errorhandler(500)
def internal_error(error):
    logging.exception("Internal server error")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(debug=True)
