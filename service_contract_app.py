import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date, datetime
import re
import smtplib
import base64
import time
import requests
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Service Contract Manager",
    page_icon="📋",
    layout="wide"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'DM Serif Display', serif; }

.app-header {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.app-header h1 { color: #ffffff; margin: 0; font-size: 1.6rem; letter-spacing: 0.5px; }
.app-header span { color: #a8d8ea; font-size: 0.85rem; }

.badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.5px; }
.badge-draft     { background: #e8e8e8; color: #555; }
.badge-pending   { background: #fff3cd; color: #856404; }
.badge-signed    { background: #d4edda; color: #155724; }
.badge-declined  { background: #f8d7da; color: #721c24; }
.badge-cancelled { background: #e2e3e5; color: #383d41; }

.tier-platinum { background: #e8e0f7; color: #4a1e8a; border-radius: 6px; padding: 2px 8px; font-size: 0.8rem; font-weight: 600; }
.tier-gold     { background: #fff4d6; color: #92650a; border-radius: 6px; padding: 2px 8px; font-size: 0.8rem; font-weight: 600; }
.tier-silver   { background: #eaeaea; color: #444;    border-radius: 6px; padding: 2px 8px; font-size: 0.8rem; font-weight: 600; }

.section-title { font-family: 'DM Serif Display', serif; font-size: 1.2rem; color: #2c5364; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.4rem; margin-bottom: 1rem; }

.info-box { background: #eef6fb; border-left: 4px solid #2c5364; padding: 0.8rem 1rem; border-radius: 0 8px 8px 0; margin-bottom: 1rem; font-size: 0.88rem; color: #2c5364; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SUPABASE CONNECTION
# ─────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = get_supabase()

# ─────────────────────────────────────────────
# EMAIL FUNCTION
# ─────────────────────────────────────────────
def send_contract_email(customer, contract, contract_body):
    try:
        cfg         = st.secrets["email"]
        smtp_host   = cfg["smtp_host"]
        smtp_port   = int(cfg["smtp_port"])
        smtp_user   = cfg["smtp_user"]
        smtp_pass   = cfg["smtp_password"]
        sender_name = cfg.get("sender_name", "Carob Technologies")
        app_url     = cfg.get("app_url", "").rstrip("/")

        review_link = f"{app_url}/review?contract={contract['contract_id']}&version={contract['version']}"

        html = f"""
        <html><body style="font-family:Arial,sans-serif;color:#222;max-width:700px;margin:auto;">

        <div style="background:linear-gradient(135deg,#0f2027,#2c5364);padding:24px 32px;border-radius:10px 10px 0 0;">
            <h2 style="color:#fff;margin:0;">Service Contract for Review &amp; Signature</h2>
            <p style="color:#a8d8ea;margin:6px 0 0;">Carob Technologies — AMC Division</p>
        </div>

        <div style="border:1px solid #ddd;border-top:none;border-radius:0 0 10px 10px;padding:28px 32px;">
            <p>Dear <strong>{customer['contact_person']}</strong>,</p>
            <p>Please find your <strong>{contract['contract_tier']} AMC Contract</strong>
               for <strong>{contract['equipment_type']}</strong> equipment below.
               Kindly review and click Approve or Decline at the bottom.</p>

            <table style="width:100%;border-collapse:collapse;margin:20px 0;font-size:0.9rem;">
                <tr style="background:#f0f4f8;">
                    <td style="padding:10px 14px;font-weight:600;border:1px solid #ddd;width:35%;">Contract ID</td>
                    <td style="padding:10px 14px;border:1px solid #ddd;">{contract['contract_id']} — Version {contract['version']}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;font-weight:600;border:1px solid #ddd;">Equipment Type</td>
                    <td style="padding:10px 14px;border:1px solid #ddd;">{contract['equipment_type']}</td>
                </tr>
                <tr style="background:#f0f4f8;">
                    <td style="padding:10px 14px;font-weight:600;border:1px solid #ddd;">Contract Tier</td>
                    <td style="padding:10px 14px;border:1px solid #ddd;">{contract['contract_tier']}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;font-weight:600;border:1px solid #ddd;">Contract Value</td>
                    <td style="padding:10px 14px;border:1px solid #ddd;">Rs {float(contract['contract_value']):,.2f} per annum</td>
                </tr>
                <tr style="background:#f0f4f8;">
                    <td style="padding:10px 14px;font-weight:600;border:1px solid #ddd;">Contract Period</td>
                    <td style="padding:10px 14px;border:1px solid #ddd;">{contract['start_date']} to {contract['end_date']}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;font-weight:600;border:1px solid #ddd;">Payment Terms</td>
                    <td style="padding:10px 14px;border:1px solid #ddd;">{contract['payment_terms']}</td>
                </tr>
            </table>

            <h3 style="color:#2c5364;border-bottom:2px solid #e5e7eb;padding-bottom:8px;">Contract Document</h3>
            <div style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:6px;padding:20px;
                        font-family:'Courier New',monospace;font-size:0.82rem;line-height:1.8;
                        white-space:pre-wrap;color:#1a1a1a;">
{contract_body}
            </div>

            <div style="text-align:center;margin:32px 0 16px;">
                <a href="{review_link}&action=approve"
                   style="background:#28a745;color:#fff;padding:14px 32px;border-radius:6px;
                          text-decoration:none;font-weight:700;font-size:1rem;margin-right:16px;">
                   Approve &amp; Sign
                </a>
                <a href="{review_link}&action=decline"
                   style="background:#dc3545;color:#fff;padding:14px 32px;border-radius:6px;
                          text-decoration:none;font-weight:700;font-size:1rem;">
                   Decline with Comments
                </a>
            </div>

            <p style="font-size:0.82rem;color:#888;text-align:center;">
                Clicking a button above opens the review portal to confirm your decision.<br>
                For queries, contact us at {smtp_user}.
            </p>

            <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
            <p style="font-size:0.8rem;color:#aaa;text-align:center;">
                This is an automated email from Carob Technologies Service Contract Manager.
            </p>
        </div>
        </body></html>
        """

        plain = f"""Dear {customer['contact_person']},

Please review your {contract['contract_tier']} AMC Contract for {contract['equipment_type']}.

Contract ID   : {contract['contract_id']} v{contract['version']}
Contract Value: Rs {float(contract['contract_value']):,.2f} per annum
Period        : {contract['start_date']} to {contract['end_date']}
Payment Terms : {contract['payment_terms']}

CONTRACT DOCUMENT:
{contract_body}

To review and sign, visit:
{review_link}

Regards,
Carob Technologies
"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"AMC Contract for Review — {contract['contract_id']} ({contract['contract_tier']} {contract['equipment_type']})"
        msg["From"]    = f"{sender_name} <{smtp_user}>"
        msg["To"]      = customer["email"]

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html,  "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, customer["email"], msg.as_string())

        return True, None

    except Exception as e:
        return False, str(e)

# ─────────────────────────────────────────────
# DOCUSIGN INTEGRATION
# ─────────────────────────────────────────────
def get_docusign_token():
    """Get JWT access token from DocuSign using cryptography library directly"""
    import json
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
    from cryptography.hazmat.backends import default_backend

    cfg             = st.secrets["docusign"]
    integration_key = cfg["integration_key"]
    user_id         = cfg["user_id"]
    private_key_str = cfg["private_key"]

    now = int(time.time())

    # Build JWT header and payload
    header  = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss":   integration_key,
        "sub":   user_id,
        "aud":   "account-d.docusign.com",
        "iat":   now,
        "exp":   now + 3600,
        "scope": "signature impersonation"
    }

    def b64url(data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    header_b64      = b64url(json.dumps(header,  separators=(",", ":")))
    payload_b64     = b64url(json.dumps(payload, separators=(",", ":")))
    signing_input   = f"{header_b64}.{payload_b64}".encode("utf-8")

    # Load RSA private key and sign
    private_key_obj = serialization.load_pem_private_key(
        private_key_str.encode("utf-8"),
        password=None,
        backend=default_backend()
    )
    signature     = private_key_obj.sign(signing_input, asym_padding.PKCS1v15(), hashes.SHA256())
    signature_b64 = b64url(signature)

    jwt_token = f"{header_b64}.{payload_b64}.{signature_b64}"

    resp = requests.post(
        "https://account-d.docusign.com/oauth/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion":  jwt_token
        }
    )
    if not resp.ok:
        raise Exception(f"Token error {resp.status_code}: {resp.text}")
    return resp.json()["access_token"]


def send_to_docusign(customer, contract, contract_body):
    """Create and send envelope via DocuSign REST API"""
    try:
        cfg        = st.secrets["docusign"]
        account_id = cfg["account_id"]
        base_uri   = cfg["base_uri"].rstrip("/")

        # Get access token
        access_token = get_docusign_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type":  "application/json"
        }

        # Convert contract text to base64 PDF-like document
        # DocuSign accepts plain text as a .txt document
        doc_bytes   = contract_body.encode("utf-8")
        doc_base64  = base64.b64encode(doc_bytes).decode("utf-8")

        doc_name    = f"{contract['contract_id']}_v{contract['version']}_{contract['contract_tier']}_{contract['equipment_type']}.txt"
        subject     = f"AMC Contract for Signature — {contract['contract_id']} ({contract['contract_tier']} {contract['equipment_type']})"

        envelope_payload = {
            "emailSubject": subject,
            "emailBlurb":   f"Dear {customer['contact_person']}, please review and sign your {contract['contract_tier']} AMC contract for {contract['equipment_type']} equipment.",
            "documents": [
                {
                    "documentBase64": doc_base64,
                    "name":           doc_name,
                    "fileExtension":  "txt",
                    "documentId":     "1"
                }
            ],
            "recipients": {
                "signers": [
                    {
                        "email":        customer["email"],
                        "name":         customer["contact_person"],
                        "recipientId":  "1",
                        "routingOrder": "1",
                        "tabs": {
                            "signHereTabs": [
                                {
                                    "documentId":  "1",
                                    "pageNumber":  "1",
                                    "recipientId": "1",
                                    "tabLabel":    "Signature",
                                    "xPosition":   "100",
                                    "yPosition":   "700"
                                }
                            ],
                            "dateSignedTabs": [
                                {
                                    "documentId":  "1",
                                    "pageNumber":  "1",
                                    "recipientId": "1",
                                    "tabLabel":    "Date Signed",
                                    "xPosition":   "300",
                                    "yPosition":   "700"
                                }
                            ]
                        }
                    }
                ]
            },
            "status": "sent"
        }

        url  = f"{base_uri}/restapi/v2.1/accounts/{account_id}/envelopes"
        resp = requests.post(url, json=envelope_payload, headers=headers)
        resp.raise_for_status()

        envelope_id = resp.json().get("envelopeId")
        return True, envelope_id

    except Exception as e:
        return False, str(e)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def generate_contract_id():
    year = date.today().year
    res  = supabase.table("contracts").select("contract_id").execute()
    existing = [r["contract_id"] for r in res.data] if res.data else []
    nums = []
    for cid in existing:
        m = re.search(r"C-\d{4}-(\d+)", cid)
        if m:
            nums.append(int(m.group(1)))
    next_num = (max(nums) + 1) if nums else 1
    return f"C-{year}-{next_num:03d}"

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

def log_action(contract_id, version, action, action_by="Internal", notes=""):
    supabase.table("contract_audit_log").insert({
        "contract_id": contract_id,
        "version":     version,
        "action":      action,
        "action_by":   action_by,
        "notes":       notes
    }).execute()

def badge_html(status):
    return f'<span class="badge badge-{status.lower()}">{status.upper()}</span>'

def tier_html(tier):
    return f'<span class="tier-{tier.lower()}">{tier}</span>'

# ─────────────────────────────────────────────
# DATA LOADERS
# ─────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_customers():
    res = supabase.table("customers").select("*").order("customer_name").execute()
    return res.data or []

@st.cache_data(ttl=30)
def load_equipment(customer_id=None):
    q = supabase.table("equipment").select("*")
    if customer_id:
        q = q.eq("customer_id", customer_id)
    return q.execute().data or []

@st.cache_data(ttl=30)
def load_templates(equipment_type=None, tier=None):
    q = supabase.table("contract_templates").select("*")
    if equipment_type:
        q = q.eq("equipment_type", equipment_type)
    if tier:
        q = q.eq("contract_tier", tier)
    return q.execute().data or []

@st.cache_data(ttl=10)
def load_contracts():
    res = supabase.table("contracts_summary").select("*").order("contract_id", desc=True).execute()
    return res.data or []

@st.cache_data(ttl=10)
def load_audit(contract_id):
    res = supabase.table("contract_audit_log").select("*").eq("contract_id", contract_id).order("action_at").execute()
    return res.data or []

def load_contract_versions(contract_id):
    res = supabase.table("contracts").select("*").eq("contract_id", contract_id).order("version").execute()
    return res.data or []

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1>Service Contract Manager</h1>
    <span>Carob Technologies &nbsp;|&nbsp; Lift & Escalator AMC</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────
tabs = st.tabs(["Dashboard", "New Contract", "Customer Review", "Audit Trail", "Analytics"])

# ═══════════════════════════════════════════════════════════
# TAB 1: DASHBOARD
# ═══════════════════════════════════════════════════════════
with tabs[0]:
    contracts = load_contracts()

    total     = len(set(c["contract_id"] for c in contracts))
    pending   = sum(1 for c in contracts if c["status"] == "Pending")
    signed    = sum(1 for c in contracts if c["status"] == "Signed")
    declined  = sum(1 for c in contracts if c["status"] == "Declined")
    draft     = sum(1 for c in contracts if c["status"] == "Draft")
    cancelled = sum(1 for c in contracts if c["status"] == "Cancelled")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Contracts", total)
    c2.metric("Draft",     draft)
    c3.metric("Pending",   pending)
    c4.metric("Signed",    signed)
    c5.metric("Declined",  declined)
    c6.metric("Cancelled", cancelled)

    st.markdown("<div class='section-title'>All Contracts</div>", unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    with f1:
        status_filter = st.selectbox("Filter by Status", ["All", "Draft", "Pending", "Signed", "Declined", "Cancelled"])
    with f2:
        type_filter = st.selectbox("Equipment Type", ["All", "Lift", "Escalator"])
    with f3:
        tier_filter = st.selectbox("Contract Tier", ["All", "Platinum", "Gold", "Silver"])

    filtered = contracts
    if status_filter != "All":
        filtered = [c for c in filtered if c["status"] == status_filter]
    if type_filter != "All":
        filtered = [c for c in filtered if c["equipment_type"] == type_filter]
    if tier_filter != "All":
        filtered = [c for c in filtered if c["contract_tier"] == tier_filter]

    if not filtered:
        st.info("No contracts found. Create one from the New Contract tab.")
    else:
        for c in filtered:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 1.8, 1.2])
                with col1:
                    st.markdown(f"**{c['contract_id']}** &nbsp; v{c['version']}", unsafe_allow_html=True)
                    st.caption(f"{c['customer_name']} — {c['contact_person']}")
                with col2:
                    st.markdown(f"{c['equipment_type']} &nbsp; {tier_html(c['contract_tier'])}", unsafe_allow_html=True)
                    st.caption(str(c.get("equipment", "")))
                with col3:
                    st.markdown(f"Rs {float(c['contract_value']):,.0f}", unsafe_allow_html=True)
                    st.caption(f"{c['start_date']} to {c['end_date']}")
                with col4:
                    st.markdown(badge_html(c["status"]), unsafe_allow_html=True)
                    if c.get("signed_at"):
                        st.caption(f"Signed: {str(c['signed_at'])[:10]}")
                    elif c.get("sent_at"):
                        st.caption(f"Sent: {str(c['sent_at'])[:10]}")
                    # Show comments for Declined and Cancelled
                    if c["status"] in ["Declined", "Cancelled"] and c.get("customer_comments"):
                        comments = str(c.get("customer_comments", ""))
                        short    = comments[:80] + "..." if len(comments) > 80 else comments
                        st.caption("Note: " + short)
                with col5:
                    if c["status"] == "Draft":
                        if st.button("Send Email", key=f"send_{c['contract_id']}_{c['version']}"):
                            versions_data = load_contract_versions(c["contract_id"])
                            this_v  = next((v for v in versions_data if v["version"] == c["version"]), None)
                            custs   = load_customers()
                            cust    = next((cu for cu in custs if cu["customer_id"] == this_v["customer_id"]), {})
                            eq_list = load_equipment(this_v["customer_id"])
                            eq      = next((e for e in eq_list if e["equipment_id"] == this_v["equipment_id"]), {})
                            tmpls   = load_templates(this_v["equipment_type"], this_v["contract_tier"])
                            tmpl    = tmpls[0] if tmpls else {}

                            if tmpl and cust:
                                filled = fill_template(tmpl["template_body"], cust, eq, this_v)

                                with st.spinner("Sending via DocuSign..."):
                                    # Send via DocuSign
                                    ds_ok, ds_result = send_to_docusign(cust, this_v, filled)

                                if ds_ok:
                                    st.success(f"✅ Sent via DocuSign! Envelope: {ds_result}")
                                    supabase.table("contracts").update({
                                        "status":        "Pending",
                                        "sent_at":       datetime.now().isoformat(),
                                        "signed_pdf_url": ds_result
                                    }).eq("contract_id", c["contract_id"]).eq("version", c["version"]).execute()
                                    log_action(c["contract_id"], c["version"], "Sent via DocuSign",
                                        "Internal",
                                        f"DocuSign envelope {ds_result} sent to {cust['email']}")
                                    # Send internal notification to team
                                    send_contract_email(cust, this_v, filled)
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    # Fallback to plain email if DocuSign fails
                                    st.warning(f"DocuSign error: {ds_result}. Falling back to email...")
                                    ok, err = send_contract_email(cust, this_v, filled)
                                    if ok:
                                        supabase.table("contracts").update({
                                            "status":  "Pending",
                                            "sent_at": datetime.now().isoformat()
                                        }).eq("contract_id", c["contract_id"]).eq("version", c["version"]).execute()
                                        log_action(c["contract_id"], c["version"], "Sent via Email",
                                            "Internal", f"Email sent to {cust['email']}")
                                        st.cache_data.clear()
                                        st.success(f"Sent via email to {cust['email']}")
                                        st.rerun()
                                    else:
                                        st.error(f"Email also failed: {err}")
                            else:
                                st.error("Could not load template or customer data.")

                    elif c["status"] == "Declined":
                        if st.button("Revise", key=f"rev_{c['contract_id']}_{c['version']}"):
                            st.session_state["revise_contract_id"] = c["contract_id"]
                            st.session_state["revise_version"]     = c["version"]
                            st.info(f"Go to New Contract tab to revise {c['contract_id']}")
                st.divider()

# ═══════════════════════════════════════════════════════════
# TAB 2: NEW CONTRACT
# ═══════════════════════════════════════════════════════════
with tabs[1]:
    is_revision = "revise_contract_id" in st.session_state
    if is_revision:
        st.markdown(f"""<div class='info-box'>
            Revising contract <strong>{st.session_state['revise_contract_id']}</strong> —
            v{st.session_state['revise_version']} was declined. A new version will be created.
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Contract Details</div>", unsafe_allow_html=True)

    customers = load_customers()
    if not customers:
        st.warning("No customers found. Please check your database.")
    else:
        customer_map = {c["customer_name"]: c for c in customers}
        sel_cust_name = st.selectbox("Select Customer", list(customer_map.keys()))
        sel_customer  = customer_map[sel_cust_name]

        equip_list = load_equipment(sel_customer["customer_id"])
        if not equip_list:
            st.warning("No equipment found for this customer.")
        else:
            equip_map = {
                f"{e['equipment_type']} — {e['make']} {e['model']} ({e['site_location']})": e
                for e in equip_list
            }
            sel_equip_label = st.selectbox("Select Equipment", list(equip_map.keys()))
            sel_equip = equip_map[sel_equip_label]

            col1, col2 = st.columns(2)
            with col1:
                contract_tier = st.selectbox("Contract Tier", ["Platinum", "Gold", "Silver"])
            with col2:
                payment_terms = st.selectbox("Payment Terms", [
                    "Quarterly in advance", "Half-yearly in advance",
                    "Annual in advance", "Monthly"
                ])

            col3, col4 = st.columns(2)
            with col3:
                start_date = st.date_input("Contract Start Date", value=date.today())
            with col4:
                end_date = st.date_input("Contract End Date",
                    value=date(date.today().year + 1, date.today().month, date.today().day))

            contract_value = st.number_input("Contract Value (Rs per annum)",
                min_value=1000.0, step=500.0, value=50000.0)

            changed_fields = ""
            if is_revision:
                changed_fields = st.text_area("What changed in this revision?",
                    placeholder="e.g. Contract value revised; Payment terms changed")

            templates = load_templates(sel_equip["equipment_type"], contract_tier)
            if not templates:
                st.error(f"No template found for {sel_equip['equipment_type']} — {contract_tier}.")
            else:
                template = templates[0]
                draft_contract = {
                    "start_date":     start_date,
                    "end_date":       end_date,
                    "contract_value": contract_value,
                    "payment_terms":  payment_terms,
                }
                filled = fill_template(template["template_body"], sel_customer, sel_equip, draft_contract)

                st.markdown("<div class='section-title'>Contract Preview</div>", unsafe_allow_html=True)
                st.code(filled, language=None)

                # ── Duplicate check (show before button) ─────────────────
                block_save   = False
                warning_msg  = None

                if not is_revision:
                    # Check for Signed contracts with overlapping dates
                    signed_existing = supabase.table("contracts").select(
                        "contract_id, version, contract_tier, start_date, end_date"
                    ).eq("customer_id",  sel_customer["customer_id"])\
                     .eq("equipment_id", sel_equip["equipment_id"])\
                     .eq("status",       "Signed")\
                     .execute()

                    for sc in (signed_existing.data or []):
                        sc_start = sc["start_date"]
                        sc_end   = sc["end_date"]
                        # Check date overlap
                        if str(start_date) <= sc_end and str(end_date) >= sc_start:
                            block_save  = True
                            warning_msg = (
                                f"⛔ Cannot create contract — a **Signed** {sc['contract_tier']} AMC "
                                f"({sc['contract_id']}) already covers this equipment "
                                f"from **{sc_start}** to **{sc_end}**. "
                                f"An active AMC contract exists for this period."
                            )
                            break

                    if not block_save:
                        # Check for Draft or Pending contracts
                        active_existing = supabase.table("contracts").select(
                            "contract_id, version, contract_tier, status"
                        ).eq("customer_id",  sel_customer["customer_id"])\
                         .eq("equipment_id", sel_equip["equipment_id"])\
                         .in_("status",      ["Draft", "Pending"])\
                         .execute()

                        if active_existing.data:
                            active_list = ", ".join([
                                f"{c['contract_id']} ({c['contract_tier']} — {c['status']})"
                                for c in active_existing.data
                            ])
                            warning_msg = (
                                f"ℹ️ Note: An active contract already exists for this equipment — "
                                f"**{active_list}**. You can still save this new contract."
                            )

                # Show warning if any
                if block_save and warning_msg:
                    st.error(warning_msg)
                elif warning_msg:
                    st.info(warning_msg)

                # Show Save button only if not blocked
                if not block_save:
                    if st.button("Save as Draft"):
                        if is_revision:
                            prev_vers   = load_contract_versions(st.session_state["revise_contract_id"])
                            new_version = max(v["version"] for v in prev_vers) + 1
                            contract_id = st.session_state["revise_contract_id"]
                        else:
                            contract_id = generate_contract_id()
                            new_version = 1

                        supabase.table("contracts").insert({
                            "contract_id":    contract_id,
                            "version":        new_version,
                            "customer_id":    sel_customer["customer_id"],
                            "equipment_id":   sel_equip["equipment_id"],
                            "template_id":    template["template_id"],
                            "equipment_type": sel_equip["equipment_type"],
                            "contract_tier":  contract_tier,
                            "contract_value": contract_value,
                            "start_date":     str(start_date),
                            "end_date":       str(end_date),
                            "payment_terms":  payment_terms,
                            "status":         "Draft",
                            "changed_fields": changed_fields,
                        }).execute()

                        log_action(contract_id, new_version, "Created", "Internal",
                            f"Draft — {sel_equip['equipment_type']} {contract_tier}")
                        st.cache_data.clear()

                        if is_revision:
                            del st.session_state["revise_contract_id"]
                            del st.session_state["revise_version"]

                        st.success(f"Contract {contract_id} v{new_version} saved as Draft!")
                        st.rerun()

# ═══════════════════════════════════════════════════════════
# TAB 3: CUSTOMER REVIEW
# ═══════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("<div class='section-title'>Customer Review Simulation</div>", unsafe_allow_html=True)
    st.markdown("""<div class='info-box'>
        This simulates what the customer sees after clicking the link in their email.
        Select a Pending contract to approve or decline.
    </div>""", unsafe_allow_html=True)

    all_contracts     = load_contracts()
    pending_contracts = [c for c in all_contracts if c["status"] == "Pending"]

    if not pending_contracts:
        st.info("No contracts pending customer signature. Send a Draft from the Dashboard first.")
    else:
        pending_map = {
            f"{c['contract_id']} v{c['version']} — {c['customer_name']} ({c['equipment_type']} {c['contract_tier']})": c
            for c in pending_contracts
        }
        options        = list(pending_map.keys())
        selected_label = st.selectbox("Select Pending Contract", options)
        selected_c     = pending_map[selected_label]

        versions     = load_contract_versions(selected_c["contract_id"])
        this_version = next((v for v in versions if v["version"] == selected_c["version"]), None)

        if this_version:
            custs      = load_customers()
            customer   = next((c for c in custs if c["customer_id"] == this_version["customer_id"]), {})
            eq_list    = load_equipment(this_version["customer_id"])
            equip      = next((e for e in eq_list if e["equipment_id"] == this_version["equipment_id"]), {})
            tmpls      = load_templates(this_version["equipment_type"], this_version["contract_tier"])
            template   = tmpls[0] if tmpls else {}

            if template:
                filled = fill_template(template.get("template_body", ""), customer, equip, this_version)
                st.code(filled, language=None)

        st.markdown("---")
        st.markdown(
            f"**Customer:** {selected_c['customer_name']} &nbsp;|&nbsp; "
            f"**Contact:** {selected_c['contact_person']} &nbsp;|&nbsp; "
            f"**Email:** {selected_c['email']}",
            unsafe_allow_html=True
        )

        action   = st.radio("Customer Decision", ["Approve and Sign", "Decline with Comments"])
        comments = ""
        if "Decline" in action:
            comments = st.text_area("Customer Comments / Revision Requests",
                placeholder="e.g. Please revise the contract value. Change payment terms to half-yearly.")

        if st.button("Submit Decision", type="primary"):
            if "Approve" in action:
                supabase.table("contracts").update({
                    "status":    "Signed",
                    "signed_at": datetime.now().isoformat()
                }).eq("contract_id", selected_c["contract_id"]).eq("version", selected_c["version"]).execute()
                log_action(selected_c["contract_id"], selected_c["version"], "Signed", "Customer",
                    f"Signed by {selected_c['contact_person']}")
                st.cache_data.clear()
                st.success(f"Contract {selected_c['contract_id']} v{selected_c['version']} signed!")
                st.balloons()
                st.rerun()
            else:
                if not comments.strip():
                    st.error("Please enter your comments before declining.")
                else:
                    supabase.table("contracts").update({
                        "status":            "Declined",
                        "customer_comments": comments
                    }).eq("contract_id", selected_c["contract_id"]).eq("version", selected_c["version"]).execute()
                    log_action(selected_c["contract_id"], selected_c["version"], "Declined", "Customer", comments)

                    # Send notification email to internal team
                    try:
                        cfg         = st.secrets["email"]
                        smtp_host   = cfg["smtp_host"]
                        smtp_port   = int(cfg["smtp_port"])
                        smtp_user   = cfg["smtp_user"]
                        smtp_pass   = cfg["smtp_password"]
                        sender_name = cfg.get("sender_name", "Carob Technologies")

                        msg = MIMEMultipart("alternative")
                        msg["Subject"] = f"Contract Declined — {selected_c['contract_id']} v{selected_c['version']} — {selected_c['customer_name']}"
                        msg["From"]    = f"{sender_name} <{smtp_user}>"
                        msg["To"]      = smtp_user

                        plain = f"""Contract Declined Notification

Contract ID  : {selected_c['contract_id']} — Version {selected_c['version']}
Customer     : {selected_c['customer_name']}
Contact      : {selected_c['contact_person']} ({selected_c['email']})
Equipment    : {selected_c['equipment_type']} — {selected_c['contract_tier']}
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
        <tr style="background:#f8f9fa;"><td style="padding:10px;font-weight:600;border:1px solid #ddd;width:40%;">Contract ID</td><td style="padding:10px;border:1px solid #ddd;">{selected_c['contract_id']} — v{selected_c['version']}</td></tr>
        <tr><td style="padding:10px;font-weight:600;border:1px solid #ddd;">Customer</td><td style="padding:10px;border:1px solid #ddd;">{selected_c['customer_name']}</td></tr>
        <tr style="background:#f8f9fa;"><td style="padding:10px;font-weight:600;border:1px solid #ddd;">Contact</td><td style="padding:10px;border:1px solid #ddd;">{selected_c['contact_person']} ({selected_c['email']})</td></tr>
        <tr><td style="padding:10px;font-weight:600;border:1px solid #ddd;">Equipment</td><td style="padding:10px;border:1px solid #ddd;">{selected_c['equipment_type']} — {selected_c['contract_tier']}</td></tr>
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

                    except Exception as mail_err:
                        pass  # Don't block the decline flow if email fails

                    st.cache_data.clear()
                    st.warning("Contract declined. Carob Technologies has been notified and will send a revised contract shortly.")
                    st.rerun()

# ═══════════════════════════════════════════════════════════
# TAB 4: AUDIT TRAIL
# ═══════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("<div class='section-title'>Contract Audit Trail</div>", unsafe_allow_html=True)

    all_contracts = load_contracts()
    if not all_contracts:
        st.info("No contracts yet.")
    else:
        contract_ids = sorted(set(c["contract_id"] for c in all_contracts), reverse=True)
        selected_id  = st.selectbox("Select Contract ID", contract_ids)

        versions = load_contract_versions(selected_id)
        if versions:
            st.markdown("**Version History**")
            vdf = pd.DataFrame(versions)[[
                "contract_id", "version", "contract_tier", "equipment_type",
                "contract_value", "status", "changed_fields", "customer_comments",
                "sent_at", "signed_at", "created_at"
            ]]
            vdf.columns = [
                "Contract ID", "Version", "Tier", "Equipment",
                "Value (Rs)", "Status", "Changes", "Customer Comments",
                "Sent At", "Signed At", "Created At"
            ]
            st.dataframe(vdf, use_container_width=True, hide_index=True)

        audit = load_audit(selected_id)
        if audit:
            st.markdown("**Action Log**")
            adf = pd.DataFrame(audit)[["action_at", "action", "action_by", "notes"]]
            adf.columns = ["Timestamp", "Action", "By", "Notes"]
            adf["Timestamp"] = adf["Timestamp"].apply(lambda x: str(x)[:19])
            st.dataframe(adf, use_container_width=True, hide_index=True)
        else:
            st.info("No audit entries yet for this contract.")

# ═══════════════════════════════════════════════════════════
# TAB 5: ANALYTICS
# ═══════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("<div class='section-title'>Contract Analytics</div>", unsafe_allow_html=True)

    # ── Load data ────────────────────────────────────────
    # Latest version per contract for status counts
    latest_res = supabase.table("contracts_latest").select(
        "contract_id, status, contract_tier, equipment_type, contract_value, start_date, end_date, signed_at, sent_at"
    ).execute()
    latest_data = latest_res.data or []

    # Version 1 only for monthly trend (contract initiation date)
    trend_res = supabase.table("contracts").select(
        "contract_id, status, contract_value, contract_tier, equipment_type, created_at"
    ).eq("version", 1).execute()
    trend_data = trend_res.data or []

    if not latest_data:
        st.info("No contract data available for analytics yet.")
    else:
        df_latest = pd.DataFrame(latest_data)
        df_trend  = pd.DataFrame(trend_data)

        # ── Revenue classification ────────────────────────
        def revenue_class(status):
            if status == "Signed":    return "Confirmed Revenue"
            if status in ["Pending", "Cancelled"]: return "Active Pipeline"
            if status == "Declined":  return "At Risk"
            return "Preparation"

        df_latest["revenue_class"]   = df_latest["status"].apply(revenue_class)
        df_latest["contract_value"]  = pd.to_numeric(df_latest["contract_value"], errors="coerce")

        # ── KPI Row ───────────────────────────────────────
        total_contracts  = len(df_latest)
        confirmed_value  = df_latest[df_latest["status"] == "Signed"]["contract_value"].sum()
        pipeline_value   = df_latest[df_latest["status"].isin(["Pending", "Cancelled"])]["contract_value"].sum()
        at_risk_value    = df_latest[df_latest["status"] == "Declined"]["contract_value"].sum()
        signing_rate     = round(len(df_latest[df_latest["status"] == "Signed"]) / total_contracts * 100, 1) if total_contracts else 0

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Contracts",    total_contracts)
        k2.metric("Confirmed Revenue",  f"Rs {confirmed_value:,.0f}")
        k3.metric("Active Pipeline",    f"Rs {pipeline_value:,.0f}")
        k4.metric("At Risk",            f"Rs {at_risk_value:,.0f}")
        k5.metric("Signing Rate",       f"{signing_rate}%")

        st.markdown("---")

        # ── Row 1: Status breakdown + Tier breakdown ──────
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Contracts by Status** (latest version per contract)")
            status_counts = df_latest["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            status_colors = {
                "Signed":    "#10B981",
                "Pending":   "#F59E0B",
                "Declined":  "#EF4444",
                "Cancelled": "#6B7280",
                "Draft":     "#94A3B8",
            }
            try:
                import plotly.express as px
                fig1 = px.pie(
                    status_counts, values="Count", names="Status",
                    color="Status",
                    color_discrete_map=status_colors,
                    hole=0.45
                )
                fig1.update_traces(textposition="inside", textinfo="percent+label")
                fig1.update_layout(showlegend=True, margin=dict(t=20, b=20, l=0, r=0), height=300)
                st.plotly_chart(fig1, use_container_width=True)
            except:
                st.dataframe(status_counts, hide_index=True)

        with col_b:
            st.markdown("**Contract Value by Tier**")
            tier_value = df_latest.groupby("contract_tier")["contract_value"].sum().reset_index()
            tier_value.columns = ["Tier", "Total Value (Rs)"]
            tier_colors = {"Platinum": "#7C3AED", "Gold": "#F59E0B", "Silver": "#64748B"}
            try:
                fig2 = px.bar(
                    tier_value, x="Tier", y="Total Value (Rs)",
                    color="Tier",
                    color_discrete_map=tier_colors,
                    text_auto=True
                )
                fig2.update_layout(showlegend=False, margin=dict(t=20, b=20, l=0, r=0), height=300)
                fig2.update_traces(texttemplate="Rs %{y:,.0f}", textposition="outside")
                st.plotly_chart(fig2, use_container_width=True)
            except:
                st.dataframe(tier_value, hide_index=True)

        # ── Row 2: Equipment type + Revenue classification ─
        col_c, col_d = st.columns(2)

        with col_c:
            st.markdown("**Lift vs Escalator**")
            equip_counts = df_latest.groupby(["equipment_type", "status"]).size().reset_index()
            equip_counts.columns = ["Equipment Type", "Status", "Count"]
            try:
                fig3 = px.bar(
                    equip_counts, x="Equipment Type", y="Count",
                    color="Status", color_discrete_map=status_colors,
                    barmode="stack", text_auto=True
                )
                fig3.update_layout(margin=dict(t=20, b=20, l=0, r=0), height=300)
                st.plotly_chart(fig3, use_container_width=True)
            except:
                st.dataframe(equip_counts, hide_index=True)

        with col_d:
            st.markdown("**Revenue Classification**")
            rev_summary = df_latest.groupby("revenue_class")["contract_value"].sum().reset_index()
            rev_summary.columns = ["Classification", "Value (Rs)"]
            rev_colors = {
                "Confirmed Revenue": "#10B981",
                "Active Pipeline":   "#F59E0B",
                "At Risk":           "#EF4444",
                "Preparation":       "#94A3B8",
            }
            try:
                fig4 = px.bar(
                    rev_summary, x="Classification", y="Value (Rs)",
                    color="Classification",
                    color_discrete_map=rev_colors,
                    text_auto=True
                )
                fig4.update_layout(showlegend=False, margin=dict(t=20, b=20, l=0, r=0), height=300)
                fig4.update_traces(texttemplate="Rs %{y:,.0f}", textposition="outside")
                st.plotly_chart(fig4, use_container_width=True)
            except:
                st.dataframe(rev_summary, hide_index=True)

        # ── Row 3: Monthly trend ──────────────────────────
        st.markdown("**Monthly Contract Trend** (by initiation date — v1 only, revisions excluded)")

        if not df_trend.empty:
            df_trend["month"] = pd.to_datetime(df_trend["created_at"]).dt.strftime("%Y-%m")
            df_trend["contract_value"] = pd.to_numeric(df_trend["contract_value"], errors="coerce")

            monthly = df_trend.groupby(["month", "status"]).size().reset_index()
            monthly.columns = ["Month", "Status", "Count"]

            try:
                fig5 = px.bar(
                    monthly, x="Month", y="Count",
                    color="Status", color_discrete_map=status_colors,
                    barmode="group", text_auto=True
                )
                fig5.update_layout(margin=dict(t=20, b=20, l=0, r=0), height=320)
                st.plotly_chart(fig5, use_container_width=True)
            except:
                st.dataframe(monthly, hide_index=True)

        # ── Row 4: Customer summary table ─────────────────
        st.markdown("**Contract Summary by Customer**")
        cust_summary = df_latest.groupby("status").agg(
            Count=("contract_id", "count"),
            Total_Value=("contract_value", "sum")
        ).reset_index()
        cust_summary.columns = ["Status", "Count", "Total Value (Rs)"]
        cust_summary["Total Value (Rs)"] = cust_summary["Total Value (Rs)"].apply(lambda x: f"Rs {x:,.0f}")
        st.dataframe(cust_summary, use_container_width=True, hide_index=True)
