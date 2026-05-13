import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date, datetime
import re

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

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
h1, h2, h3 {
    font-family: 'DM Serif Display', serif;
}

/* Header */
.app-header {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.app-header h1 {
    color: #ffffff;
    margin: 0;
    font-size: 1.6rem;
    letter-spacing: 0.5px;
}
.app-header span {
    color: #a8d8ea;
    font-size: 0.85rem;
}

/* Status badges */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.badge-draft    { background: #e8e8e8; color: #555; }
.badge-pending  { background: #fff3cd; color: #856404; }
.badge-signed   { background: #d4edda; color: #155724; }
.badge-declined { background: #f8d7da; color: #721c24; }

/* Contract card */
.contract-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    border-left: 4px solid #2c5364;
}
.contract-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.08); }

/* Contract preview box */
.contract-preview {
    background: #fafafa !important;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1.5rem;
    font-family: 'Courier New', monospace;
    font-size: 0.82rem;
    line-height: 1.7;
    white-space: pre-wrap;
    max-height: 420px;
    overflow-y: auto;
    color: #1a1a1a !important;
}

/* Tier badges */
.tier-platinum { background: #e8e0f7; color: #4a1e8a; border-radius: 6px; padding: 2px 8px; font-size: 0.8rem; font-weight: 600; }
.tier-gold     { background: #fff4d6; color: #92650a; border-radius: 6px; padding: 2px 8px; font-size: 0.8rem; font-weight: 600; }
.tier-silver   { background: #eaeaea; color: #444;    border-radius: 6px; padding: 2px 8px; font-size: 0.8rem; font-weight: 600; }

/* Section headers */
.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.2rem;
    color: #2c5364;
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
}

/* Metric cards */
.metric-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.metric-card {
    flex: 1;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
}
.metric-card .num { font-size: 2rem; font-weight: 700; color: #2c5364; }
.metric-card .lbl { font-size: 0.78rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }

/* Info box */
.info-box {
    background: #eef6fb;
    border-left: 4px solid #2c5364;
    padding: 0.8rem 1rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 1rem;
    font-size: 0.88rem;
    color: #2c5364;
}
.declined-box {
    background: #fff5f5;
    border-left: 4px solid #dc3545;
    padding: 0.8rem 1rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 1rem;
    font-size: 0.88rem;
    color: #721c24;
}
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
# HELPERS
# ─────────────────────────────────────────────
def generate_contract_id():
    year = date.today().year
    res = supabase.table("contracts").select("contract_id").execute()
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
        "{{customer_name}}":     customer["customer_name"],
        "{{contact_person}}":    customer["contact_person"],
        "{{customer_address}}":  customer["address"],
        "{{customer_city}}":     customer["city"],
        "{{customer_pincode}}":  customer["pincode"],
        "{{equipment_type}}":    equipment["equipment_type"],
        "{{equipment_make}}":    equipment["make"],
        "{{equipment_model}}":   equipment["model"],
        "{{serial_number}}":     equipment.get("serial_number", "N/A"),
        "{{number_of_units}}":   str(equipment["number_of_units"]),
        "{{site_location}}":     equipment["site_location"],
        "{{installation_date}}": str(equipment["installation_date"]),
        "{{start_date}}":        str(contract.get("start_date", "")),
        "{{end_date}}":          str(contract.get("end_date", "")),
        "{{contract_value}}":    f"{contract.get('contract_value', 0):,.2f}",
        "{{payment_terms}}":     contract.get("payment_terms", ""),
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
    cls = f"badge-{status.lower()}"
    return f'<span class="badge {cls}">{status.upper()}</span>'

def tier_html(tier):
    cls = f"tier-{tier.lower()}"
    return f'<span class="{cls}">{tier}</span>'

# ─────────────────────────────────────────────
# LOAD DATA
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
    <h1>📋 Service Contract Manager</h1>
    <span>Carob Technologies &nbsp;|&nbsp; Lift & Escalator AMC</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────
tabs = st.tabs(["📊 Dashboard", "➕ New Contract", "✍️ Customer Review", "📜 Audit Trail"])

# ═══════════════════════════════════════════════════════════
# TAB 1: DASHBOARD
# ═══════════════════════════════════════════════════════════
with tabs[0]:
    contracts = load_contracts()

    # Metrics
    total    = len(set(c["contract_id"] for c in contracts))
    pending  = sum(1 for c in contracts if c["status"] == "Pending")
    signed   = sum(1 for c in contracts if c["status"] == "Signed")
    declined = sum(1 for c in contracts if c["status"] == "Declined")
    draft    = sum(1 for c in contracts if c["status"] == "Draft")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Contracts", total)
    c2.metric("Draft",    draft,    delta=None)
    c3.metric("Pending",  pending,  delta=None)
    c4.metric("Signed",   signed,   delta=None)
    c5.metric("Declined", declined, delta=None)

    st.markdown("<div class='section-title'>All Contracts</div>", unsafe_allow_html=True)

    # Filters
    f1, f2, f3 = st.columns(3)
    with f1:
        status_filter = st.selectbox("Filter by Status", ["All", "Draft", "Pending", "Signed", "Declined"])
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
        st.info("No contracts found. Create one from the 'New Contract' tab.")
    else:
        for c in filtered:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 1.5, 1])
                with col1:
                    st.markdown(f"**{c['contract_id']}** &nbsp; v{c['version']}", unsafe_allow_html=True)
                    st.caption(f"{c['customer_name']} — {c['contact_person']}")
                with col2:
                    st.markdown(f"{c['equipment_type']} &nbsp; {tier_html(c['contract_tier'])}", unsafe_allow_html=True)
                    st.caption(f"{c['equipment']}")
                with col3:
                    st.markdown(f"₹ {c['contract_value']:,.0f}", unsafe_allow_html=True)
                    st.caption(f"{c['start_date']} → {c['end_date']}")
                with col4:
                    st.markdown(badge_html(c["status"]), unsafe_allow_html=True)
                    if c.get("signed_at"):
                        st.caption(f"Signed: {str(c['signed_at'])[:10]}")
                    elif c.get("sent_at"):
                        st.caption(f"Sent: {str(c['sent_at'])[:10]}")
                with col5:
                    if c["status"] == "Draft":
                        if st.button("Send →", key=f"send_{c['contract_id']}_{c['version']}"):
                            supabase.table("contracts").update({
                                "status": "Pending",
                                "sent_at": datetime.now().isoformat()
                            }).eq("contract_id", c["contract_id"]).eq("version", c["version"]).execute()
                            log_action(c["contract_id"], c["version"], "Sent", "Internal", "Dispatched for e-signature")
                            st.cache_data.clear()
                            st.success(f"Contract {c['contract_id']} sent for signature!")
                            st.rerun()
                    elif c["status"] == "Declined":
                        if st.button("Revise", key=f"rev_{c['contract_id']}_{c['version']}"):
                            st.session_state["revise_contract_id"] = c["contract_id"]
                            st.session_state["revise_version"]     = c["version"]
                            st.info(f"Go to 'New Contract' tab to revise {c['contract_id']}")
                st.divider()

# ═══════════════════════════════════════════════════════════
# TAB 2: NEW CONTRACT
# ═══════════════════════════════════════════════════════════
with tabs[1]:
    is_revision = "revise_contract_id" in st.session_state
    if is_revision:
        st.markdown(f"""<div class='info-box'>
            ✏️ Revising contract <strong>{st.session_state['revise_contract_id']}</strong> — 
            v{st.session_state['revise_version']} was declined. A new version will be created.
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Contract Details</div>", unsafe_allow_html=True)

    customers = load_customers()
    if not customers:
        st.warning("No customers found. Please check your database.")
    else:
        customer_map = {c["customer_name"]: c for c in customers}
        selected_customer_name = st.selectbox("Select Customer", list(customer_map.keys()))
        selected_customer = customer_map[selected_customer_name]

        # Load equipment for this customer
        equip_list = load_equipment(selected_customer["customer_id"])
        if not equip_list:
            st.warning("No equipment found for this customer.")
        else:
            equip_map = {
                f"{e['equipment_type']} — {e['make']} {e['model']} ({e['site_location']})": e
                for e in equip_list
            }
            selected_equip_label = st.selectbox("Select Equipment", list(equip_map.keys()))
            selected_equip = equip_map[selected_equip_label]

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

            contract_value = st.number_input("Contract Value (₹ per annum)", min_value=1000.0, step=500.0, value=50000.0)

            if is_revision:
                changed_fields = st.text_area("What changed in this revision?",
                    placeholder="e.g. Contract value revised from ₹50,000 to ₹45,000; Payment terms changed to quarterly")
            else:
                changed_fields = ""

            # Load template
            templates = load_templates(selected_equip["equipment_type"], contract_tier)
            if not templates:
                st.error(f"No template found for {selected_equip['equipment_type']} — {contract_tier}. Please check the contract_templates table.")
            else:
                template = templates[0]
                draft_contract = {
                    "start_date":      start_date,
                    "end_date":        end_date,
                    "contract_value":  contract_value,
                    "payment_terms":   payment_terms,
                }
                filled = fill_template(template["template_body"], selected_customer, selected_equip, draft_contract)

                st.markdown("<div class='section-title'>Contract Preview</div>", unsafe_allow_html=True)
                st.text_area(
                    "Contract Document",
                    value=filled,
                    height=400,
                    disabled=True,
                    label_visibility="collapsed"
                )

                col_a, col_b = st.columns([1, 3])
                with col_a:
                    if st.button("💾 Save as Draft", use_container_width=True):
                        if is_revision:
                            prev_versions = load_contract_versions(st.session_state["revise_contract_id"])
                            new_version   = max(v["version"] for v in prev_versions) + 1
                            contract_id   = st.session_state["revise_contract_id"]
                        else:
                            contract_id = generate_contract_id()
                            new_version = 1

                        supabase.table("contracts").insert({
                            "contract_id":     contract_id,
                            "version":         new_version,
                            "customer_id":     selected_customer["customer_id"],
                            "equipment_id":    selected_equip["equipment_id"],
                            "template_id":     template["template_id"],
                            "equipment_type":  selected_equip["equipment_type"],
                            "contract_tier":   contract_tier,
                            "contract_value":  contract_value,
                            "start_date":      str(start_date),
                            "end_date":        str(end_date),
                            "payment_terms":   payment_terms,
                            "status":          "Draft",
                            "changed_fields":  changed_fields,
                        }).execute()

                        log_action(contract_id, new_version, "Created", "Internal",
                            f"Draft created — {selected_equip['equipment_type']} {contract_tier}")
                        st.cache_data.clear()

                        if is_revision:
                            del st.session_state["revise_contract_id"]
                            del st.session_state["revise_version"]

                        st.success(f"✅ Contract {contract_id} v{new_version} saved as Draft!")
                        st.rerun()

# ═══════════════════════════════════════════════════════════
# TAB 3: CUSTOMER REVIEW (simulate customer signing)
# ═══════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("<div class='section-title'>Customer Review Simulation</div>", unsafe_allow_html=True)
    st.markdown("""<div class='info-box'>
        This simulates what the customer sees after clicking the e-sign link in their email.
        Select a Pending contract to approve or decline it.
    </div>""", unsafe_allow_html=True)

    all_contracts = load_contracts()
    pending_contracts = [c for c in all_contracts if c["status"] == "Pending"]

    if not pending_contracts:
        st.info("No contracts are currently pending customer signature.")
    else:
        pending_map = {
            f"{c['contract_id']} v{c['version']} — {c['customer_name']} ({c['equipment_type']} {c['contract_tier']})": c
            for c in pending_contracts
        }
        selected_label = st.selectbox("Select Pending Contract", list(pending_map.keys()))
        selected_c     = pending_map[selected_label]

        # Load full contract + template to show preview
        versions = load_contract_versions(selected_c["contract_id"])
        this_version = next((v for v in versions if v["version"] == selected_c["version"]), None)

        if this_version:
            customer   = next((c for c in load_customers() if c["customer_id"] == this_version["customer_id"]), {})
            equip_list = load_equipment(this_version["customer_id"])
            equip      = next((e for e in equip_list if e["equipment_id"] == this_version["equipment_id"]), {})
            templates  = load_templates(this_version["equipment_type"], this_version["contract_tier"])
            template   = templates[0] if templates else {}

            if template:
                filled = fill_template(template.get("template_body", ""), customer, equip, this_version)
                st.text_area(
                    "Contract Document",
                    value=filled,
                    height=400,
                    disabled=True,
                    label_visibility="collapsed"
                )

        st.markdown("---")
        st.markdown(f"**Customer:** {selected_c['customer_name']} &nbsp;|&nbsp; **Contact:** {selected_c['contact_person']} &nbsp;|&nbsp; **Email:** {selected_c['email']}")

        action = st.radio("Customer Decision", ["✅ Approve & Sign", "❌ Decline with Comments"], horizontal=True)
        comments = ""
        if "Decline" in action:
            comments = st.text_area("Customer Comments / Revision Requests",
                placeholder="e.g. Please revise the contract value. Also change payment terms to half-yearly.")

        if st.button("Submit Decision", type="primary"):
            if "Approve" in action:
                supabase.table("contracts").update({
                    "status":    "Signed",
                    "signed_at": datetime.now().isoformat()
                }).eq("contract_id", selected_c["contract_id"]).eq("version", selected_c["version"]).execute()
                log_action(selected_c["contract_id"], selected_c["version"], "Signed", "Customer",
                    f"Signed by {selected_c['contact_person']}")
                st.cache_data.clear()
                st.success(f"✅ Contract {selected_c['contract_id']} v{selected_c['version']} has been signed!")
                st.balloons()
                st.rerun()
            else:
                if not comments.strip():
                    st.error("Please enter customer comments before declining.")
                else:
                    supabase.table("contracts").update({
                        "status":           "Declined",
                        "customer_comments": comments
                    }).eq("contract_id", selected_c["contract_id"]).eq("version", selected_c["version"]).execute()
                    log_action(selected_c["contract_id"], selected_c["version"], "Declined", "Customer", comments)
                    st.cache_data.clear()
                    st.warning(f"Contract {selected_c['contract_id']} declined. Go to Dashboard to revise.")
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

        # Show version history
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
                "Value (₹)", "Status", "Changes", "Customer Comments",
                "Sent At", "Signed At", "Created At"
            ]
            st.dataframe(vdf, use_container_width=True, hide_index=True)

        # Show audit log
        audit = load_audit(selected_id)
        if audit:
            st.markdown("**Action Log**")
            adf = pd.DataFrame(audit)[["action_at", "action", "action_by", "notes"]]
            adf.columns = ["Timestamp", "Action", "By", "Notes"]
            adf["Timestamp"] = adf["Timestamp"].apply(lambda x: str(x)[:19])
            st.dataframe(adf, use_container_width=True, hide_index=True)
        else:
            st.info("No audit entries yet for this contract.")
