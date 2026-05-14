import streamlit as st
from supabase import create_client
from datetime import datetime

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Contract Review — Carob Technologies",
    page_icon="📋",
    layout="centered"
)

# Hide sidebar and multipage navigation completely
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
header[data-testid="stHeader"]   { display: none !important; }
#MainMenu                        { display: none !important; }
footer                           { display: none !important; }

.review-header {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    text-align: center;
}
.review-header h1 { color: #ffffff; margin: 0; font-size: 1.5rem; font-family: 'DM Serif Display', serif; }
.review-header p  { color: #a8d8ea; margin: 6px 0 0; font-size: 0.85rem; }

.info-table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0 24px;
    font-size: 0.9rem;
}
.info-table td {
    padding: 10px 14px;
    border: 1px solid #ddd;
}
.info-table tr:nth-child(odd) td { background: #f0f4f8; }
.info-table td:first-child { font-weight: 600; width: 40%; color: #2c5364; }

.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.1rem;
    color: #2c5364;
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 0.4rem;
    margin: 1.2rem 0 0.8rem;
}

.error-box {
    background: #fff5f5;
    border-left: 4px solid #dc3545;
    padding: 1rem 1.2rem;
    border-radius: 0 8px 8px 0;
    color: #721c24;
    margin: 1rem 0;
}

.success-box {
    background: #d4edda;
    border-left: 4px solid #28a745;
    padding: 1rem 1.2rem;
    border-radius: 0 8px 8px 0;
    color: #155724;
    margin: 1rem 0;
    text-align: center;
    font-size: 1rem;
}

.footer-note {
    font-size: 0.78rem;
    color: #aaa;
    text-align: center;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #eee;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SUPABASE
# ─────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

supabase = get_supabase()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fill_template(template_body, customer, equipment, contract):
    placeholders = {
        "{{company_name}}":      "Carob Technologies",
        "{{customer_name}}":     customer.get("customer_name", ""),
        "{{contact_person}}":    customer.get("contact_person", ""),
        "{{customer_address}}":  customer.get("address", ""),
        "{{customer_city}}":     customer.get("city", ""),
        "{{customer_pincode}}":  customer.get("pincode", ""),
        "{{equipment_type}}":    equipment.get("equipment_type", ""),
        "{{equipment_make}}":    equipment.get("make", ""),
        "{{equipment_model}}":   equipment.get("model", ""),
        "{{serial_number}}":     equipment.get("serial_number", "N/A"),
        "{{number_of_units}}":   str(equipment.get("number_of_units", "")),
        "{{site_location}}":     equipment.get("site_location", ""),
        "{{installation_date}}": str(equipment.get("installation_date", "")),
        "{{start_date}}":        str(contract.get("start_date", "")),
        "{{end_date}}":          str(contract.get("end_date", "")),
        "{{contract_value}}":    f"{float(contract.get('contract_value', 0)):,.2f}",
        "{{payment_terms}}":     str(contract.get("payment_terms", "")),
        "{{signed_date}}":       "_______________",
    }
    body = template_body
    for k, v in placeholders.items():
        body = body.replace(k, str(v))
    return body

def log_action(contract_id, version, action, action_by="Customer", notes=""):
    supabase.table("contract_audit_log").insert({
        "contract_id": contract_id,
        "version":     version,
        "action":      action,
        "action_by":   action_by,
        "notes":       notes
    }).execute()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="review-header">
    <h1>📋 Contract Review & Signature</h1>
    <p>Carob Technologies — AMC Division</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# READ QUERY PARAMS
# ─────────────────────────────────────────────
try:
    params      = st.query_params
    contract_id = params.get("contract", None)
    version     = int(params.get("version", 1))
except Exception:
    contract_id = None
    version     = None

# ─────────────────────────────────────────────
# INVALID LINK
# ─────────────────────────────────────────────
if not contract_id:
    st.markdown("""<div class='error-box'>
        <strong>Invalid or expired link.</strong><br>
        Please use the link provided in your email. If you believe this is an error,
        contact Carob Technologies.
    </div>""", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────
# LOAD CONTRACT
# ─────────────────────────────────────────────
res = supabase.table("contracts").select("*")\
    .eq("contract_id", contract_id)\
    .eq("version", version)\
    .execute()

if not res.data:
    st.markdown("""<div class='error-box'>
        <strong>Contract not found.</strong><br>
        This contract may have been removed or the link is incorrect.
        Please contact Carob Technologies.
    </div>""", unsafe_allow_html=True)
    st.stop()

contract = res.data[0]

# ─────────────────────────────────────────────
# ALREADY ACTIONED
# ─────────────────────────────────────────────
if contract["status"] == "Signed":
    st.markdown(f"""<div class='success-box'>
        ✅ <strong>This contract has already been signed.</strong><br>
        Contract ID: {contract_id} — Version {version}<br>
        Signed on: {str(contract.get('signed_at', ''))[:10]}
    </div>""", unsafe_allow_html=True)
    st.stop()

if contract["status"] == "Declined":
    st.markdown(f"""<div class='error-box'>
        This contract was previously declined.<br>
        A revised version will be sent to you shortly.
    </div>""", unsafe_allow_html=True)
    st.stop()

if contract["status"] != "Pending":
    st.markdown("""<div class='error-box'>
        This contract is not currently available for review.
        Please contact Carob Technologies.
    </div>""", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────
# LOAD RELATED DATA
# ─────────────────────────────────────────────
cust_res = supabase.table("customers").select("*")\
    .eq("customer_id", contract["customer_id"]).execute()
customer = cust_res.data[0] if cust_res.data else {}

eq_res = supabase.table("equipment").select("*")\
    .eq("equipment_id", contract["equipment_id"]).execute()
equip = eq_res.data[0] if eq_res.data else {}

tmpl_res = supabase.table("contract_templates").select("*")\
    .eq("template_id", contract["template_id"]).execute()
template = tmpl_res.data[0] if tmpl_res.data else {}

# ─────────────────────────────────────────────
# CONTRACT SUMMARY
# ─────────────────────────────────────────────
st.markdown(f"Dear **{customer.get('contact_person', 'Sir/Madam')}**,")
st.markdown(
    f"Please review your **{contract['contract_tier']} AMC Contract** "
    f"for **{contract['equipment_type']}** equipment and submit your decision below."
)

st.markdown(f"""
<table class="info-table">
    <tr><td>Contract ID</td><td>{contract_id} — Version {version}</td></tr>
    <tr><td>Equipment Type</td><td>{contract['equipment_type']}</td></tr>
    <tr><td>Contract Tier</td><td>{contract['contract_tier']}</td></tr>
    <tr><td>Equipment</td><td>{equip.get('make','')} {equip.get('model','')} — {equip.get('site_location','')}</td></tr>
    <tr><td>Number of Units</td><td>{equip.get('number_of_units','')}</td></tr>
    <tr><td>Contract Value</td><td>Rs {float(contract['contract_value']):,.2f} per annum</td></tr>
    <tr><td>Contract Period</td><td>{contract['start_date']} to {contract['end_date']}</td></tr>
    <tr><td>Payment Terms</td><td>{contract['payment_terms']}</td></tr>
</table>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONTRACT DOCUMENT
# ─────────────────────────────────────────────
st.markdown("<div class='section-title'>Contract Document</div>", unsafe_allow_html=True)

if template:
    filled = fill_template(template.get("template_body", ""), customer, equip, contract)
    st.code(filled, language=None)
else:
    st.warning("Contract document could not be loaded.")

# ─────────────────────────────────────────────
# DECISION
# ─────────────────────────────────────────────
st.markdown("<div class='section-title'>Your Decision</div>", unsafe_allow_html=True)
st.markdown("Please review the contract above carefully before submitting your decision.")

# Check session state to prevent re-submission
if "decision_submitted" not in st.session_state:
    st.session_state["decision_submitted"] = False

if st.session_state["decision_submitted"]:
    st.success("Your response has been submitted. Carob Technologies will be in touch shortly.")
    st.stop()

action = st.radio(
    "Select your decision",
    ["Approve and Sign", "Decline with Comments"],
    index=0
)

comments = ""
if "Decline" in action:
    comments = st.text_area(
        "Please provide your comments or revision requests",
        placeholder="e.g. Please revise the contract value. Change payment terms to half-yearly.",
        height=120
    )

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("Submit My Decision", type="primary", use_container_width=True):
        if "Decline" in action and not comments.strip():
            st.error("Please enter your comments before declining.")
        else:
            if "Approve" in action:
                supabase.table("contracts").update({
                    "status":    "Signed",
                    "signed_at": datetime.now().isoformat()
                }).eq("contract_id", contract_id).eq("version", version).execute()
                log_action(contract_id, version, "Signed", customer.get("contact_person", "Customer"),
                    f"Signed via email link by {customer.get('contact_person','')}")
                st.session_state["decision_submitted"] = True
                st.success(f"Thank you! Contract {contract_id} has been signed successfully.")
                st.balloons()
                st.rerun()
            else:
                supabase.table("contracts").update({
                    "status":            "Declined",
                    "customer_comments": comments
                }).eq("contract_id", contract_id).eq("version", version).execute()
                log_action(contract_id, version, "Declined", customer.get("contact_person", "Customer"),
                    comments)

                # Send notification email to internal team
                try:
                    import smtplib
                    from email.mime.multipart import MIMEMultipart
                    from email.mime.text import MIMEText

                    cfg         = st.secrets["email"]
                    smtp_host   = cfg["smtp_host"]
                    smtp_port   = int(cfg["smtp_port"])
                    smtp_user   = cfg["smtp_user"]
                    smtp_pass   = cfg["smtp_password"]
                    sender_name = cfg.get("sender_name", "Carob Technologies")

                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = f"Contract Declined — {contract_id} v{version} — {customer.get('customer_name','')}"
                    msg["From"]    = f"{sender_name} <{smtp_user}>"
                    msg["To"]      = smtp_user

                    plain = f"""Contract Declined Notification

Contract ID  : {contract_id} — Version {version}
Customer     : {customer.get('customer_name','')}
Contact      : {customer.get('contact_person','')} ({customer.get('email','')})
Equipment    : {contract.get('equipment_type','')} — {contract.get('contract_tier','')}
Declined At  : {datetime.now().strftime('%Y-%m-%d %H:%M')}

Customer Comments:
{comments}

Please revise and resend the contract from the Dashboard.
"""
                    html = f"""
<html><body style="font-family:Arial,sans-serif;color:#222;max-width:600px;margin:auto;">
<div style="background:#dc3545;padding:20px 28px;border-radius:10px 10px 0 0;">
    <h2 style="color:#fff;margin:0;">Contract Declined</h2>
    <p style="color:#ffd0d0;margin:4px 0 0;">Action required — please revise and resend</p>
</div>
<div style="border:1px solid #ddd;border-top:none;border-radius:0 0 10px 10px;padding:24px 28px;">
    <table style="width:100%;border-collapse:collapse;font-size:0.9rem;margin-bottom:20px;">
        <tr style="background:#f8f9fa;"><td style="padding:10px;font-weight:600;border:1px solid #ddd;width:40%;">Contract ID</td><td style="padding:10px;border:1px solid #ddd;">{contract_id} — v{version}</td></tr>
        <tr><td style="padding:10px;font-weight:600;border:1px solid #ddd;">Customer</td><td style="padding:10px;border:1px solid #ddd;">{customer.get('customer_name','')}</td></tr>
        <tr style="background:#f8f9fa;"><td style="padding:10px;font-weight:600;border:1px solid #ddd;">Contact</td><td style="padding:10px;border:1px solid #ddd;">{customer.get('contact_person','')} ({customer.get('email','')})</td></tr>
        <tr><td style="padding:10px;font-weight:600;border:1px solid #ddd;">Equipment</td><td style="padding:10px;border:1px solid #ddd;">{contract.get('equipment_type','')} — {contract.get('contract_tier','')}</td></tr>
        <tr style="background:#f8f9fa;"><td style="padding:10px;font-weight:600;border:1px solid #ddd;">Declined At</td><td style="padding:10px;border:1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M')}</td></tr>
    </table>
    <h3 style="color:#dc3545;">Customer Comments:</h3>
    <div style="background:#fff5f5;border-left:4px solid #dc3545;padding:14px;border-radius:0 6px 6px 0;font-size:0.95rem;">
        {comments}
    </div>
    <p style="margin-top:20px;font-size:0.88rem;color:#555;">
        Please log in to the Service Contract Manager, revise the contract, and resend.
    </p>
</div>
</body></html>
"""
                    msg.attach(MIMEText(plain, "plain"))
                    msg.attach(MIMEText(html,  "html"))

                    with smtplib.SMTP(smtp_host, smtp_port) as server:
                        server.ehlo()
                        server.starttls()
                        server.login(smtp_user, smtp_pass)
                        server.sendmail(smtp_user, smtp_user, msg.as_string())

                except Exception:
                    pass  # Don't block the decline flow if email fails

                st.session_state["decision_submitted"] = True
                st.warning("Your decline has been recorded. Carob Technologies will send a revised contract shortly.")
                st.rerun()

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<div class='footer-note'>
    This is a secure contract review portal by Carob Technologies.<br>
    If you did not request this contract or have concerns, please contact us immediately.
</div>
""", unsafe_allow_html=True)
