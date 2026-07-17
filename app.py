import os
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# డేటాబేస్ పాత్ సెటప్
db_path = os.path.join(basedir, 'instance', 'database.db')
db_dir = os.path.dirname(db_path)
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "slns_secret_admin_key"

db = SQLAlchemy(app)

# 📁 అప్‌లోడ్ ఫోల్డర్ సెటప్
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ----------------------------------------
# 🗄️ డేటాబేస్ మోడల్స్ (Database Models)
# ----------------------------------------

class PanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    father_name = db.Column(db.String(100), nullable=False)
    mother_name = db.Column(db.String(100), nullable=False)
    aadhaar_num = db.Column(db.String(20), nullable=False)
    mobile_num = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AddressUpdateApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_num = db.Column(db.String(50), nullable=False)
    aadhaar_num = db.Column(db.String(20), nullable=False)
    mobile_num = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class PanWithBirthApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_name = db.Column(db.String(100), nullable=False)
    father_name = db.Column(db.String(100), nullable=False)
    mother_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    aadhaar_num = db.Column(db.String(20), nullable=False)
    mobile_num = db.Column(db.String(20), nullable=False)
    birth_proof_type = db.Column(db.String(50), nullable=False)
    photo_filename = db.Column(db.String(100))
    signature_filename = db.Column(db.String(100))
    aadhaar_filename = db.Column(db.String(100))
    birth_proof_filename = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class HealthInsuranceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    mobile_num = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    medical_history = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class VehicleInsuranceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    mobile_num = db.Column(db.String(20), nullable=False)
    vehicle_number = db.Column(db.String(50), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class LifeInsuranceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    mobile_num = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    coverage_amount = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------------------------------
# 🎨 HTML లేఅవుట్ టెంప్లేట్స్ (UI Design)
# ----------------------------------------

HTML_HEADER = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SLNS Online & Insurance Services</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #f0f4f8; font-family: 'Segoe UI', sans-serif; color: #333; position: relative; min-height: 100vh; }
        .navbar { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364) !important; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .card { box-shadow: 0 4px 8px rgba(0,0,0,0.05); border: none; margin-bottom: 25px; transition: transform 0.2s; }
        .card:hover { transform: translateY(-3px); }
        .form-label { font-weight: 600; }
        .note-box { color: #b58900; background: #fff3cd; padding: 10px; border-radius: 5px; font-size: 14px; border-left: 4px solid #ffc107; }
        .whatsapp-float { position: fixed; bottom: 20px; right: 20px; background: #25d366; color: white; padding: 12px 20px; border-radius: 30px; font-weight: bold; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.2); z-index: 9999; transition: transform 0.2s; }
        .whatsapp-float:hover { transform: scale(1.05); color: white; }
    </style>
</head>
<body>
<nav class="navbar navbar-dark navbar-expand-lg">
    <div class="container">
        <a class="navbar-brand font-weight-bold" href="/">🛡️ SLNS ONLINE & INSURANCE SERVICES</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
            <div class="ms-auto d-flex align-items-center gap-2 mt-2 mt-lg-0">
                <a href="https://t.me/pancsc" target="_blank" class="btn btn-info btn-sm text-white">✈️ Join Telegram</a>
                <a href="https://whatsapp.com/channel/0029VbCut5E4o7qH8GUgjO0s" target="_blank" class="btn btn-success btn-sm">💬 WhatsApp Channel</a>
                <a href="/dashboard" class="btn btn-outline-light btn-sm">🔒 Dashboard</a>
            </div>
        </div>
    </div>
</nav>
<div class="container my-5">
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
          <div class="alert alert-success alert-dismissible fade show" role="alert">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
          </div>
        {% endfor %}
      {% endif %}
    {% endwith %}
"""

HTML_FOOTER = """
</div>
<!-- వాట్సాప్ లైవ్ హెల్ప్ చాట్ విజెట్ -->
<a href="https://wa.me/919390038979" target="_blank" class="whatsapp-float">
    📲 Live Help Chat
</a>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

INDEX_CONTENT = """
<div class="row">
    <!-- ఫారమ్ 1: PAN Card Service Standard -->
    <div class="col-md-6">
        <div class="card p-4">
            <h4 class="text-primary mb-3">📝 1. PAN Card Service Application</h4>
            <form action="/apply-pan" method="POST">
                <div class="mb-3">
                    <label class="form-label">A. Full Name of the Person</label>
                    <input type="text" name="full_name" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">B. Father's Name (Including Surname)</label>
                    <input type="text" name="father_name" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">C. Mother's Name (Including Surname)</label>
                    <input type="text" name="mother_name" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">D. Aadhaar Card Number</label>
                    <input type="text" name="aadhaar_num" class="form-control" placeholder="12 digit number" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">E. Date of Birth</label>
                    <input type="date" name="dob" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">F. Aadhaar Linked Mobile Number</label>
                    <input type="tel" name="mobile_num" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">Submit Standard PAN Application</button>
            </form>
        </div>
    </div>

    <!-- ఫారమ్ 2: Aadhaar Address Update -->
    <div class="col-md-6">
        <div class="card p-4">
            <h4 class="text-success mb-3">🏠 2. Aadhaar Address Update</h4>
            <form action="/update-address" method="POST">
                <div class="mb-3">
                    <label class="form-label">A. Voter ID Number</label>
                    <input type="text" name="voter_num" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">B. Aadhaar Card Number</label>
                    <input type="text" name="aadhaar_num" class="form-control" placeholder="12 digit number" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">C. Aadhaar Linked Mobile Number</label>
                    <input type="tel" name="mobile_num" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Write Complete Address (Max 1500 words)</label>
                    <textarea name="address" class="form-control" rows="4" required></textarea>
                </div>
                <button type="submit" class="btn btn-success w-100">Submit Address Update</button>
            </form>
        </div>
    </div>
</div>

<!-- ఫారమ్ 3: PAN Card Apply with Birth Proof -->
<div class="row mt-4">
    <div class="col-12">
        <div class="card p-4" style="border: 1px solid #0d6efd;">
            <h4 class="text-primary mb-3">📜 3. PAN Card Apply with Birth Proof <span class="badge bg-danger">Fee: ₹299</span></h4>
            <form action="/apply-pan-birth" method="POST" enctype="multipart/form-data">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Full Name of the Candidate</label>
                        <input type="text" name="candidate_name" class="form-control" required>
                        <div class="note-box mt-2">
                            ⚠️ <b>Note:</b> Married women also have to enter her father Name and Mother Name with their surname.
                        </div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Father Full Name</label>
                        <input type="text" name="father_name" class="form-control" required>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Mother Full Name</label>
                        <input type="text" name="mother_name" class="form-control" required>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Date of Birth of Candidate</label>
                        <input type="date" name="dob" class="form-control" required>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Aadhaar Number</label>
                        <input type="text" name="aadhaar_num" class="form-control" placeholder="12 digit number" required>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Aadhaar Linked Mobile Number</label>
                        <input type="tel" name="mobile_num" class="form-control" required>
                    </div>
                    <div class="col-md-12 mb-4">
                        <label class="form-label">Choose the Birth Proof</label>
                        <select name="birth_proof_type" class="form-select" required>
                            <option value="">-- Select Birth Proof --</option>
                            <option value="Birth Certificate">Birth Certificate</option>
                            <option value="Passport">Passport</option>
                            <option value="Driving Licence">Driving Licence (with full DOB)</option>
                            <option value="Voter ID">Voter ID (with full DOB)</option>
                            <option value="Class 10 Certificate">Class 10/Matriculation Certificate (where accepted)</option>
                            <option value="Affidavit">Affidavit sworn before the advocate</option>
                        </select>
                    </div>
                </div>

                <div class="p-3 bg-light rounded mb-3 border">
                    <h5 class="mb-3 text-secondary">📁 Upload Required Documents:</h5>
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">1. Upload passport size photo</label>
                            <input type="file" name="photo_file" class="form-control" accept="image/*" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">2. Signature</label>
                            <input type="file" name="signature_file" class="form-control" accept="image/*" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">3. Aadhaar card</label>
                            <input type="file" name="aadhaar_file" class="form-control" accept=".pdf,image/*" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">4. Birth Proof Certificate</label>
                            <input type="file" name="birth_proof_file" class="form-control" accept=".pdf,image/*" required>
                        </div>
                    </div>
                </div>

                <button type="submit" class="btn btn-danger w-100 py-2 btn-lg">Pay ₹299 & Submit Application</button>
            </form>
        </div>
    </div>
</div>

<!-- 🛡️ INSURANCE SERVICES SECTION -->
<div class="row mt-5">
    <div class="col-12 text-center mb-4">
        <h2 style="color: #2c5364; font-weight: 700; border-bottom: 3px solid #203a43; display: inline-block; padding-bottom: 10px;">🛡️ Insurance Customer Request Forms</h2>
        <p class="text-muted">మీకు కావలసిన ఇన్సూరెన్స్ వివరాలను ఇక్కడ నమోదు చేయండి. మేము మిమ్మల్ని సంప్రదిస్తాము.</p>
    </div>

    <!-- 1. Health Insurance Form -->
    <div class="col-md-4 mb-4">
        <div class="card p-4 h-100" style="border-top: 5px solid #00d2ff;">
            <div class="text-center mb-3">
                <i class="fas fa-heartbeat" style="font-size: 45px; color: #00d2ff;"></i>
                <h4 class="mt-2" style="color: #333; font-weight: 600;">Health Insurance</h4>
            </div>
            <form action="/request-health-insurance" method="POST">
                <div class="mb-3">
                    <label class="form-label">Full Name</label>
                    <input type="text" name="full_name" class="form-control" placeholder="మీ పూర్తి పేరు" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Mobile Number</label>
                    <input type="tel" name="mobile_num" class="form-control" placeholder="మొబైల్ నంబర్" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Age of Applicant</label>
                    <input type="number" name="age" class="form-control" placeholder="వయస్సు" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Previous Medical History (If any)</label>
                    <textarea name="medical_history" class="form-control" rows="2" placeholder="ఆరోగ్య సమస్యలు ఉంటే రాయండి..."></textarea>
                </div>
                <button type="submit" class="btn btn-info text-white w-100 py-2">Get Health Quote</button>
            </form>
        </div>
    </div>

    <!-- 2. Vehicle Insurance Form -->
    <div class="col-md-4 mb-4">
        <div class="card p-4 h-100" style="border-top: 5px solid #ff416c;">
            <div class="text-center mb-3">
                <i class="fas fa-car" style="font-size: 45px; color: #ff416c;"></i>
                <h4 class="mt-2" style="color: #333; font-weight: 600;">Vehicle Insurance</h4>
            </div>
            <form action="/request-vehicle-insurance" method="POST">
                <div class="mb-3">
                    <label class="form-label">Full Name</label>
                    <input type="text" name="full_name" class="form-control" placeholder="మీ పూర్తి పేరు" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Mobile Number</label>
                    <input type="tel" name="mobile_num" class="form-control" placeholder="మొబైల్ నంబర్" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Vehicle Type</label>
                    <select name="vehicle_type" class="form-select" required>
                        <option value="">-- Select Type --</option>
                        <option value="Two Wheeler">Two Wheeler (బైక్ / స్కూటర్)</option>
                        <option value="Four Wheeler">Four Wheeler (కారు / ఆటో / ట్రాక్టర్)</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Vehicle Registration Number</label>
                    <input type="text" name="vehicle_number" class="form-control" placeholder="e.g., TS04XX1234" required>
                </div>
                <button type="submit" class="btn btn-danger w-100 py-2" style="background: #ff416c; border: none;">Get Vehicle Quote</button>
            </form>
        </div>
    </div>

    <!-- 3. Life Insurance Form -->
    <div class="col-md-4 mb-4">
        <div class="card p-4 h-100" style="border-top: 5px solid #ffb199;">
            <div class="text-center mb-3">
                <i class="fas fa-umbrella" style="font-size: 45px; color: #ffb199;"></i>
                <h4 class="mt-2" style="color: #333; font-weight: 600;">Life Insurance</h4>
            </div>
            <form action="/request-life-insurance" method="POST">
                <div class="mb-3">
                    <label class="form-label">Full Name</label>
                    <input type="text" name="full_name" class="form-control" placeholder="మీ పూర్తి పేరు" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Mobile Number</label>
                    <input type="tel" name="mobile_num" class="form-control" placeholder="మొబైల్ నంబర్" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Date of Birth</label>
                    <input type="date" name="dob" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Required Policy Term/Coverage</label>
                    <select name="coverage_amount" class="form-select" required>
                        <option value="">-- Select Coverage --</option>
                        <option value="5 Lakhs">₹5 Lakhs Coverage</option>
                        <option value="10 Lakhs">₹10 Lakhs Coverage</option>
                        <option value="20 Lakhs+">₹20 Lakhs+ Coverage</option>
                    </select>
                </div>
                <button type="submit" class="btn w-100 py-2 text-white" style="background: #ffb199; border: none;">Get Life Quote</button>
            </form>
        </div>
    </div>
</div>
"""

# ----------------------------------------
# 🚀 అప్లికేషన్ రూట్స్ (Routes & Controllers)
# ----------------------------------------

@app.route('/')
def index():
    return render_template_string(HTML_HEADER + INDEX_CONTENT + HTML_FOOTER)

@app.route('/apply-pan', methods=['POST'])
def apply_pan():
    new_app = PanApplication(
        full_name=request.form.get('full_name'),
        father_name=request.form.get('father_name'),
        mother_name=request.form.get('mother_name'),
        aadhaar_num=request.form.get('aadhaar_num'),
        mobile_num=request.form.get('mobile_num'),
        dob=request.form.get('dob')
    )
    db.session.add(new_app)
    db.session.commit()
    flash("Standard PAN Application submitted successfully!")
    return redirect(url_for('index'))

@app.route('/update-address', methods=['POST'])
def update_address():
    new_app = AddressUpdateApplication(
        voter_num=request.form.get('voter_num'),
        aadhaar_num=request.form.get('aadhaar_num'),
        mobile_num=request.form.get('mobile_num'),
        address=request.form.get('address')
    )
    db.session.add(new_app)
    db.session.commit()
    flash("Aadhaar Address Update submitted successfully!")
    return redirect(url_for('index'))

@app.route('/apply-pan-birth', methods=['POST'])
def apply_pan_birth():
    f_photo = request.files.get('photo_file')
    f_sig = request.files.get('signature_file')
    f_aadh = request.files.get('aadhaar_file')
    f_birth = request.files.get('birth_proof_file')

    p_name = secure_filename(f_photo.filename) if f_photo else ""
    s_name = secure_filename(f_sig.filename) if f_sig else ""
    a_name = secure_filename(f_aadh.filename) if f_aadh else ""
    b_name = secure_filename(f_birth.filename) if f_birth else ""

    if f_photo: f_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], p_name))
    if f_sig: f_sig.save(os.path.join(app.config['UPLOAD_FOLDER'], s_name))
    if f_aadh: f_aadh.save(os.path.join(app.config['UPLOAD_FOLDER'], a_name))
    if f_birth: f_birth.save(os.path.join(app.config['UPLOAD_FOLDER'], b_name))

    new_app = PanWithBirthApplication(
        candidate_name=request.form.get('candidate_name'),
        father_name=request.form.get('father_name'),
        mother_name=request.form.get('mother_name'),
        dob=request.form.get('dob'),
        aadhaar_num=request.form.get('aadhaar_num'),
        mobile_num=request.form.get('mobile_num'),
        birth_proof_type=request.form.get('birth_proof_type'),
        photo_filename=p_name,
        signature_filename=s_name,
        aadhaar_filename=a_name,
        birth_proof_filename=b_name
    )
    db.session.add(new_app)
    db.session.commit()
    flash("PAN Application with Birth Proof submitted successfully! Fee of ₹299 received.")
    return redirect(url_for('index'))

@app.route('/request-health-insurance', methods=['POST'])
def request_health():
    new_req = HealthInsuranceRequest(
        full_name=request.form.get('full_name'),
        mobile_num=request.form.get('mobile_num'),
        age=request.form.get('age'),
        medical_history=request.form.get('medical_history')
    )
    db.session.add(new_req)
    db.session.commit()
    flash("Health Insurance inquiry submitted successfully! We will contact you soon.")
    return redirect(url_for('index'))

@app.route('/request-vehicle-insurance', methods=['POST'])
def request_vehicle():
    new_req = VehicleInsuranceRequest(
        full_name=request.form.get('full_name'),
        mobile_num=request.form.get('mobile_num'),
        vehicle_type=request.form.get('vehicle_type'),
        vehicle_number=request.form.get('vehicle_number')
    )
    db.session.add(new_req)
    db.session.commit()
    flash("Vehicle Insurance inquiry submitted successfully!")
    return redirect(url_for('index'))

@app.route('/request-life-insurance', methods=['POST'])
def request_life():
    new_req = LifeInsuranceRequest(
        full_name=request.form.get('full_name'),
        mobile_num=request.form.get('mobile_num'),
        dob=request.form.get('dob'),
        coverage_amount=request.form.get('coverage_amount')
    )
    db.session.add(new_req)
    db.session.commit()
    flash("Life Insurance inquiry submitted successfully!")
    return redirect(url_for('index'))

# ----------------------------------------
# 🔒 సెక్యూర్ అడ్మిన్ లాగిన్ & డాష్‌బోర్డ్
# ----------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == 'Ravi@123':
            session['logged_in'] = True
            flash('Successfully logged into Admin Panel!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Username or Password!')
    return render_template_string('''
        <div style="max-width: 400px; margin: 100px auto; padding: 30px; border: 1px solid #ddd; border-radius: 8px; font-family: sans-serif; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <h2 style="text-align: center; color: #333;">SLNS Admin Login</h2>
            {% with messages = get_flashed_messages() %}
              {% if messages %}{% for m in messages %}<p style="color: red; text-align: center;">{{m}}</p>{% endfor %}{% endif %}
            {% endwith %}
            <form method="POST">
                <div style="margin-bottom: 15px;">
                    <label>Username:</label><br>
                    <input type="text" name="username" required style="width: 100%; padding: 10px; margin-top: 5px; box-sizing: border-box;">
                </div>
                <div style="margin-bottom: 20px;">
                    <label>Password:</label><br>
                    <input type="password" name="password" required style="width: 100%; padding: 10px; margin-top: 5px; box-sizing: border-box;">
                </div>
                <button type="submit" style="background: #007bff; color: white; border: none; padding: 12px; width: 100%; border-radius: 4px; font-size: 16px; cursor: pointer;">Login</button>
            </form>
        </div>
    ''')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    pans = PanApplication.query.all()
    addresses = AddressUpdateApplication.query.all()
    birth_pans = PanWithBirthApplication.query.all()
    health_reqs = HealthInsuranceRequest.query.all()
    vehicle_reqs = VehicleInsuranceRequest.query.all()
    life_reqs = LifeInsuranceRequest.query.all()

    DASHBOARD_CONTENT = """
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>🔒 SLNS Admin Dashboard</h2>
        <a href="/logout" class="btn btn-danger btn-sm">Sign Out</a>
    </div>
    
    <ul class="nav nav-tabs" id="myTab" role="tablist">
      <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#tab1">Standard PAN</button></li>
      <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab2">Address Update</button></li>
      <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab3">PAN with Birth</button></li>
      <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab4">Insurance Inquiries</button></li>
    </ul>
    
    <div class="tab-content bg-white p-3 border border-top-0 rounded-bottom">
      <div class="tab-pane fade show active" id="tab1">
        <table class="table table-striped mt-2">
            <thead><tr><th>Name</th><th>Father Name</th><th>Aadhaar [Omitted]</th><th>Mobile</th><th>DOB</th></tr></thead>
            <tbody>
                {% for p in pans %}
                <tr><td>{{p.full_name}}</td><td>{{p.father_name}}</td><td>[Aadhaar Redacted]</td><td>{{p.mobile_num}}</td><td>{{p.dob}}</td></tr>
                {% endfor %}
            </tbody>
        </table>
      </div>
      <div class="tab-pane fade" id="tab2">
        <table class="table table-striped mt-2">
            <thead><tr><th>Voter ID</th><th>Aadhaar [Omitted]</th><th>Mobile</th><th>Address</th></tr></thead>
            <tbody>
                {% for a in addresses %}
                <tr><td>{{a.voter_num}}</td><td>[Aadhaar Redacted]</td><td>{{a.mobile_num}}</td><td>{{a.address}}</td></tr>
                {% endfor %}
            </tbody>
        </table>
      </div>
      <div class="tab-pane fade" id="tab3">
        <table class="table table-striped mt-2">
            <thead><tr><th>Candidate</th><th>Father</th><th>Proof Type</th><th>Aadhaar [Omitted]</th><th>Files</th></tr></thead>
            <tbody>
                {% for b in birth_pans %}
                <tr>
                    <td>{{b.candidate_name}}</td>
                    <td>{{b.father_name}}</td>
                    <td>{{b.birth_proof_type}}</td>
                    <td>[Aadhaar Redacted]</td>
                    <td>
                        <small>
                        📸 Photo: {{b.photo_filename}}<br>
                        ✍️ Sig: {{b.signature_filename}}<br>
                        📄 Aadh: {{b.aadhaar_filename}}<br>
                        📜 Proof: {{b.birth_proof_filename}}
                        </small>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
      </div>
      <div class="tab-pane fade" id="tab4">
        <h5 class="mt-2 text-info">❤️ Health Insurance Requests</h5>
        <table class="table table-sm table-bordered">
            <thead><tr><th>Name</th><th>Mobile</th><th>Age</th><th>History</th></tr></thead>
            <tbody>
                {% for h in health_reqs %}<tr><td>{{h.full_name}}</td><td>{{h.mobile_num}}</td><td>{{h.age}}</td><td>{{h.medical_history}}</td></tr>{% endfor %}
            </tbody>
        </table>
        <h5 class="mt-3 text-danger">🚗 Vehicle Insurance Requests</h5>
        <table class="table table-sm table-bordered">
            <thead><tr><th>Name</th><th>Mobile</th><th>Type</th><th>Vehicle No</th></tr></thead>
            <tbody>
                {% for v in vehicle_reqs %}<tr><td>{{v.full_name}}</td><td>{{v.mobile_num}}</td><td>{{v.vehicle_type}}</td><td>{{v.vehicle_number}}</td></tr>{% endfor %}
            </tbody>
        </table>
        <h5 class="mt-3 text-warning">☂️ Life Insurance Requests</h5>
        <table class="table table-sm table-bordered">
            <thead><tr><th>Name</th><th>Mobile</th><th>DOB</th><th>Coverage</th></tr></thead>
            <tbody>
                {% for l in life_reqs %}<tr><td>{{l.full_name}}</td><td>{{l.mobile_num}}</td><td>{{l.dob}}</td><td>{{l.coverage_amount}}</td></tr>{% endfor %}
            </tbody>
        </table>
      </div>
    </div>
    """
    return render_template_string(HTML_HEADER + DASHBOARD_CONTENT + HTML_FOOTER, pans=pans, addresses=addresses, birth_pans=birth_pans, health_reqs=health_reqs, vehicle_reqs=vehicle_reqs, life_reqs=life_reqs)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
