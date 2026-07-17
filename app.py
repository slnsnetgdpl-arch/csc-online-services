import os
import re
import urllib.request
from datetime import datetime, date, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, flash, session, jsonify
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
# 🔍 వీక్లీ-సింక్ అండ్ ఫోర్స్ లోడింగ్ ఇంజిన్
# ----------------------------------------
def sync_and_clean_jobs():
    # 🛑 1. 45 రోజుల పాత డేటా ఆటోమేటిక్ డిలీట్ రూల్
    try:
        time_threshold = datetime.now() - timedelta(days=45)
        JobNotification.query.filter(JobNotification.created_at < time_threshold).delete()
        db.session.commit()
    except Exception:
        db.session.rollback()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    # 🌐 A. BIKKI NEWS వెబ్‌సైట్ నుండి డేటా సేకరించడం (టాప్ 15 పోస్టులు)
    try:
        bikki_url = "https://bikkinews.in/feed/"
        bikki_req = urllib.request.Request(bikki_url, headers=headers)
        bikki_xml = urllib.request.urlopen(bikki_req, timeout=4).read().decode('utf-8')
        
        bikki_items = re.findall(r'<item>(.*?)</item>', bikki_xml, re.DOTALL)
        for item in bikki_items[:15]: 
            b_title = re.search(r'<title>(.*?)</title>', item)
            b_desc = re.search(r'<description>(.*?)</description>', item)
            
            if b_title and b_desc:
                title_text = re.sub(r'<[^>]*>', '', b_title.group(1)).strip()
                desc_text = re.sub(r'<[^>]*>', '', b_desc.group(1)).replace('<![CDATA[', '').replace(']]>', '').strip()
                
                # ప్రొటెక్టెడ్ ఫిల్టర్స్
                desc_text = re.sub(r'https?://\S+|www\.\S+', '', desc_text)
                desc_text = re.sub(r'\b\d{10}\b', '[Protected]', desc_text)
                
                existing = JobNotification.query.filter_by(title=title_text).first()
                if not existing and len(desc_text) > 20:
                    db.session.add(JobNotification(source="JOB UPDATE", title=title_text, text=desc_text))
        db.session.commit()
    except Exception:
        db.session.rollback()

    # ✈️ B. టెలిగ్రామ్ ఫీడ్స్ నుండి డేటా సేకరించడం (వారం రోజుల బ్యాక్‌లాగ్‌తో)
    channels = ['bikkinews', 'studybizz', 'tspsc_world', 'Telangana_Jobs', 'eLearningBADI', 'vidyarthinestam']
    for channel in channels:
        try:
            url = f"https://tg.ihtw.site/s/{channel}"
            req = urllib.request.Request(url, headers=headers)
            html = urllib.request.urlopen(req, timeout=4).read().decode('utf-8')
            messages = re.findall(r'<div class="tgme_widget_message_text[^">]*"([^>]*)>(.*?)</div>', html, re.DOTALL)
            
            # మొదటి రోజు/వారం అప్‌డేట్స్ కోసం ప్రతి ఛానెల్ నుండి గరిష్టంగా 6 లేటెస్ట్ పోస్టులను లోడ్ చేస్తుంది
            for msg_match in messages[:6]:
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
                title = first_line[:45] + "..." if len(first_line) > 45 else first_line
                if not title or len(title) < 5:
                    title = text[:45] + "..."
                
                existing = JobNotification.query.filter_by(text=text).first()
                if not existing and text:
                    db.session.add(JobNotification(source="JOB UPDATE", title=title, text=text))
            db.session.commit()
        except Exception:
            db.session.rollback()
            continue

    # డేటాబేస్ లోని మొత్తం సమాచారాన్ని (గత వారం నుండి ఇప్పటిదాకా ఉన్నవన్నీ) ఆర్డర్ లో పంపుతుంది
    return JobNotification.query.order_by(JobNotification.created_at.desc()).all()

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
        
        #sidebar-right { min-width: 310px; max-width: 310px; background: #fff; min-height: calc(100vh - 56px); padding: 20px 12px; box-shadow: -4px 0 10px rgba(0,0,0,0.05); border-left: 1px solid #e2e8f0; }
        #sidebar-right .job-link { display: block; padding: 12px; margin-bottom: 10px; background: #f8fafc; border-left: 4px solid #ffc107; color: #1e293b; text-decoration: none; border-radius: 0 6px 6px 0; font-size: 13px; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.02); transition: all 0.2s; }
        #sidebar-right .job-link:hover { background: #fff3cd; color: #b45309; transform: translateX(3px); }
        
        #content { flex-grow: 1; padding: 30px; min-height: calc(100vh - 56px); background: #f8fafc; }
        .whatsapp-float { position: fixed; bottom: 20px; right: 20px; background: #25d366; color: white; padding: 12px 20px; border-radius: 30px; font-weight: bold; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.2); z-index: 9999; }
        .brand-logo-card { background: #fff; border-radius: 8px; padding: 15px 10px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.05); font-weight: 700; font-size: 13px; display: flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid #e2e8f0; }
        .visitor-counter-box { background: linear-gradient(135deg, #0f2027, #203a43); color: #fff; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 14px; }

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

    <div id="content">
"""

HTML_FOOTER = """
    </div> <!-- content closing -->

    <!-- 💼 కుడివైపు మెనూ బార్: డైనమిక్ AJAX లోడింగ్ బార్ -->
    <nav id="sidebar-right">
        <h5 class="text-dark font-weight-bold mb-3 pb-2" style="border-bottom: 2px solid #ffc107;"><i class="fas fa-briefcase text-warning me-2"></i> Job Notifications</h5>
        <p class="text-muted" style="font-size: 11px;">తాజా ఉద్యోగ సమాచారం కింద ప్రదర్శించబడుతోంది.</p>
        
        <div id="jobs-container" style="max-height: 550px; overflow-y: auto; padding-right:5px;">
            <p class="text-muted text-center py-3" id="jobs-loading-status">
                <i class="fas fa-sync fa-spin me-1"></i> తాజా నోటిఫికేషన్లు లోడ్ అవుతున్నాయి...
            </p>
        </div>
        <!-- 🔄 Load More బటన్ ఆప్షన్ -->
        <div class="text-center mt-3">
            <button id="load-more-btn" class="btn btn-outline-primary btn-sm w-100 font-weight-bold" style="display:none; border-radius:20px;"><i class="fas fa-plus-circle me-1"></i> Load More News</button>
        </div>
    </nav>
</div>

<div id="modals-container"></div>

<a href="https://wa.me/919390038979" target="_blank" class="whatsapp-float">
    📲 Live Help Chat
</a>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<!-- 🧠 అప్‌గ్రేడెడ్ AJAX ఇంజిన్ స్క్రిప్ట్ -->
<script>
document.addEventListener("DOMContentLoaded", function() {
    let allJobs = [];
    let displayedCount = 0;
    const itemsPerPage = 5; // ఒకేసారి 5 వార్తలు మాత్రమే లోడ్ అవుతాయి

    const container = document.getElementById('jobs-container');
    const modalsContainer = document.getElementById('modals-container');
    const loadMoreBtn = document.getElementById('load-more-btn');

    fetch('/api/jobs')
        .then(response => response.json())
        .then(data => {
            allJobs = data;
            container.innerHTML = ''; 
            
            if(!allJobs || allJobs.length === 0) {
                container.innerHTML = '<p class="text-muted text-center py-2">సమాచారం అందుబాటులో లేదు. దయచేసి కొద్దిసేపటి తర్వాత రీఫ్రెష్ చేయండి.</p>';
                return;
            }
            
            renderNextJobs(); 
            
            if (allJobs.length > itemsPerPage) {
                loadMoreBtn.style.display = 'block'; 
            }
        })
        .catch(error => {
            container.innerHTML = '<p class="text-muted text-center py-2">తాజా సమాచారం సింక్ అవుతోంది. దయచేసి పేజీని రీఫ్రెష్ చేయండి.</p>';
        });

    function renderNextJobs() {
        const nextSet = allJobs.slice(displayedCount, displayedCount + itemsPerPage);
        
        nextSet.forEach(job => {
            const jobLink = document.createElement('a');
            jobLink.href = "#";
            jobLink.className = "job-link";
            jobLink.setAttribute("data-bs-toggle", "modal");
            jobLink.setAttribute("data-bs-target", `#jobModal${job.id}`);
            jobLink.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="badge bg-warning text-dark text-uppercase" style="font-size:9px; padding:2px 5px; font-weight:700;">JOB UPDATE</span>
                    <span class="text-muted" style="font-size:10px;"><i class="far fa-clock"></i> ${job.time_str}</span>
                </div>
                <div style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.4; font-weight:600;">${job.title}</div>
            `;
            container.appendChild(jobLink);
            
            const modalDiv = document.createElement('div');
            modalDiv.className = "modal fade";
            modalDiv.id = `jobModal${job.id}`;
            modalDiv.setAttribute("tabindex", "-1");
            modalDiv.innerHTML = `
              <div class="modal-dialog modal-dialog-centered modal-lg modal-dialog-scrollable">
                <div class="modal-content text-dark" style="border-radius:12px; box-shadow:0 10px 30px rgba(0,0,0,0.15);">
                  <div class="modal-header bg-dark text-white py-3">
                    <div>
                       <h5 class="modal-title font-weight-bold"><i class="fas fa-bullhorn text-warning me-2"></i> SLNS Job Alert</h5>
                       <small class="text-white-50">Posted on: ${job.date_str}</small>
                    </div>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                  </div>
                  <div class="modal-body p-4" style="font-size: 15px; line-height: 1.7; white-space: pre-wrap; background: #fafafa; color: #1e293b;">${job.text}</div>
                  <div class="p-3 bg-light border-top text-center">
                     <h6 class="font-weight-bold text-dark mb-3" style="font-size: 13px;">📞 ఈ ఉద్యోగానికి ఆన్‌లైన్ లో అప్లై చేయడానికి మా సపోర్ట్ టీమ్‌ను సంప్రదించండి:</h6>
                     <div class="d-flex flex-wrap justify-content-center gap-3">
                         <a href="https://wa.me/919390038979" target="_blank" class="btn btn-success px-4 py-2 font-weight-bold shadow-sm" style="border-radius:6px;"><i class="fab fa-whatsapp me-2"></i> WhatsApp Help</a>
                     </div>
                  </div>
                  <div class="modal-footer py-2 bg-light">
                    <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Close Window</button>
                  </div>
                </div>
              </div>
            `;
            modalsContainer.appendChild(modalDiv);
        });

        displayedCount += nextSet.length;
        if (displayedCount >= allJobs.length) {
            loadMoreBtn.style.display = 'none';
        }
    }

    loadMoreBtn.addEventListener('click', function() {
        renderNextJobs();
    });
});
</script>
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
                <div class="mb-3"><label class="form-label">A. Full Name of the Person</label><input type="text" name="full_name" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">B. Father's Name</label><input type="text" name="father_name" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">C. Mother's Name</label><input type="text" name="mother_name" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">D. Aadhaar Card Number</label><input type="text" name="aadhaar_num" class="form-control" placeholder="12 digit number" required></div>
                <div class="mb-3"><label class="form-label">E. Date of Birth</label><input type="date" name="dob" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">F. Aadhaar Linked Mobile Number</label><input type="tel" name="mobile_num" class="form-control" required></div>
                <button type="submit" class="btn btn-primary w-100">Submit Standard PAN Application</button>
            </form>
        </div>
    </div>

    <!-- ఫారమ్ 2: Aadhaar Address Update -->
    <div class="col-md-6" id="address-update">
        <div class="card p-4">
            <h4 class="text-success mb-3">🏠 2. Aadhaar Address Update</h4>
            <form action="/update-address" method="POST">
                <div class="mb-3"><label class="form-label">A. Voter ID Number</label><input type="text" name="voter_num" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">B. Aadhaar Card Number</label><input type="text" name="aadhaar_num" class="form-control" placeholder="12 digit number" required></div>
                <div class="mb-3"><label class="form-label">C. Aadhaar Linked Mobile Number</label><input type="tel" name="mobile_num" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">Write Complete Address</label><textarea name="address" class="form-control" rows="4" required></textarea></div>
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
                    <div class="col-md-6 mb-3"><label class="form-label">Full Name of the Candidate</label><input type="text" name="candidate_name" class="form-control" required></div>
                    <div class="col-md-6 mb-3"><label class="form-label">Father Full Name</label><input type="text" name="father_name" class="form-control" required></div>
                    <div class="col-md-6 mb-3"><label class="form-label">Mother Full Name</label><input type="text" name="mother_name" class="form-control" required></div>
                    <div class="col-md-6 mb-3"><label class="form-label">Date of Birth</label><input type="date" name="dob" class="form-control" required></div>
                    <div class="col-md-6 mb-3"><label class="form-label">Aadhaar Number</label><input type="text" name="aadhaar_num" class="form-control" required></div>
                    <div class="col-md-6 mb-3"><label class="form-label">Aadhaar Linked Mobile Number</label><input type="tel" name="mobile_num" class="form-control" required></div>
                    <div class="col-md-12 mb-4">
                        <label class="form-label">Choose the Birth Proof</label>
                        <select name="birth_proof_type" class="form-select" required>
                            <option value="Birth Certificate">Birth Certificate</option>
                            <option value="Class 10 Certificate">Class 10/Matriculation Certificate</option>
                        </select>
                    </div>
                </div>
                <button type="submit" class="btn btn-danger w-100 py-2 btn-lg">Pay ₹299 & Submit Application</button>
            </form>
        </div>
    </div>
</div>

<!-- 🛡️ INSURANCE SERVICES SECTION -->
<div class="row mt-5">
    <div class="col-12 text-center mb-4"><h2 style="color: #2c5364; font-weight: 700;">🛡️ Insurance Customer Request Forms</h2></div>
    <div class="col-md-4 mb-4" id="health-insurance">
        <div class="card p-4 h-100" style="border-top: 5px solid #00d2ff;">
            <h4>Health Insurance</h4>
            <form action="/request-health-insurance" method="POST">
                <input type="text" name="full_name" placeholder="Name" class="form-control mb-2" required>
                <input type="tel" name="mobile_num" placeholder="Mobile" class="form-control mb-2" required>
                <input type="number" name="age" placeholder="Age" class="form-control mb-2" required>
                <button type="submit" class="btn btn-info text-white w-100">Get Health Quote</button>
            </form>
        </div>
    </div>
    <div class="col-md-4 mb-4" id="vehicle-insurance">
        <div class="card p-4 h-100" style="border-top: 5px solid #ff416c;">
            <h4>Vehicle Insurance</h4>
            <form action="/request-vehicle-insurance" method="POST">
                <input type="text" name="full_name" placeholder="Name" class="form-control mb-2" required>
                <input type="tel" name="mobile_num" placeholder="Mobile" class="form-control mb-2" required>
                <input type="text" name="vehicle_number" placeholder="Vehicle No" class="form-control mb-2" required>
                <button type="submit" class="btn btn-danger w-100" style="background:#ff416c; border:none;">Get Vehicle Quote</button>
            </form>
        </div>
    </div>
    <div class="col-md-4 mb-4" id="life-insurance">
        <div class="card p-4 h-100" style="border-top: 5px solid #ffb199;">
            <h4>Life Insurance</h4>
            <form action="/request-life-insurance" method="POST">
                <input type="text" name="full_name" placeholder="Name" class="form-control mb-2" required>
                <input type="tel" name="mobile_num" placeholder="Mobile" class="form-control mb-2" required>
                <input type="date" name="dob" class="form-control mb-2" required>
                <button type="submit" class="btn w-100 text-white" style="background:#ffb199; border:none;">Get Life Quote</button>
            </form>
        </div>
    </div>
</div>

<!-- 🏢 top insurance partners -->
<div class="row mt-5 mb-4 text-center">
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card">🛡️ TATA AIA Life</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card">🚗 TATA AIG Gen</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card">📈 Bajaj Allianz</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card">🩺 Niva Bupa</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card">🏠 HDFC ERGO</div></div>
    <div class="col-6 col-md-2 mb-3"><div class="brand-logo-card">🚙 ICICI Lombard</div></div>
</div>

<!-- 📊 LIVE VISITOR COUNTER SECTION -->
<div class="row mt-4 mb-2 justify-content-center">
    <div class="col-md-6">
        <div class="visitor-counter-box">
            <span>📊 Traffic Counter</span>
            <div class="d-flex justify-content-around mt-2 pt-2" style="border-top: 1px solid rgba(255,255,255,0.2);">
                <div>📅 Today: <span class="badge bg-warning text-dark">{{ stats.today_count }}</span></div>
                <div>🗓️ Month: <span class="badge bg-info text-white">{{ stats.month_count }}</span></div>
                <div>👥 Total: <span class="badge bg-success text-white">{{ stats.total_count }}</span></div>
            </div>
        </div>
    </div>
</div>
"""

# ----------------------------------------
# 🚀 రోడ్స్ & API కంట్రోలర్స్
# ----------------------------------------

@app.route('/')
def index():
    user_ip = request.remote_addr
    today_dt = date.today()
    current_m = datetime.now().strftime('%Y-%m')
    try:
        if not VisitorLog.query.filter_by(ip_address=user_ip, visit_date=today_dt).first():
            db.session.add(VisitorLog(ip_address=user_ip, visit_date=today_dt, visit_month=current_m))
            db.session.commit()
    except Exception:
        db.session.rollback()
        
    stats = {
        'today_count': VisitorLog.query.filter_by(visit_date=today_dt).count() or 1,
        'month_count': VisitorLog.query.filter_by(visit_month=current_m).count() or 1,
        'total_count': VisitorLog.query.count() or 1
    }
    return render_template_string(HTML_HEADER + INDEX_CONTENT + HTML_FOOTER, stats=stats)

# 🌐 హై-స్పీడ్ బ్యాకెండ్ API రూట్ (ఫోర్స్ సింకింగ్ మోడ్‌తో)
@app.route('/api/jobs')
def get_jobs_api():
    jobs = sync_and_clean_jobs()
    jobs_list = []
    for j in jobs:
        jobs_list.append({
            'id': j.id,
            'source': "JOB UPDATE", 
            'title': j.title,
            'text': j.text,
            'time_str': j.created_at.strftime('%d-%b %I:%M %p'),
            'date_str': j.created_at.strftime('%d-%m-%Y %I:%M %p')
        })
    return jsonify(jobs_list)

@app.route('/apply-pan', methods=['POST'])
def apply_pan():
    db.session.add(PanApplication(full_name=request.form.get('full_name'), father_name=request.form.get('father_name'), mother_name=request.form.get('mother_name'), aadhaar_num=request.form.get('aadhaar_num'), mobile_num=request.form.get('mobile_num'), dob=request.form.get('dob')))
    db.session.commit()
    flash("Standard PAN Application submitted successfully!")
    return redirect(url_for('index'))

@app.route('/update-address', methods=['POST'])
def update_address():
    db.session.add(AddressUpdateApplication(voter_num=request.form.get('voter_num'), aadhaar_num=request.form.get('aadhaar_num'), mobile_num=request.form.get('mobile_num'), address=request.form.get('address')))
    db.session.commit()
    flash("Aadhaar Address Update submitted successfully!")
    return redirect(url_for('index'))

@app.route('/apply-pan-birth', methods=['POST'])
def apply_pan_birth():
    db.session.add(PanWithBirthApplication(candidate_name=request.form.get('candidate_name'), father_name=request.form.get('father_name'), mother_name=request.form.get('mother_name'), dob=request.form.get('dob'), aadhaar_num=request.form.get('aadhaar_num'), mobile_num=request.form.get('mobile_num'), birth_proof_type=request.form.get('birth_proof_type')))
    db.session.commit()
    flash("PAN Application submitted successfully!")
    return redirect(url_for('index'))

@app.route('/request-health-insurance', methods=['POST'])
def request_health():
    db.session.add(HealthInsuranceRequest(full_name=request.form.get('full_name'), mobile_num=request.form.get('mobile_num'), age=request.form.get('age'), medical_history=request.form.get('medical_history')))
    db.session.commit()
    flash("Insurance Request submitted successfully!")
    return redirect(url_for('index'))

@app.route('/request-vehicle-insurance', methods=['POST'])
def request_vehicle():
    db.session.add(VehicleInsuranceRequest(full_name=request.form.get('full_name'), mobile_num=request.form.get('mobile_num'), vehicle_type=request.form.get('vehicle_type'), vehicle_number=request.form.get('vehicle_number')))
    db.session.commit()
    flash("Vehicle Insurance inquiry submitted successfully!")
    return redirect(url_for('index'))

@app.route('/request-life-insurance', methods=['POST'])
def request_life():
    db.session.add(LifeInsuranceRequest(full_name=request.form.get('full_name'), mobile_num=request.form.get('mobile_num'), dob=request.form.get('dob'), coverage_amount=request.form.get('coverage_amount')))
    db.session.commit()
    flash("Life Insurance inquiry submitted successfully!")
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
