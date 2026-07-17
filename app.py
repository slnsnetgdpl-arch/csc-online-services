import os
import re
import urllib.request
from datetime import datetime, date, timedelta
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

class VisitorLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50))
    visit_date = db.Column(db.Date, default=date.today)
    visit_month = db.Column(db.String(7), default=lambda: datetime.now().strftime('%Y-%m'))

class JobNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

# ----------------------------------------
# 🔍 ఫిక్స్డ్: ఫాస్ట్ సింకింగ్ ఫంక్షన్ (క్రాష్ ప్రొటెక్షన్ తో)
# ----------------------------------------
def sync_and_clean_jobs():
    try:
        # 45 दिनों से पुराने जॉब्स डिलीट करना
        time_threshold = datetime.now() - timedelta(days=45)
        JobNotification.query.filter(JobNotification.created_at < time_threshold).delete()
        db.session.commit()
    except Exception:
        db.session.rollback()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    # 🌐 1. BIKKI NEWS వెబ్‌సైట్ ఫీడ్ సింకింగ్
    try:
        bikki_url = "https://bikkinews.in/feed/"
        bikki_req = urllib.request.Request(bikki_url, headers=headers)
        bikki_xml = urllib.request.urlopen(bikki_req, timeout=2).read().decode('utf-8')
        
        bikki_items = re.findall(r'<item>(.*?)</item>', bikki_xml, re.DOTALL)
        for item in bikki_items[:3]:
            b_title = re.search(r'<title>(.*?)</title>', item)
            b_desc = re.search(r'<description>(.*?)</description>', item)
            
            if b_title and b_desc:
                title_text = re.sub(r'<[^>]*>', '', b_title.group(1)).strip()
                desc_text = re.sub(r'<[^>]*>', '', b_desc.group(1)).replace('<![CDATA[', '').replace(']]>', '').strip()
                
                desc_text = re.sub(r'https?://\S+|www\.\S+', '', desc_text)
                desc_text = re.sub(r'\b\d{10}\b', '[Protected]', desc_text)
                
                existing = JobNotification.query.filter_by(title=title_text).first()
                if not existing and len(desc_text) > 20:
                    new_bikki_job = JobNotification(source="JOB UPDATE", title=title_text, text=desc_text)
                    db.session.add(new_bikki_job)
        db.session.commit()
    except Exception:
        db.session.rollback()

    # ✈️ 2. టెలిగ్రామ్ మిర్రర్ ఫీడ్స్ సింకింగ్
    channels = ['bikkinews', 'studybizz', 'tspsc_world', 'Telangana_Jobs', 'eLearningBADI', 'vidyarthinestam']
    for channel in channels:
        try:
            url = f"https://tg.ihtw.site/s/{channel}"
            req = urllib.request.Request(url, headers=headers)
            html = urllib.request.urlopen(req, timeout=2).read().decode('utf-8')
            messages = re.findall(r'<div class="tgme_widget_message_text[^">]*"([^>]*)>(.*?)</div>', html, re.DOTALL)
            
            for msg_match in messages[:2]:
                msg_content = msg_match[1]
                text = re.sub(r'<br\s*/?>', '\n', msg_content)
                text = re.sub(r'<[^>]*>', '', text)
                text = text.replace('&amp;', '&').replace('&quot;', '"').replace('&apos;', "'").strip()
                
                if len(text) < 35:
                    continue
                
                text = re.sub(r'https?://\S+|www\.\S+', '', text)
                text = re.sub(r'\S+\.(com|in|net|org|info|edu|gov|xyz|co|me|site)\b', '', text)
                text = re.sub(r't\.me/\S+', '', text)
                text = re.sub(r'\b\d{10}\b|\b\d{5}[-\s]\d{5}\b', '[Protected]', text)
                text = re.sub(r' +', ' ', text).strip()
                
                first_line = text.split('\n')[0].strip()
                title = first_line[:40] + "..." if len(first_line) > 40 else first_line
                
                existing = JobNotification.query.filter_by(text=text).first()
                if not existing and text:
                    new_job = JobNotification(source="JOB UPDATE", title=title, text=text)
                    db.session.add(new_job)
            db.session.commit()
        except Exception:
            db.session.rollback()
            continue

    # 🔄 పటిష్టమైన మార్పు: ఏదైనా నెట్‌వర్క్ ఎర్రర్ వచ్చినా తిరగకుండా డేటాబేస్ లో ఉన్న పాత జాబ్స్ ని ఇన్‌స్టంట్‌గా పంపుతుంది
    try:
        all_jobs = JobNotification.query.order_by(JobNotification.created_at.desc()).limit(15).all()
        if all_jobs:
            return all_jobs
    except Exception:
        pass

    # ఒకవేళ డేటాబేస్ పూర్తిగా ఖాళీగా ఉంటే లోడింగ్ ఇండికేటర్ ఆపడానికి డెమో బాక్స్
    return [
        JobNotification(id=999, source="JOB UPDATE", title="తాజా ఎడ్యుకేషన్ & జాబ్ నోటిఫికేషన్ వివరాలు", text="తాజా విద్యా మరియు ఉద్యోగ సమాచారం ఇక్కడ ఆటోమేటిక్‌గా ప్రదర్శించబడుతుంది. వివరాల కోసం దయచేసి కొద్దిసేపటి తర్వాత పేజీని రీఫ్రెష్ చేయండి.", created_at=datetime.now())
    ]

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
        body { background: #f0f4f8; font-family: 'Segoe UI', sans-serif; color: #333; min-height: 100vh; overflow-x: hidden; }
        .navbar { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364) !important; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 1030; }
        .card { box-shadow: 0 4px 8px rgba(0,0,0,0.05); border: none; margin-bottom: 25px; transition: transform 0.2s; scroll-margin-top: 90px; }
        .card:hover { transform: translateY(-3px); }
        .form-label { font-weight: 600; }
        .note-box { color: #b58900; background: #fff3cd; padding: 10px; border-radius: 5px; font-size: 14px; border-left: 4px solid #ffc107; }
        
        .wrapper { display: flex; width: 100%; align-items: stretch; }
        
        #sidebar-left { min-width: 240px; max-width: 240px; background: linear-gradient(180deg, #0f2027, #203a43); color: #fff; min-height: calc(100vh - 56px); padding-top: 20px; box-shadow: 4px 0 10px rgba(0,0,0,0.1); }
        #sidebar-left .menu-header { padding: 10px 20px; background: rgba(0,0,0,0.2); border-bottom: 1px solid rgba(255,255,255,0.1); font-weight: bold; }
        #sidebar-left ul li a { padding: 12px 20px; font-size: 14px; display: block; color: rgba(255,255,255,0.8); text-decoration: none; transition: all 0.3s; font-weight: 500; }
        #sidebar-left ul li a:hover { color: #fff; background: rgba(255,255,255,0.1); border-left: 4px solid #00d2ff; }
        
        #sidebar-right { min-width: 300px; max-width: 300px; background: #fff; min-height: calc(100vh - 56px); padding: 20px 12px; box-shadow: -4px 0 10px rgba(0,0,0,0.05); border-left: 1px solid #e2e8f0; }
        #sidebar-right .job-link { display: block; padding: 12px; margin-bottom: 10px; background: #f8fafc; border-left: 4px solid #ffc107; color: #1e293b; text-decoration: none; border-radius: 0 6px 6px 0; font-size: 13.5px; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.02); transition: all 0.2s; }
        #sidebar-right .job-link:hover { background: #fff3cd; color: #b45309; transform: translateX(3px); }
        
        #content { flex-grow: 1; padding: 30px; min-height: calc(100vh - 56px); background: #f8fafc; }
        
        .whatsapp-float { position: fixed; bottom: 20px; right: 20px; background: #25d366; color: white; padding: 12px 20px; border-radius: 30px; font-weight: bold; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.2); z-index: 9999; }
        
        .brand-logo-card {
            background: #fff; border-radius: 8px; padding: 15px 10px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.05); font-weight: 700; font-size: 13px; display: flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid #e2e8f0; transition: all 0.3s;
        }
        .brand-logo-card:hover { transform: translateY(-4px); box-shadow: 0 6px 15px rgba(0,0,0,0.1); }

        .visitor-counter-box {
            background: linear-gradient(135deg, #0f2027, #203a43); color: #fff; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 14px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }

        @media (max-width: 1200px) {
            .wrapper { flex-direction: column; }
            #sidebar-left, #sidebar-right { min-width: 100%; max-width: 100%; min-height: auto; }
        }
    </style>
</head>
<body>
<nav class="navbar navbar-dark navbar-expand-lg sticky-top">
    <div class="container-fluid px-4">
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

<div class="wrapper">
    <!-- 🗂️ ఎడమ వైపు మెనూ బార్ -->
    <nav id="sidebar-left">
        <div class="menu-header text-center">🏢 SLNS Services</div>
        <ul class="list-unstyled components m-0 p-0">
            <li><a href="#standard-pan"><i class="fas fa-file-alt me-2"></i> 1. Standard PAN Card</a></li>
            <li><a href="#address-update"><i class="fas fa-home me-2"></i> 2. Aadhaar Address Update</a></li>
            <li><a href="#birth-pan"><i class="fas fa-certificate me-2"></i> 3. PAN with Birth Proof</a></li>
            <hr style="border-color: rgba(255,255,255,0.15); margin: 10px 0;">
            <div class="px-3 py-1 text-info" style="font-size: 11px; font-weight: bold; text-transform: uppercase;">Insurance Forms</div>
            <li><a href="#health-insurance" style="color: #00d2ff;"><i class="fas fa-heartbeat me-2"></i> Health Insurance</a></li>
            <li><a href="#vehicle-insurance" style="color: #ff416c;"><i class="fas fa-car me-2"></i> Vehicle Insurance</a></li>
            <li><a href="#life-insurance" style="color: #ffb199;"><i class="fas fa-umbrella me-2"></i> Life Insurance</a></li>
        </ul>
    </nav>

    <!-- 💻 మధ్యలో కంటెంట్ ఏరియా -->
    <div id="content">
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
    </div> <!-- content closing -->

    <!-- 💼 కుడివైపు మెనూ బార్: జాబ్ నోటిఫికేషన్స్ లింకులు -->
    <nav id="sidebar-right">
        <h5 class="text-dark font-weight-bold mb-3 pb-2" style="border-bottom: 2px solid #ffc107;"><i class="fas fa-briefcase text-warning me-2"></i> Job Notifications</h5>
        <p class="text-muted" style="font-size: 11px;">లేటెస్ట్ అప్‌డేట్స్ పైన ఉంటాయి. క్లిక్ చేసి పూర్తి వివరాలు చూడండి.</p>
        
        <div style="max-height: 650px; overflow-y: auto;">
            {% if job_updates %}
                {% for job in job_updates %}
                    <a href="#" class="job-link" data-bs-toggle="modal" data-bs-target="#jobModal{{ job.id }}">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="badge bg-warning text-dark text-uppercase" style="font-size:9px; padding:2px 5px; font-weight:700;">{{ job.source }}</span>
                            <span class="text-muted" style="font-size:10px;"><i class="far fa-clock"></i> {{ job.created_at.strftime('%d-%b %I:%M %p') }}</span>
                        </div>
                        <div style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.4;">{{ job.title }}</div>
                    </a>
                {% endfor %}
            {% else %}
                <p class="text-muted text-center" style="font-size:12px;"><i class="fas fa-sync fa-spin"></i> Loading updates...</p>
            {% endif %}
        </div>
    </nav>
</div> <!-- wrapper closing -->

<!-- 📑 ప్రతి జాబ్ లింక్ కోసం పాప్-అప్ విండోలు -->
{% if job_updates %}
    {% for job in job_updates %}
    <div class="modal fade" id="jobModal{{ job.id }}" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered modal-lg modal-dialog-scrollable">
        <div class="modal-content text-dark" style="border-radius:12px; box-shadow:0 10px 30px rgba(0,0,0,0.15);">
          <div class="modal-header bg-dark text-white py-3">
            <div>
               <h5 class="modal-title font-weight-bold"><i class="fas fa-bullhorn text-warning me-2"></i> SLNS Job Alert Notification</h5>
               <small class="text-white-50">Posted on: {{ job.created_at.strftime('%d-%m-%Y %I:%M %p') }}</small>
            </div>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body p-4" style="font-size: 15px; line-height: 1.7; white-space: pre-wrap; background: #fafafa; color: #1e293b;">{{ job.text }}</div>
          
          <!-- 💬 కాంటాక్ట్ సపోర్ట్ బటన్స్ సెక్షన్ -->
          <div class="p-3 bg-light border-top text-center">
             <h6 class="font-weight-bold text-dark mb-3" style="font-size: 13px;">📞 ఈ ఉద్యోగానికి ఆన్‌లైన్ లో అప్లై చేయడానికి మా సపోర్ట్ టీమ్‌ను సంప్రదించండి:</h6>
             <div class="d-flex flex-wrap justify-content-center gap-3">
                 <a href="https://wa.me/919390038979" target="_blank" class="btn btn-success px-4 py-2 font-weight-bold shadow-sm" style="border-radius:6px;"><i class="fab fa-whatsapp me-2"></i> WhatsApp Help</a>
                 <a href="https://t.me/pancsc" target="_blank" class="btn btn-info px-4 py-2 font-weight-bold shadow-sm text-white" style="border-radius:6px; background:#0088cc;"><i class="fab fa-telegram-plane me-2"></i> Telegram Channel</a>
             </div>
          </div>
          
          <div class="modal-footer py-2 bg-light">
            <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Close Window</button>
          </div>
        </div>
      </div>
    </div>
    {% endfor %}
{% endif %}

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
    <div class="col-md-6" id="standard-pan">
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
    <div class="col-md-6" id="address-update">
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
<div class="row mt-4" id="birth-pan">
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
    <div class="col-md-4 mb-4" id="health-insurance">
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
    <div class="col-md-4 mb-4" id="vehicle-insurance">
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
    <div class="col-md-4 mb-4" id="life-insurance">
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

<!-- 🏢 REALISTIC INSURANCE BRANDS LOGO SECTION -->
<div class="row mt-5 mb-4">
    <div class="col-12 text-center mb-4">
        <h3 style="color: #2c5364; font-weight: 700; border-bottom: 3px solid #203a43; display: inline-block; padding-bottom: 10px;">🤝 Our Authorized Insurance Partners</h3>
    </div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card" style="border-left: 4px solid #003366;"><i class="fas fa-shield-alt" style="color:#003366;"></i> TATA AIA Life</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card" style="border-left: 4px solid #003366;"><i class="fas fa-car-crash" style="color:#003366;"></i> TATA AIG Gen</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card" style="border-left: 4px solid #005ea6;"><i class="fas fa-chart-line" style="color:#005ea6;"></i> Bajaj Allianz</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card" style="border-left: 4px solid #009639;"><i class="fas fa-user-md" style="color:#009639;"></i> Niva Bupa</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card" style="border-left: 4px solid #004c8f;"><i class="fas fa-hotel" style="color:#004c8f;"></i> HDFC ERGO</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card" style="border-left: 4px solid #f26522;"><i class="fas fa-ambulance" style="color:#f26522;"></i> ICICI Lombard</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card" style="border-left: 4px solid #0a5697;"><i class="fas fa-star" style="color:#ffc107;"></i> Star Health</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card" style="border-left: 4px solid #1a3668;"><i class="fas fa-university" style="color:#1a3668;"></i> SBI General</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card" style="border-left: 4px solid #0072bc;"><i class="fas fa-industry" style="color:#0072bc;"></i> Chola MS</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card" style="border-left: 4px solid #ce1126;"><i class="fas fa-building" style="color:#ce1126;"></i> United India</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card" style="border-left: 4px solid #0b2f61;"><i class="fas fa-handshake" style="color:#0b2f61;"></i> Universal Sompo</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card" style="border-left: 4px solid #97144d;"><i class="fas fa-credit-card" style="color:#97144d;"></i> Axis Life</div></div>
</div>

<!-- 📊 LIVE VISITOR COUNTER SECTION -->
<div class="row mt-4 mb-2 justify-content-center">
    <div class="col-md-6">
        <div class="visitor-counter-box">
            <span>📊 SLNS Traffic Analytics Counter</span>
            <div class="d-flex justify-content-around mt-2 pt-2" style="border-top: 1px solid rgba(255,255,255,0.2);">
                <div>📅 Today Visitors: <span class="badge bg-warning text-dark px-2 py-1" style="font-size:15px;">{{ stats.today_count }}</span></div>
                <div>🗓️ Current Month: <span class="badge bg-info text-white px-2 py-1" style="font-size:15px;">{{ stats.month_count }}</span></div>
                <div>👥 Total Hits: <span class="badge bg-success text-white px-2 py-1" style="font-size:15px;">{{ stats.total_count }}</span></div>
            </div>
        </div>
    </div>
</div>
"""

# ----------------------------------------
# 🚀 అప్లికేషన్ రూట్స్ (Routes & Controllers)
# ----------------------------------------

@app.route('/')
def index():
    user_ip = request.remote_addr
    today_dt = date.today()
    current_m = datetime.now().strftime('%Y-%m')
    
    try:
        existing_log = VisitorLog.query.filter_by(ip_address=user_ip, visit_date=today_dt).first()
        if not existing_log:
            new_log = VisitorLog(ip_address=user_ip, visit_date=today_dt, visit_month=current_m)
            db.session.add(new_log)
            db.session.commit()
    except Exception:
        db.session.rollback()
        
    today_count = VisitorLog.query.filter_by(visit_date=today_dt).count()
    month_count = VisitorLog.query.filter_by(visit_month=current_m).count()
    total_count = VisitorLog.query.count()
    
    stats = {
        'today_count': today_count if today_count > 0 else 1,
        'month_count': month_count if month_count > 0 else 1,
        'total_count': total_count if total_count > 0 else 1
    }

    jobs = sync_and_clean_jobs()
    return render_template_string(HTML_HEADER + INDEX_CONTENT + HTML_FOOTER, job_updates=jobs, stats=stats)

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
    flash("PAN Application with Birth Proof submitted successfully!")
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
    flash("Health Insurance inquiry submitted successfully!")
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

# 🔒 అడ్మిన్ లాగిన్ & డాష్‌బోర్డ్ సెక్షన్
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == 'Ravi@123':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Username or Password!')
    return render_template_string('''
        <div style="max-width: 400px; margin: 100px auto; padding: 30px; border: 1px solid #ddd; border-radius: 8px; font-family: sans-serif;">
            <h2 style="text-align: center;">SLNS Admin Login</h2>
            <form method="POST">
                <div style="margin-bottom: 15px;"><label>Username:</label><input type="text" name="username" required style="width: 100%; padding: 8px;"></div>
                <div style="margin-bottom: 20px;"><label>Password:</label><input type="password" name="password" required style="width: 100%; padding: 8px;"></div>
                <button type="submit" style="background: #007bff; color: white; padding: 10px; width: 100%; border: none;">Login</button>
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
    <div class="container mt-5 text-dark">
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
                <thead><tr><th>Name</th><th>Father Name</th><th>Mobile</th><th>DOB</th></tr></thead>
                <tbody>{% for p in pans %}<tr><td>{{p.full_name}}</td><td>{{p.father_name}}</td><td>{{p.mobile_num}}</td><td>{{p.dob}}</td></tr>{% endfor %}</tbody>
            </table>
          </div>
          <div class="tab-pane fade" id="tab2">
            <table class="table table-striped mt-2">
                <thead><tr><th>Voter ID</th><th>Mobile</th><th>Address</th></tr></thead>
                <tbody>{% for a in addresses %}<tr><td>{{a.voter_num}}</td><td>{{a.mobile_num}}</td><td>{{a.address}}</td></tr>{% endfor %}</tbody>
            </table>
          </div>
          <div class="tab-pane fade" id="tab3">
            <table class="table table-striped mt-2">
                <thead><tr><th>Candidate</th><th>Father</th><th>Proof Type</th><th>Files</th></tr></thead>
                <tbody>{% for b in birth_pans %}<tr><td>{{b.candidate_name}}</td><td>{{b.father_name}}</td><td>{{b.birth_proof_type}}</td><td><small>📸 {{b.photo_filename}}<br>✍️ {{b.signature_filename}}</small></td></tr>{% endfor %}</tbody>
            </table>
          </div>
          <div class="tab-pane fade" id="tab4">
            <h5 class="text-info">❤️ Health Insurance</h5>
            <table class="table table-sm table-bordered"><tbody>{% for h in health_reqs %}<tr><td>{{h.full_name}}</td><td>{{h.mobile_num}}</td><td>{{h.age}}</td></tr>{% endfor %}</tbody></table>
            <h5 class="text-danger mt-3">🚗 Vehicle Insurance</h5>
            <table class="table table-sm table-bordered"><tbody>{% for v in vehicle_reqs %}<tr><td>{{v.full_name}}</td><td>{{v.mobile_num}}</td><td>{{v.vehicle_number}}</td></tr>{% endfor %}</tbody></table>
            <h5 class="text-warning mt-3">☂️ Life Insurance</h5>
            <table class="table table-sm table-bordered"><tbody>{% for l in life_reqs %}<tr><td>{{l.full_name}}</td><td>{{l.mobile_num}}</td><td>{{l.coverage_amount}}</td></tr>{% endfor %}</tbody></table>
          </div>
        </div>
        <div class="mt-4"><a href="/" class="btn btn-secondary btn-sm">← Back to Main Web Portal</a></div>
    </div>
    """
    return render_template_string('<!DOCTYPE html><html><head><title>Dashboard</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"></head><body class="bg-light">' + DASHBOARD_CONTENT + '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>', pans=pans, addresses=addresses, birth_pans=birth_pans, health_reqs=health_reqs, vehicle_reqs=vehicle_reqs, life_reqs=life_reqs)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
