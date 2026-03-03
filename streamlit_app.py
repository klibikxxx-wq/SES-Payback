import streamlit as st
import numpy as np
import os
from datetime import date
from fpdf import FPDF

# =================================================================
# ⚙️ 1. KONFIGURĀCIJA UN CENAS
# =================================================================
TECHNICAL_PARAMS = {
    "solar_yield": 1050,      # kWh/kWp gadā
    "grid_fee_save": 0.045,   # €/kWh (Sadales tīkls)
    "bat_cycles": 300,        # Cikli gadā
    "arb_spread": 0.10,       # €/kWh starpība
    "bat_eff": 0.88,          # Baterijas lietderība
    "degradation": 0.005,     # 0.5% gadā
    "elec_inflation": 0.03    # 3% gadā
}

PRICING_CONFIG = {
    "small":  {"max_kw": 20, "solar_eur_kw": 700, "bat_eur_kwh": 250},
    "medium": {"max_kw": 50, "solar_eur_kw": 650, "bat_eur_kwh": 220},
    "large":  {"solar_eur_kw": 600, "bat_eur_kwh": 200}
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =================================================================
# 📄 2. PDF KLASES DEFINĪCIJA (Latviešu valodas atbalsts)
# =================================================================
class EstacijaPDF(FPDF):
    def __init__(self):
        super().__init__()
        # Mēģinām ielādēt fontus no tās pašas mapes
        reg_path = os.path.join(BASE_DIR, "Roboto-Regular.ttf")
        bold_path = os.path.join(BASE_DIR, "Roboto-Bold.ttf")
        
        if os.path.exists(reg_path) and os.path.exists(bold_path):
            self.add_font("Roboto", "", reg_path)
            self.add_font("Roboto", "B", bold_path)
            self.font_family_name = "Roboto"
        else:
            self.font_family_name = "helvetica" # Rezerves variants (bez LV zīmēm)

    def header(self):
        logo_path = os.path.join(BASE_DIR, "New_logo1.png")
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 35)
        self.set_font(self.font_family_name, "B", 14)
        self.cell(0, 10, "KOMERCIĀLAIS PIEDĀVĀJUMS", border=0, align="R")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family_name, "", 8)
        self.cell(0, 10, f"Lapa {self.page_no()}/{{nb}} | estacija.lv", align="C")

# =================================================================
# 🖥️ 3. STREAMLIT LIETOTNES SASKARNE
# =================================================================
st.set_page_config(page_title="ESTACIJA Piedāvājumu Sistēma", layout="wide")

# Logo attēlošana UI
logo_ui = os.path.join(BASE_DIR, "New_logo1.png")
if os.path.exists(logo_ui):
    st.image(logo_ui, width=200)

st.title("Saules un Bateriju Sistēmu Piedāvājumu Ģenerators")

# --- IEVADES DATI ---
with st.sidebar:
    st.header("👤 Klienta dati")
    c_name = st.text_input("Klients", "SIA Klienta Uzņēmums")
    c_addr = st.text_input("Adrese", "Rīga, Latvija")
    c_bill = st.number_input("Esošais mēneša rēķins (€ bez PVN)", value=300.0)
    
    st.divider()
    st.header("🏦 Finansējums")
    is_loan = st.checkbox("Iekļaut kredītu", value=True)
    loan_rate = st.slider("Likme (%)", 1.9, 12.0, 1.9) / 100
    loan_years = st.select_slider("Termiņš (Gadi)", options=list(range(1, 11)), value=5)
    grant_pct = st.slider("Valsts atbalsts (%)", 0, 50, 30) / 100

st.subheader("🛠️ Sistēmas Konfigurācija")
col1, col2, col3 = st.columns(3)

with col1:
    scenario = st.selectbox("Scenārijs", [
        "Saules paneļi + Baterijas", 
        "Tikai Saules paneļi", 
        "Tikai Baterijas", 
        "Bateriju pievienošana esošai sistēmai"
    ])
with col2:
    new_kw = st.number_input("Jaunā Saules jauda (kW)", min_value=0.0, value=10.0 if "Saules" in scenario else 0.0)
    exist_kw = st.number_input("Esošā Saules jauda (kW)", min_value=0.0, value=0.0) if "esošai" in scenario else 0.0
with col3:
    bat_kwh = st.number_input("Bateriju ietilpība (kWh)", min_value=0.0, value=20.0 if "Baterija" in scenario or "Bateriju" in scenario else 0.0)

# =================================================================
# 🧮 4. APRĒĶINU MOTORS
# =================================================================
# Cenu līmeņa noteikšana
calc_tier_kw = new_kw if new_kw > 0 else (bat_kwh / 2)
if calc_tier_kw < PRICING_CONFIG["small"]["max_kw"]: tier = "small"
elif calc_tier_kw < PRICING_CONFIG["medium"]["max_kw"]: tier = "medium"
else: tier = "large"

s_u = PRICING_CONFIG[tier]["solar_eur_kw"]
b_u = PRICING_CONFIG[tier]["bat_eur_kwh"]

# Investīcija
inv_s = new_kw * s_u
inv_b = bat_kwh * b_u
total_neto = inv_s + inv_b
grant_val = total_neto * grant_pct
net_invest = total_neto - grant_val

# Ietaupījums
total_active_kw = new_kw + exist_kw
save_solar = (total_active_kw * TECHNICAL_PARAMS["solar_yield"]) * (0.16 + TECHNICAL_PARAMS["grid_fee_save"])
save_bat = (bat_kwh * TECHNICAL_PARAMS["bat_cycles"] * TECHNICAL_PARAMS["arb_spread"] * TECHNICAL_PARAMS["bat_eff"])
monthly_save = (save_solar + save_bat) / 12

# Kredīta PMT formula
pmt = 0
if is_loan and net_invest > 0:
    r = loan_rate / 12
    n = loan_years * 12
    pmt = net_invest * (r * (1+r)**n) / ((1+r)**n - 1)

# =================================================================
# 📊 5. REZULTĀTU ATTĒLOŠANA
# =================================================================
t1, t2, t3 = st.tabs(["📋 Piedāvājums", "⚖️ Rēķinu salīdzinājums", "📈 ROI Grafiks"])

with t1:
    m1, m2, m3 = st.columns(3)
    m1.metric("Gala investīcija", f"{net_invest:,.0f} €")
    m2.metric("Mēneša ietaupījums", f"{monthly_save:,.2f} €")
    m3.metric("Mēneša Cash-flow", f"{monthly_save - pmt:,.2f} €")

    # PDF Ģenerēšanas poga
    def generate_pdf_bytes():
        pdf = EstacijaPDF()
        pdf.add_page()
        pdf.set_font(pdf.font_family_name, "B", 12)
        pdf.cell(0, 10, f"Klients: {c_name}", ln=True)
        pdf.set_font(pdf.font_family_name, "", 10)
        pdf.cell(0, 5, f"Objekta adrese: {c_addr}", ln=True)
        pdf.cell(0, 5, f"Datums: {date.today().strftime('%d.%m.%Y')}", ln=True)
        pdf.ln(10)

        # Tabula
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font(pdf.font_family_name, "B", 10)
        pdf.cell(85, 10, "Pozīcija", 1, 0, "L", True)
        pdf.cell(35, 10, "Apjoms", 1, 0, "C", True)
        pdf.cell(35, 10, "Cena (vien.)", 1, 0, "C", True)
        pdf.cell(35, 10, "Summa", 1, 1, "C", True)
        
        pdf.set_font(pdf.font_family_name, "", 10)
        if new_kw > 0:
            pdf.cell(85, 10, "Saules paneļu sistēmas uzstādīšana", 1)
            pdf.cell(35, 10, f"{new_kw} kW", 1, 0, "C")
            pdf.cell(35, 10, f"{s_u} €", 1, 0, "C")
            pdf.cell(35, 10, f"{inv_s:,.2f} €", 1, 1, "C")
        if bat_kwh > 0:
            pdf.cell(85, 10, "Bateriju krātuves uzstādīšana (LFP)", 1)
            pdf.cell(35, 10, f"{bat_kwh} kWh", 1, 0, "C")
            pdf.cell(35, 10, f"{b_u} €", 1, 0, "C")
            pdf.cell(35, 10, f"{inv_b:,.2f} €", 1, 1, "C")

        pdf.ln(5)
        pdf.set_font(pdf.font_family_name, "B", 11)
        pdf.cell(155, 8, "KOPĀ NETO:", 0, 0, "R")
        pdf.cell(35, 8, f"{total_neto:,.2f} €", 0, 1, "R")
        pdf.cell(155, 8, f"Valsts atbalsts ({int(grant_pct*100)}%):", 0, 0, "R")
        pdf.cell(35, 8, f"-{grant_val:,.2f} €", 0, 1, "R")
        pdf.set_text_color(34, 139, 34)
        pdf.cell(155, 10, "GALA INVESTĪCIJA:", 0, 0, "R")
        pdf.cell(35, 10, f"{net_invest:,.2f} €", 0, 1, "R")
        
        return pdf.output()

    if st.button("Sagatavot PDF failu"):
        pdf_data = generate_pdf_bytes()
        st.download_button(
            label="📥 Lejupielādēt PDF",
            data=bytes(pdf_data),
            file_name=f"Estacija_Piedavajums_{c_name.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

with t2:
    st.subheader("Mēneša izmaksu piemērs ar sistēmu")
    c_now, c_future = st.columns(2)
    with c_now:
        st.error(f"ŠOBRĪD: {c_bill:,.2f} € / mēn")
        st.caption("Tikai elektrības rēķins")
    with c_future:
        new_bill = max(0, c_bill - monthly_save)
        st.success(f"NĀKOTNĒ: {new_bill + pmt:,.2f} € / mēn")
        st.caption(f"Rēķins: {new_bill:,.2f} € + Kredīts: {pmt:,.2f} €")
    
    st.info(f"Klients katru mēnesi ietaupa **{c_bill - (new_bill + pmt):,.2f} €** no savas naudas plūsmas.")

with t3:
    st.subheader("Kumulatīvā naudas plūsma (20 gadi)")
    balance = -net_invest if not is_loan else 0
    history = []
    for y in range(21):
        if y > 0:
            y_save = (monthly_save * 12) * ((1 + TECHNICAL_PARAMS["elec_inflation"])**y) * ((1 - TECHNICAL_PARAMS["degradation"])**y)
            y_loan = (pmt * 12) if (is_loan and y <= loan_years) else 0
            balance += (y_save - y_loan)
        history.append(balance)
    
    st.area_chart(history)
    
    st.write(f"Sistēmas tīrā peļņa 20 gadu laikā: **{history[-1]:,.0f} €**")