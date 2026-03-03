import streamlit as st
import numpy as np
from datetime import date
from fpdf import FPDF
import base64
import os

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

# --- PDF ĢENERĒŠANAS FUNKCIJA ---
class ESTACIJA_PDF(FPDF):
    def header(self):
        if os.path.exists("New_logo1.png"):
            self.image("New_logo1.png", 10, 8, 40)
        self.set_font("helvetica", "B", 15)
        self.cell(80)
        self.cell(110, 10, "KOMERCIĀLAIS PIEDĀVĀJUMS", border=0, align="R")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Lapa {self.page_no()}/{{nb}} | estacija.lv", align="C")

def create_pdf(cust_data, system_data, finance_data):
    pdf = ESTACIJA_PDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    
    # Klienta dati
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, f"Klients: {cust_data['name']}", ln=True)
    pdf.set_font("helvetica", size=10)
    pdf.cell(0, 5, f"Adrese: {cust_data['addr']}", ln=True)
    pdf.cell(0, 5, f"Piedāvājuma Nr: {cust_data['no']}", ln=True)
    pdf.cell(0, 5, f"Datums: {date.today().strftime('%d.%m.%Y')}", ln=True)
    pdf.ln(10)

    # Tabulas galvene
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(90, 10, "Pozicija", border=1, fill=True)
    pdf.cell(30, 10, "Apjoms", border=1, fill=True, align="C")
    pdf.cell(30, 10, "Cena (vien.)", border=1, fill=True, align="C")
    pdf.cell(40, 10, "Summa", border=1, fill=True, align="C")
    pdf.ln()

    # Pozīcijas
    pdf.set_font("helvetica", size=10)
    for item in system_data['items']:
        pdf.cell(90, 10, item['name'], border=1)
        pdf.cell(30, 10, item['qty'], border=1, align="C")
        pdf.cell(30, 10, f"{item['price']} EUR", border=1, align="C")
        pdf.cell(40, 10, f"{item['total']:,} EUR", border=1, align="C")
        pdf.ln()

    # Kopsavilkums
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(150, 10, "KOPA NETO:", align="R")
    pdf.cell(40, 10, f"{finance_data['total_neto']:,} EUR", align="R")
    pdf.ln()
    pdf.cell(150, 10, f"Valsts atbalsts ({finance_data['grant_pct']}%):", align="R")
    pdf.cell(40, 10, f"-{finance_data['grant_val']:,} EUR", align="R")
    pdf.ln()
    pdf.set_text_color(0, 100, 0)
    pdf.cell(150, 10, "GALA INVESTICIJA:", align="R")
    pdf.cell(40, 10, f"{finance_data['final_invest']:,} EUR", align="R")
    
    # Kredīta info ja ir
    if finance_data['pmt'] > 0:
        pdf.set_text_color(0, 0, 0)
        pdf.ln(15)
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 10, "Finansejuma informācija (Kredits):", ln=True)
        pdf.set_font("helvetica", size=10)
        pdf.cell(0, 7, f"- Menesa maksajums: {finance_data['pmt']:.2f} EUR", ln=True)
        pdf.cell(0, 7, f"- Termins: {finance_data['loan_yrs']} gadi", ln=True)
        pdf.cell(0, 7, f"- Procentu likme: {finance_data['int_rate']*100}%", ln=True)

    return pdf.output(dest='S')

# =================================================================
# 🖥️ STREAMLIT UI
# =================================================================

st.set_page_config(page_title="ESTACIJA Piedāvājums & Kredīts", page_icon="📄", layout="wide")

st.image("New_logo1.png", width=250)
st.title("Piedāvājuma un Finanšu Ģenerators")

with st.sidebar:
    st.header("👤 Klienta un Enerģijas dati")
    cust_name = st.text_input("Klients", "SIA Uzņēmums")
    cust_addr = st.text_input("Adrese", "Rīga, Latvija")
    offer_no = st.text_input("Piedāvājuma Nr.", "2026-OFF-001")
    bill_in = st.number_input("Pašreizējais mēneša rēķins (€ bez PVN)", min_value=0.0, value=250.0)
    
    st.divider()
    st.header("🏦 Kredīts")
    is_loan = st.checkbox("Iekļaut kredītu", value=True)
    int_rate = st.slider("Likme (%)", 1.9, 15.0, 1.9) / 100
    loan_yrs = st.select_slider("Gadi", options=list(range(1, 11)), value=5)

st.subheader("🛠️ Sistēmas konfigurācija")
col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    sys_mode = st.selectbox("Scenārijs", ["Saules paneļi + Baterijas", "Tikai Saules paneļi", "Tikai Baterijas", "Bateriju pievienošana esošai sistēmai"])
with col_s2:
    new_solar = st.number_input("Jaunā Saule (kW)", min_value=0.0, value=10.0)
with col_s3:
    battery_cap = st.number_input("Baterijas (kWh)", min_value=0.0, value=20.0)

exist_solar = st.number_input("Esošā Saule (kW)", min_value=0.0, value=0.0) if "esošai" in sys_mode else 0.0
grant_pct_val = st.slider("Valsts atbalsts (%)", 0, 50, 30)

# --- APRĒĶINI ---
tier_kw = new_solar if new_solar > 0 else (battery_cap / 2)
tier = "small" if tier_kw < 20 else ("medium" if tier_kw < 50 else "large")
s_u = PRICING_CONFIG[tier]["solar_eur_kw"]
b_u = PRICING_CONFIG[tier]["bat_eur_kwh"]

inv_solar = new_solar * s_u
inv_bat = battery_cap * b_u
total_neto = inv_solar + inv_bat
grant_amount = total_neto * (grant_pct_val / 100)
net_invest = total_neto - grant_amount

# Kredīts
pmt = 0
if is_loan:
    m_r = int_rate / 12
    m_c = loan_yrs * 12
    pmt = net_invest * (m_r * (1+m_r)**m_c) / ((1+m_r)**m_c - 1)

# Ietaupījums
m_save = ((new_solar + exist_solar) * 1050 * (0.16 + 0.045) + battery_cap * 300 * 0.10 * 0.88) / 12

# --- UI ATTĒLOŠANA ---
tab1, tab2 = st.tabs(["📋 Piedāvājums un ROI", "📉 Rēķinu piemērs"])

with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Investīcija", f"{net_invest:,.0f} €")
    c2.metric("Mēneša ietaupījums", f"{m_save:,.2f} €")
    c3.metric("Mēneša Cash-flow", f"{m_save - pmt:,.2f} €")

    # PDF Poga
    sys_items = []
    if new_solar > 0: sys_items.append({'name': 'Saules panelu sistema', 'qty': f'{new_solar} kW', 'price': s_u, 'total': inv_solar})
    if battery_cap > 0: sys_items.append({'name': 'Akumulatoru kratuve', 'qty': f'{battery_cap} kWh', 'price': b_u, 'total': inv_bat})

    pdf_bytes = create_pdf(
        {'name': cust_name, 'addr': cust_addr, 'no': offer_no},
        {'items': sys_items},
        {'total_neto': total_neto, 'grant_pct': grant_pct_val, 'grant_val': grant_amount, 'final_invest': net_invest, 'pmt': pmt, 'loan_yrs': loan_yrs, 'int_rate': int_rate}
    )

    st.download_button(
        label="📥 Lejupielādēt PDF piedāvājumu",
        data=pdf_bytes,
        file_name=f"ESTACIJA_Piedavajums_{cust_name.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

with tab2:
    st.subheader("Mēneša izmaksu salīdzinājums")
    col_a, col_b = st.columns(2)
    with col_a:
        st.error(f"ŠOBRĪD: {bill_in:,.2f} €/mēn")
    with col_b:
        new_bill = max(0, bill_in - m_save)
        st.success(f"AR SISTĒMU: {new_bill + pmt:,.2f} €/mēn")
        st.write(f"(Rēķins: {new_bill:,.2f} € + Kredīts: {pmt:,.2f} €)")