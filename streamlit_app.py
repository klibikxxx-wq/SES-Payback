import streamlit as st
import numpy as np
import os
from datetime import date
from fpdf import FPDF

# =================================================================
# ⚙️ 1. KONFIGURĀCIJA
# =================================================================
TECHNICAL_PARAMS = {
    "solar_yield": 1050,      
    "grid_fee_save": 0.045,   
    "bat_cycles": 300,        
    "bat_eff": 0.88,          
    "degradation": 0.005,     
    "elec_inflation": 0.03,
    "nordpool_avg": 0.09,     # Vidējā NordPool cena
    "nordpool_spread": 0.12   # Starpība starp lētāko/dārgāko stundu baterijām
}

PRICING_CONFIG = {
    "small":  {"max_kw": 20, "solar_eur_kw": 700, "bat_eur_kwh": 250},
    "medium": {"max_kw": 50, "solar_eur_kw": 650, "bat_eur_kwh": 220},
    "large":  {"solar_eur_kw": 600, "bat_eur_kwh": 200}
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class EstacijaPDF(FPDF):
    def __init__(self):
        super().__init__()
        reg_path = os.path.join(BASE_DIR, "Roboto-Regular.ttf")
        bold_path = os.path.join(BASE_DIR, "Roboto-Bold.ttf")
        if os.path.exists(reg_path) and os.path.exists(bold_path):
            self.add_font("Roboto", "", reg_path)
            self.add_font("Roboto", "B", bold_path)
            self.font_family_name = "Roboto"
        else: self.font_family_name = "helvetica"

    def header(self):
        logo_path = os.path.join(BASE_DIR, "New_logo1.png")
        if os.path.exists(logo_path): self.image(logo_path, 10, 8, 35)
        self.set_font(self.font_family_name, "B", 14)
        self.cell(0, 10, "TEHNISKI-EKONOMISKAIS PAMATOJUMS", border=0, align="R")
        self.ln(20)

# =================================================================
# 🖥️ 2. UI UN IEVADE
# =================================================================
st.set_page_config(page_title="ESTACIJA NordPool Calc", layout="wide")

with st.sidebar:
    st.header("👤 Klienta dati")
    c_name = st.text_input("Klients", "SIA Uzņēmums")
    c_bill = st.number_input("Mēneša rēķins (€ bez PVN)", value=400.0)
    
    st.divider()
    st.header("⚡ Elektroenerģijas tarifs")
    pricing_type = st.radio("Tarifa veids", ["Fiksēta cena", "Nord Pool (Biržas cena)"])
    
    if pricing_type == "Fiksēta cena":
        c_price = st.number_input("Cena (€/kWh)", value=0.16)
        bat_spread = 0.08 # Mazāks spreads fiksētai cenai (tikai pašpatēriņš)
    else:
        c_price = TECHNICAL_PARAMS["nordpool_avg"]
        bat_spread = TECHNICAL_PARAMS["nordpool_spread"]
        st.info(f"Nord Pool aprēķinā izmantota vidējā cena {c_price} €/kWh un arbitrāžas potenciāls {bat_spread} €/kWh.")

    st.divider()
    st.header("🏦 Finansējums")
    is_loan = st.checkbox("Iekļaut kredītu", value=True)
    loan_rate = 0.019 # 1.9%
    loan_years = 5
    grant_pct = st.slider("Valsts atbalsts (%)", 0, 50, 30) / 100

# Sistēmas konfigurācija
st.subheader("🛠️ Konfigurācija")
col1, col2, col3 = st.columns(3)
with col1:
    scenario = st.selectbox("Modelis", ["Saule + Baterijas", "Tikai Saule", "Tikai Baterijas", "Baterijas esošai Saulei"])
with col2:
    new_kw = st.number_input("Jauna Saule (kW)", value=10.0 if "Saule" in scenario else 0.0)
    exist_kw = st.number_input("Esoša Saule (kW)", value=0.0) if "esošai" in scenario else 0.0
with col3:
    bat_kwh = st.number_input("Baterijas (kWh)", value=20.0 if "Baterija" in scenario or "Baterijas" in scenario else 0.0)

# =================================================================
# 🧮 3. APRĒĶINI (Salīdzinājums)
# =================================================================
# Kopējās izmaksas
tier_kw = new_kw if new_kw > 0 else (bat_kwh / 2)
tier = "small" if tier_kw < 20 else ("medium" if tier_kw < 50 else "large")
total_neto = (new_kw * PRICING_CONFIG[tier]["solar_eur_kw"]) + (bat_kwh * PRICING_CONFIG[tier]["bat_eur_kwh"])
net_invest = total_neto * (1 - grant_pct)

# Kredīts
r = loan_rate / 12
n = loan_years * 12
pmt = net_invest * (r * (1+r)**n) / ((1+r)**n - 1) if is_loan else 0

# IETAUPĪJUMA SALĪDZINĀJUMS
def calc_savings(p_price, p_spread):
    s_save = (new_kw + exist_kw) * 1050 * (p_price + 0.045)
    b_save = bat_kwh * 300 * p_spread * 0.88
    return (s_save + b_save) / 12

m_save_fixed = calc_savings(0.16, 0.08)
m_save_nord = calc_savings(TECHNICAL_PARAMS["nordpool_avg"], TECHNICAL_PARAMS["nordpool_spread"])

current_m_save = m_save_nord if pricing_type == "Nord Pool (Biržas cena)" else m_save_fixed

# =================================================================
# 📊 4. REZULTĀTI
# =================================================================
st.divider()
st.subheader("📈 Ekonomiskais salīdzinājums")

res_col1, res_col2 = st.columns(2)
with res_col1:
    st.markdown("#### Fiksēta cena (0.16 €/kWh)")
    st.write(f"Mēneša ietaupījums: **{m_save_fixed:,.2f} €**")
    st.write(f"Neto Cash-flow: **{m_save_fixed - pmt:,.2f} €/mēn**")

with res_col2:
    st.markdown("#### Nord Pool (Biržas cena)")
    st.write(f"Mēneša ietaupījums: **{m_save_nord:,.2f} €**")
    st.write(f"Neto Cash-flow: **{m_save_nord - pmt:,.2f} €/mēn**")



# --- PDF ĢENERĒŠANA ---
if st.button("Sagatavot PDF ar salīdzinājumu"):
    pdf = EstacijaPDF()
    pdf.add_page()
    pdf.set_font("Roboto", "B", 12)
    pdf.cell(0, 10, f"Klients: {c_name}", ln=True)
    pdf.ln(5)
    
    # Salīdzinājuma tabula PDF failā
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(80, 10, "Parametrs", 1, 0, "L", True)
    pdf.cell(55, 10, "Fiksēts tarifs", 1, 0, "C", True)
    pdf.cell(55, 10, "Nord Pool tarifs", 1, 1, "C", True)
    
    pdf.set_font("Roboto", "", 10)
    pdf.cell(80, 10, "Mēneša ietaupījums", 1)
    pdf.cell(55, 10, f"{m_save_fixed:,.2f} EUR", 1, 0, "C")
    pdf.cell(55, 10, f"{m_save_nord:,.2f} EUR", 1, 1, "C")
    
    pdf.cell(80, 10, "Kredīta maksājums", 1)
    pdf.cell(55, 10, f"{pmt:,.2f} EUR", 1, 0, "C")
    pdf.cell(55, 10, f"{pmt:,.2f} EUR", 1, 1, "C")
    
    pdf.set_font("Roboto", "B", 10)
    pdf.cell(80, 10, "TĪRAIS IEGUVUMS (mēn)", 1)
    pdf.cell(55, 10, f"{m_save_fixed - pmt:,.2f} EUR", 1, 0, "C")
    pdf.cell(55, 10, f"{m_save_nord - pmt:,.2f} EUR", 1, 1, "C")
    
    st.download_button("Lejupielādēt PDF", data=bytes(pdf.output()), file_name="Estacija_NordPool_Compare.pdf")