import os
import urllib.parse
from flask import Flask, render_template_string, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'slns_secret_key_2026'

# 1. డేటాబేస్ కాన్ఫిగరేషన్
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///slns_services.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 2. కేటగిరీల వారీగా కస్టమర్ డేటాబేస్ మోడల్స్ (UTR & Payment Status తో)
class PanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    father_name = db.Column(db.String(150), nullable=False)
    mother_name = db.Column(db.String(150), nullable=False)
    aadhar_masked = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.String(50), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    payment_status = db.Column(db.String(20), default='Pending') # Pending, Paid, Failed
    utr_number = db.Column(db.String(50), default='N/A')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AddressUpdateApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.String(50), nullable=False)
    aadhar_masked = db.Column(db.String(20), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    new_address = db.Column(db.Text, nullable=False)
    payment_status = db.Column(db.String(20), default='Pending') # Pending, Paid, Failed
    utr_number = db.Column(db.String(50), default='N/A')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class CustomerFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(150), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def mask_aadhar(num_str):
    clean = "".join(filter(str.isdigit, num_str))
    if len(clean) >= 4:
        return f"XXXX-XXXX-{clean[-4:]}"
    return "XXXX-XXXX-XXXX"

# 3. HTML హెడర్ మరియు ఫుటర్ లేఅవుట్
HTML_HEADER = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SLNS Online & Insurance Services</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    
    <style>
        :root { --primary-gradient: linear-gradient(135deg, #0f2027, #203a43, #2c5364); }
        body { background: #f0f4f8; font-family: 'Segoe UI', sans-serif; color: #333; }
        .navbar { background: var(--primary-gradient) !important; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .navbar-brand { font-weight: 800; letter-spacing: 1px; }
        .rich-card { background: white; border-radius: 16px; border: none; box-shadow: 0 10px 30px rgba(0,0,0,0.05); transition: all 0.4s ease; overflow: hidden; }
        .rich-card:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.12); }
        .card-header-custom-pan { background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 15px 20px; font-weight: 600; }
        .card-header-custom-aadhar { background: linear-gradient(135deg, #11998e, #38ef7d); color: white; padding: 15px 20px; font-weight: 600; }
        .social-btn-tg { background: #229ED9; color: white !important; }
        .social-btn-wa { background: #25D366; color: white !important; }
        .status-badge-paid { background-color: #d1e7dd; color: #0f5132; padding: 5px 10px; border-radius: 30px; font-size: 13px; font-weight: 600; }
        .status-badge-pending { background-color: #fff3cd; color: #664d03; padding: 5px 10px; border-radius: 30px; font-size: 13px; font-weight: 600; }
        .status-badge-failed { background-color: #f8d7da; color: #842029; padding: 5px 10px; border-radius: 30px; font-size: 13px; font-weight: 600; }
        
        .whatsapp-bubble { position: fixed; bottom: 20px; right: 20px; background: linear-gradient(135deg, #11998e, #38ef7d); color: white; padding: 14px 22px; border-radius: 50px; box-shadow: 0 5px 20px rgba(37, 211, 102, 0.4); cursor: pointer; text-decoration: none !important; z-index: 1000; font-weight: bold; }
        .whatsapp-chat-box { position: fixed; bottom: 90px; right: 20px; width: 320px; background: white; border-radius: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); display: none; flex-direction: column; z-index: 1000; overflow: hidden; animation: fadeInUp 0.4s; }
        .chat-header { background: #075E54; color: white; padding: 12px; font-weight: bold; display: flex; align-items: center; justify-content: space-between;}
        .chat-body { padding: 15px; max-height: 220px; overflow-y: auto; background: #ece5dd; font-size: 14px; }
        .chat-input-area { display: flex; border-top: 1px solid #ccc; }
        .chat-input { flex-grow: 1; border: none; padding: 12px; outline: none; }
        .chat-btn { background: #075E54; color: white; border: none; padding: 0 15px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
      <div class="container">
        <a class="navbar-brand animate__animated animate__fadeInLeft" href="/">
            <i class="fa-solid fa-shield-halved text-info me-2"></i>SLNS ONLINE & INSURANCE SERVICES
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
            <div class="navbar-nav ms-auto align-items-center">
                <a class="btn social-btn-tg btn-sm mx-1 my-1" href="https://t.me/pancsc" target="_blank"><i class="fa-brands fa-telegram me-1"></i> Join Telegram</a>
                <a class="btn social-btn-wa btn-sm mx-1 my-1" href="https://whatsapp.com/channel/0029VbCut5E4o7qH8GUgjO0s" target="_blank"><i class="fa-brands fa-whatsapp me-1"></i> WhatsApp Channel</a>
                <a class="nav-link text-white font-weight-bold ms-3" href="/dashboard"><i class="fa-solid fa-sliders me-1"></i> Dashboard</a>
            </div>
        </div>
      </div>
    </nav>
    
    <div class="container my-5">
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for msg in messages %}
              <div class="alert alert-success alert-dismissible fade show animate__animated animate__bounceInDown shadow-sm" role="alert">
                <i class="fa-solid fa-circle-check me-2"></i>{{ msg }}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}
"""

HTML_FOOTER = """
    </div>
    
    <footer class="bg-dark text-white text-center py-4 mt-5 border-top border-secondary">
        <div class="container">
            <h5>Stay Connected With Us</h5>
            <div class="mb-3">
                <a href="https://t.me/pancsc" target="_blank" class="btn social-btn-tg mx-2"><i class="fa-brands fa-telegram fa-lg me-2"></i>Join Telegram Group</a>
                <a href="https://whatsapp.com/channel/0029VbCut5E4o7qH8GUgjO0s" target="_blank" class="btn social-btn-wa mx-2"><i class="fa-brands fa-whatsapp fa-lg me-2"></i>Follow WhatsApp Channel</a>
            </div>
            <p class="mb-0 small text-muted">&copy; 2026 SLNS Online Services. All Rights Reserved.</p>
        </div>
    </footer>

    <a href="#" class="whatsapp-bubble animate__animated animate__pulse animate__infinite" onclick="toggleChat(event)"><i class="fa-brands fa-whatsapp fa-xl me-2"></i>Live Help Chat</a>
    <div class="whatsapp-chat-box" id="chatBox">
        <div class="chat-header"><span><i class="fa-brands fa-whatsapp text-success me-2"></i>SLNS Auto-Support</span><i class="fa-solid fa-xmark" style="cursor:pointer;" onclick="toggleChat(event)"></i></div>
        <div class="chat-body" id="chatBody"><div class="p-2 my-1 bg-white rounded"><b>Bot:</b> Hello! Welcome to SLNS Online Services. Type "PAN" or "Address" for info!</div></div>
        <div class="chat-input-area"><input type="text" id="chatInput" class="chat-input" placeholder="Type a message..."><button class="chat-btn" onclick="sendWhatsAppMsg()"><i class="fa-solid fa-paper-plane"></i></button></div>
    </div>
    
    <script>
        function toggleChat(e) { if(e) e.preventDefault(); var box = document.getElementById('chatBox'); box.style.display = (box.style.display === 'flex') ? 'none' : 'flex'; }
        function sendWhatsAppMsg() {
            var input = document.getElementById('chatInput'); var body = document.getElementById('chatBody'); if(!input.value.trim()) return;
            body.innerHTML += "<div class='p-2 my-1 text-end bg-light rounded text-dark'><b>You:</b> " + input.value + "</div>";
            var text = input.value.toLowerCase(); input.value = "";
            setTimeout(function() {
                var reply = "Thank you for contacting SLNS Office. We received your request.";
                if(text.includes('pan')) { reply = "For PAN Application, ensure you submit full Father/Mother names with Surnames."; }
                else if (text.includes('address') || text.includes('update')) { reply = "For Address Updates, please provide Voter ID alongside address details."; }
                body.innerHTML += "<div class='p-2 my-1 bg-white rounded'><b>Bot:</b> " + reply + "</div>"; body.scrollTop = body.scrollHeight;
            }, 700);
        }
    </script>
</body>
</html>
"""

INDEX_CONTENT = """
<div class="row">
    <!-- 1. పాన్ కార్డ్ అప్లికేషన్ ఫామ్ -->
    <div class="col-md-6 animate__animated animate__fadeInLeft">
        <div class="card rich-card">
            <div class="card-header-custom-pan"><i class="fa-solid fa-id-card me-2"></i>1. PAN Card Service Application</div>
            <div class="card-body p-4">
                <form action="/submit_pan" method="POST" enctype="multipart/form-data">
                    <div class="mb-3"><label class="form-label font-weight-bold">A. Full Name of the Person</label><input type="text" name="name" class="form-control" required placeholder="Enter full name"></div>
                    <div class="alert alert-warning py-2 font-monospace" style="font-size:12px; border-left: 4px solid #ffc107;"><i class="fa-solid fa-triangle-exclamation me-1"></i>Note: For Married Women also only Father and Mother Name Have to be entered.</div>
                    <div class="mb-3"><label class="form-label">B. Father's Name (Including Surname)</label><input type="text" name="father_name" class="form-control" required></div>
                    <div class="mb-3"><label class="form-label">C. Mother's Name (Including Surname)</label><input type="text" name="mother_name" class="form-control" required></div>
                    <div class="mb-3"><label class="form-label">D. Aadhaar Card Number</label><input type="text" name="aadhar" class="form-control" maxlength="12" pattern="\\d{12}" placeholder="12 digit number" required></div>
                    <div class="mb-3"><label class="form-label">E. Date of Birth</label><input type="date" name="dob" class="form-control" required></div>
                    <div class="mb-3"><label class="form-label">F. Aadhaar Linked Mobile Number</label><input type="tel" name="mobile" class="form-control" required></div>
                    <div class="mb-2"><label class="small font-weight-bold">Upload Aadhaar Document:</label> <input type="file" name="f_aadhar" class="form-control form-control-sm" required></div>
                    <div class="mb-2"><label class="small font-weight-bold">Upload Passport Photo:</label> <input type="file" name="f_photo" class="form-control form-control-sm" required></div>
                    <div class="mb-3"><label class="small font-weight-bold">Upload Signature:</label> <input type="file" name="f_sig" class="form-control form-control-sm" required></div>
                    <button type="submit" class="btn btn-primary w-100 btn-lg shadow-sm">Submit PAN Application (₹399)</button>
                </form>
            </div>
        </div>
    </div>

    <!-- 2. ఆధార్ అడ్రస్ అప్డేట్ ఫామ్ -->
    <div class="col-md-6 animate__animated animate__fadeInRight">
        <div class="card rich-card">
            <div class="card-header-custom-aadhar"><i class="fa-solid fa-house-chimney-user me-2"></i>2. Aadhaar Address Update</div>
            <div class="card-body p-4">
                <form action="/submit_address" method="POST" enctype="multipart/form-data">
                    <div class="mb-3"><label class="form-label">A. Voter ID Number</label><input type="text" name="voter_id" class="form-control" required placeholder="Enter Voter Card Number"></div>
                    <div class="mb-3"><label class="form-label">B. Aadhaar Card Number</label><input type="text" name="aadhar" class="form-control" maxlength="12" pattern="\\d{12}" placeholder="12 digit number" required></div>
                    <div class="mb-3"><label class="form-label">C. Aadhaar Linked Mobile Number</label><input type="tel" name="mobile" class="form-control" required></div>
                    <div class="mb-3"><label class="form-label">Write Complete Address (Max 1500 words)</label><textarea name="new_address" class="form-control" rows="4" maxlength="9000" placeholder="Type detailed layout address..." required></textarea></div>
                    <div class="row mb-3">
                        <div class="col"><label class="small font-weight-bold">Upload Photo:</label><input type="file" name="f_photo" class="form-control form-control-sm" required></div>
                        <div class="col"><label class="small font-weight-bold">Upload Aadhaar:</label><input type="file" name="f_aadhar" class="form-control form-control-sm" required></div>
                    </div>
                    <button type="submit" class="btn btn-success w-100 btn-lg shadow-sm text-white">Submit Address Update (₹399)</button>
                </form>
            </div>
        </div>

        <!-- 5. కస్టమర్ ఫీడ్‌బ్యాక్ ఫామ్ -->
        <div class="card rich-card mt-4 animate__animated animate__fadeInUp animate__delay-1s">
            <div class="card-body p-4">
                <h4 class="text-secondary mb-3"><i class="fa-solid fa-comments me-2"></i>5. Customer Feedback Form</h4>
                <form action="/submit_feedback" method="POST">
                    <div class="mb-2"><input type="text" name="c_name" class="form-control form-control-sm" placeholder="Your Name" required></div>
                    <div class="mb-2">
                        <label class="small me-2">1 To 5 Star Rating:</label>
                        {% for i in range(1, 6) %}
                        <div class="form-check form-check-inline"><input class="form-check-input" type="radio" name="rating" id="r{{i}}" value="{{i}}" required><label class="form-check-label" for="r{{i}}">{{i}}★</label></div>
                        {% endfor %}
                    </div>
                    <div class="mb-2"><textarea name="comments" class="form-control form-control-sm" rows="2" maxlength="3000" placeholder="Your comments..." required></textarea></div>
                    <button type="submit" class="btn btn-secondary btn-sm w-100">Submit Rating</button>
                </form>
            </div>
        </div>
    </div>
</div>
"""

DASHBOARD_CONTENT = """
<div class="animate__animated animate__fadeIn">
    <h2 class="mb-4">⚙️ Centralized Customer Database Dashboard</h2>
    <hr>
    <h3 class="text-primary mb-3">PAN Card Submission Database Entries</h3>
    <div class="table-responsive shadow-sm rounded mb-5">
        <table class="table table-striped table-bordered bg-white mb-0">
            <thead class="table-dark">
                <tr><th>ID</th><th>Name</th><th>Aadhaar (Masked)</th><th>Mobile</th><th>Status</th><th>UTR ID / Transaction No</th><th>Timestamp</th></tr>
            </thead>
            <tbody>
                {% for item in pans %}
                <tr>
                    <td>{{item.id}}</td>
                    <td>{{item.name}}</td>
                    <td><code>{{item.aadhar_masked}}</code></td>
                    <td>{{item.mobile}}</td>
                    <td>
                        {% if item.payment_status == 'Paid' %}
                            <span class="status-badge-paid"><i class="fa-solid fa-circle-check me-1"></i>Paid</span>
                        {% elif item.payment_status == 'Failed' %}
                            <span class="status-badge-failed"><i class="fa-solid fa-circle-xmark me-1"></i>Failed</span>
                        {% else %}
                            <span class="status-badge-pending"><i class="fa-solid fa-clock me-1"></i>Not Paid</span>
                        {% endif %}
                    </td>
                    <td><span class="badge bg-secondary font-monospace">{{item.utr_number}}</span></td>
                    <td>{{item.timestamp.strftime('%Y-%m-%d %H:%M')}}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <h3 class="text-success mb-3 mt-4">Aadhaar Address Update Database Entries</h3>
    <div class="table-responsive shadow-sm rounded mb-5">
        <table class="table table-striped table-bordered bg-white mb-0">
            <thead class="table-dark">
                <tr><th>ID</th><th>Voter ID</th><th>Aadhaar (Masked)</th><th>Mobile</th><th>Status</th><th>UTR ID / Transaction No</th><th>Timestamp</th></tr>
            </thead>
            <tbody>
                {% for item in addresses %}
                <tr>
                    <td>{{item.id}}</td>
                    <td>{{item.voter_id}}</td>
                    <td><code>{{item.aadhar_masked}}</code></td>
                    <td>{{item.mobile}}</td>
                    <td>
                        {% if item.payment_status == 'Paid' %}
                            <span class="status-badge-paid"><i class="fa-solid fa-circle-check me-1"></i>Paid</span>
                        {% elif item.payment_status == 'Failed' %}
                            <span class="status-badge-failed"><i class="fa-solid fa-circle-xmark me-1"></i>Failed</span>
                        {% else %}
                            <span class="status-badge-pending"><i class="fa-solid fa-clock me-1"></i>Not Paid</span>
                        {% endif %}
                    </td>
                    <td><span class="badge bg-secondary font-monospace">{{item.utr_number}}</span></td>
                    <td>{{item.timestamp.strftime('%Y-%m-%d %H:%M')}}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    <a href="/" class="btn btn-outline-dark mt-4">← Return to Application Portals</a>
</div>
"""

UPI_PAYMENT_CONTENT = """
<div class="container text-center animate__animated animate__zoomIn">
    <div class="card p-4 mx-auto bg-white shadow-lg" style="max-width: 440px; border-radius: 20px; border: none;">
        <div class="py-2 text-white rounded-top" style="background: linear-gradient(135deg, #1e3c72, #2a5298); margin: -25px -25px 20px -25px;">
            <h5 class="mb-0 py-2">SECURE UPI PAYMENT</h5>
        </div>
        <h5 class="text-primary mb-1">SLNS ONLINE SERVICES</h5>
        <h6 class="text-secondary mb-3">{{ service }}</h6>
        <p class="text-muted small">Scan QR Code using PhonePe, Google Pay, or Paytm App</p>
        
        <div class="my-2">
            <img src="{{ qr_url }}" alt="UPI QR Code" class="img-fluid border p-3 bg-white rounded shadow-sm" style="width: 240px; height: 240px;">
        </div>
        
        <h2 class="text-success my-2 font-weight-bold">₹{{ amount }}</h2>
        
        <div class="alert alert-light border py-2 small font-monospace">
            <i class="fa-solid fa-building-columns me-2 text-primary"></i>UPI ID: sweetnani873@ybl
        </div>
        
        <!-- UTR / TRANSACTION ID INPUT FORM -->
        <form action="/confirm_payment" method="POST" class="mt-3 text-start">
            <input type="hidden" name="record_id" value="{{ record_id }}">
            <input type="hidden" name="service_type" value="{{ service_type }}">
            
            <div class="mb-3">
                <label class="form-label small text-dark font-weight-bold">Enter UPI UTR / Transaction ID (12 Digits):</label>
                <input type="text" name="utr_number" class="form-control form-control-sm font-monospace" placeholder="e.g. 623456789012" required maxlength="20">
            </div>
            
            <div class="row g-2">
                <div class="col-6">
                    <button type="submit" name="status" value="Paid" class="btn btn-success w-100"><i class="fa-solid fa-check me-1"></i>I Have Paid</button>
                </div>
                <div class="col-6">
                    <button type="submit" name="status" value="Failed" class="btn btn-danger w-100"><i class="fa-solid fa-xmark me-1"></i>Payment Failed</button>
                </div>
            </div>
        </form>
    </div>
</div>
"""

# 4. ఫ్లాస్క్ రౌటింగ్ లాజిక్
@app.route('/')
def index():
    full_html = HTML_HEADER + INDEX_CONTENT + HTML_FOOTER
    return render_template_string(full_html)

@app.route('/submit_pan', methods=['POST'])
def submit_pan():
    new_pan = PanApplication(
        name=request.form.get('name').upper(),
        father_name=request.form.get('father_name').upper(),
        mother_name=request.form.get('mother_name').upper(),
        aadhar_masked=mask_aadhar(request.form.get('aadhar')),
        dob=request.form.get('dob'),
        mobile=request.form.get('mobile')
    )
    db.session.add(new_pan)
    db.session.commit()
    return redirect(url_for('upi_payment', amount="399.00", service="New PAN Card Application", record_id=new_pan.id, service_type="pan"))

@app.route('/submit_address', methods=['POST'])
def submit_address():
    new_addr = AddressUpdateApplication(
        voter_id=request.form.get('voter_id').upper(),
        aadhar_masked=mask_aadhar(request.form.get('aadhar')),
        mobile=request.form.get('mobile'),
        new_address=request.form.get('new_address')
    )
    db.session.add(new_addr)
    db.session.commit()
    return redirect(url_for('upi_payment', amount="399.00", service="Aadhaar Address Update Service", record_id=new_addr.id, service_type="address"))

@app.route('/upi_payment')
def upi_payment():
    amount = request.args.get('amount', '399.00')
    service = request.args.get('service', 'SLNS Smart Service')
    record_id = request.args.get('record_id')
    service_type = request.args.get('service_type')
    
    upi_id = "sweetnani873@ybl"
    business_name = "SLNS Online Services"
    
    upi_url = f"upi://pay?pa={upi_id}&pn={business_name}&am={amount}&cu=INR"
    encoded_upi_url = urllib.parse.quote(upi_url)
    qr_image_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_upi_url}"
    
    full_html = HTML_HEADER + UPI_PAYMENT_CONTENT + HTML_FOOTER
    return render_template_string(full_html, qr_url=qr_image_url, amount=amount, service=service, record_id=record_id, service_type=service_type)

# UTR నంబర్ మరియు సక్సెస్/ఫెయిల్యూర్ స్టేటస్ కన్ఫర్మేషన్ రూట్
@app.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    record_id = request.form.get('record_id')
    service_type = request.form.get('service_type')
    status = request.form.get('status') # Paid / Failed
    utr_number = request.form.get('utr_number')
    
    if service_type == "pan":
        record = PanApplication.query.get(record_id)
    else:
        record = AddressUpdateApplication.query.get(record_id)
        
    if record:
        record.payment_status = status
        record.utr_number = utr_number
        db.session.commit()
        flash(f"Payment status updated to '{status}' with UTR: {utr_number}")
        
    return redirect(url_for('dashboard'))

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    new_fb = CustomerFeedback(customer_name=request.form.get('c_name'), rating=int(request.form.get('rating')), comments=request.form.get('comments'))
    db.session.add(new_fb)
    db.session.commit()
    flash("Thank you for your valuable feedback rating!")
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    pans = PanApplication.query.order_by(PanApplication.timestamp.desc()).all()
    addresses = AddressUpdateApplication.query.order_by(AddressUpdateApplication.timestamp.desc()).all()
    full_html = HTML_HEADER + DASHBOARD_CONTENT + HTML_FOOTER
    return render_template_string(full_html, pans=pans, addresses=addresses)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
