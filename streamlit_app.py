import streamlit as st
import numpy as np
from datetime import date

# =================================================================
# ⚙️ IEKŠĒJIE KONFIGURĀCIJAS PARAMETRI
# =================================================================
TECHNICAL_PARAMS = {
    "solar_yield": 1050,
    "grid_fee_save": 0.045,
    "bat_cycles": 300,
    "arb_spread": 0.10,
    "bat_eff": 0.88,
    "degradation": 0.005,
    "elec_inflation": 0.03
}

PRICING_CONFIG = {
    "small":  {"max_kw": 20, "solar_eur_kw": 700, "bat_eur_kwh": 250},
    "medium": {"max_kw": 50, "solar_eur_kw": 650, "bat_eur_kwh": 220},
    "large":  {"solar_eur_kw": 600, "bat_eur_kwh": 200}
}

st.set_page_config(page_title="ESTACIJA Piedāvājums & Kredīts", page_icon="📄", layout="wide")

# --- LOGO UN VIRSRAKSTS ---
st.image("New_logo1.png", width=250)
st.title("Piedāvājuma un Finanšu Ģenerators")

# --- 1. IEVADES SADAĻA ---
with st.sidebar:
    st.header("👤 Klienta un Enerģijas dati")
    cust_name = st.text_input("Klients", "SIA Uzņēmums")
    bill_in = st.number_input("Pašreizējais mēneša rēķins (€ bez PVN)", min_value=0.0, value=250.0)
    # Pieņemam vidējo cenu 0.16 EUR/kWh, ja nav norādīts citādi
    usage_est = bill_in / 0.16 
    
    st.divider()
    st.header("🏦 Kredīta kalkulators")
    is_loan = st.checkbox("Iekļaut kredītu piedāvājumā", value=True)
    int_rate = st.slider("Procentu likme (%)", 1.9, 15.0, 1.9) / 100
    loan_yrs = st.select_slider("Termiņš (Gadi)", options=list(range(1, 11)), value=5)

# --- 2. SISTĒMAS KONFIGURĀCIJA ---
st.subheader("🛠️ Sistēmas parametri")
col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    sys_mode = st.selectbox(
        "Scenārijs",
        ["Saules paneļi + Baterijas", "Tikai Saules paneļi", "Tikai Baterijas", "Bateriju pievienošana esošai sistēmai"]
    )
with col_s2:
    new_solar = st.number_input("Jaunā Saules jauda (kW)", min_value=0.0, value=10.0)
with col_s3:
    battery_cap = st.number_input("Bateriju ietilpība (kWh)", min_value=0.0, value=20.0)

exist_solar = st.number_input("Esošā Saules jauda (kW)", min_value=0.0, value=0.0) if "esošai" in sys_mode else 0.0
grant_pct = st.slider("Valsts atbalsts (%)", 0, 50, 30) / 100

# --- 3. APRĒĶINU LOĢIKA ---
# Investīcija
tier_kw = new_solar if new_solar > 0 else (battery_cap / 2)
tier = "small" if tier_kw < 20 else ("medium" if tier_kw < 50 else "large")

inv_total = (new_solar * PRICING_CONFIG[tier]["solar_eur_kw"]) + (battery_cap * PRICING_CONFIG[tier]["bat_eur_kwh"])
net_invest = inv_total * (1 - grant_pct)

# Kredīta maksājums (Anuitāte)
# Formula: $PMT = L \cdot \frac{i(1+i)^n}{(1+i)^n-1}$
if is_loan:
    m_rate = int_rate / 12
    m_count = loan_yrs * 12
    pmt = net_invest * (m_rate * (1+m_rate)**m_count) / ((1+m_rate)**m_count - 1)
else:
    pmt = 0

# Ietaupījums
total_kw = new_solar + exist_solar
ann_save = (total_kw * 1050 * (0.16 + 0.045)) + (battery_cap * 300 * 0.10 * 0.88)
m_save = ann_save / 12

# --- 4. REZULTĀTU CILNES ---
tab1, tab2, tab3 = st.tabs(["📋 Piedāvājums", "📊 Rēķinu salīdzinājums", "📈 ROI Grafiks"])

with tab1:
    st.markdown(f"### Piedāvājums: {cust_name}")
    st.write(f"Sistēma: {new_solar}kW Saule + {battery_cap}kWh Baterijas")
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Investīcija (Neto)", f"{net_invest:,.0f} €")
    c2.metric("Mēneša ietaupījums", f"{m_save:,.2f} €")
    if is_loan:
        c3.metric("Kredīta maksājums", f"{pmt:,.2f} €")
    
    st.success(f"**Tīrais mēneša ieguvums (Cash-flow): {m_save - pmt:,.2f} €**")

with tab2:
    st.subheader("Mēneša izmaksu piemērs")
    st.write("Salīdzinājums starp pašreizējo situāciju un modeli pēc sistēmas uzstādīšanas.")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.error("📉 ŠOBRĪD (Bez sistēmas)")
        st.write(f"Mēneša rēķins: **{bill_in:,.2f} €**")
        st.write("Kredīta maksājums: 0.00 €")
        st.write("---")
        st.write(f"**KOPĀ: {bill_in:,.2f} €**")
        
    with col_v2:
        st.success("🚀 AR ESTACIJA SISTĒMU")
        new_bill = max(0, bill_in - m_save)
        st.write(f"Jaunais rēķins (provizoriski): **{new_bill:,.2f} €**")
        st.write(f"Kredīta maksājums: **{pmt:,.2f} €**")
        st.write("---")
        st.write(f"**KOPĀ: {new_bill + pmt:,.2f} €**")
    
    diff = bill_in - (new_bill + pmt)
    st.info(f"💡 **Secinājums:** Klients katru mēnesi ietaupa **{diff:,.2f} €**, pat maksājot kredītu!")

with tab3:
    st.subheader("Kumulatīvā naudas plūsma (20 gadi)")
    cash_flows = []
    balance = -net_invest if not is_loan else 0 # Ja ir kredīts, sākam no 0, bet rēķinām CF
    
    curr_bal = -net_invest if not is_loan else 0
    for y in range(21):
        if y > 0:
            y_save = ann_save * ((1.03)**y)
            y_loan = (pmt * 12) if (is_loan and y <= loan_yrs) else 0
            curr_bal += (y_save - y_loan)
        cash_flows.append(curr_bal)
    
    st.area_chart(cash_flows)
    

st.markdown("---")
st.caption(f"Piedāvājums Nr. {date.today().strftime('%Y%m%d')}-1. Finanšu aprēķinam ir informatīvs raksturs.")