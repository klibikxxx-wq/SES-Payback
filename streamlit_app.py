import streamlit as st
import numpy as np
import os
from datetime import date
from fpdf import FPDF

# =================================================================
# ⚙️ 1. KONFIGURĀCIJA UN CENAS
# =================================================================
TECHNICAL_PARAMS = {
    "solar_yield": 850,      
    "grid_fee_save": 0.045,   
    "bat_cycles": 365,        
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =================================================================
# 📄 2. PDF KLASES DEFINĪCIJA (Ar paplašinātu informāciju)
# =================================================================
class EstacijaPDF(FPDF):
    def __init__(self):
        super().__init__()
        reg_path = os.path.join(BASE_DIR, "Roboto-Regular.ttf")
        bold_path = os.path.join(BASE_DIR, "Roboto-Bold.ttf")
        
        if os.path.exists(reg_path) and os.path.exists(bold_path):
            self.add_font("Roboto", "", reg_path)
            self.add_font("Roboto", "B", bold_path)
            self.font_family_name = "Roboto"
        else:
            self.font_family_name = "helvetica"

    def header(self):
        logo_path = os.path.join(BASE_DIR, "New_logo1.png")
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 35)
        self.set_font(self.font_family_name, "B", 14)
        self.cell(0, 10, "PROJEKTA ROI UN TEHNISKAIS PAMATOJUMS", border=0, align="R")
        self.ln(20)

    def section_title(self, label):
        self.set_font(self.font_family_name, "B", 12)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 10, f" {label}", 0, 1, "L", True)
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family_name, "", 8)
        self.cell(0, 10, f"Lapa {self.page_no()}/{{nb}} | estacija.lv", align="C")

# =================================================================
# 🖥️ 3. STREAMLIT LIETOTNES SASKARNE
# =================================================================
st.set_page_config(page_title="ESTACIJA Piedāvājumu Sistēma", layout="wide")

logo_ui = os.path.join(BASE_DIR, "New_logo1.png")
if os.path.exists(logo_ui):
    st.image(logo_ui, width=200)

st.title("Piedāvājuma un ROI Aprēķinu Sistēma")

with st.sidebar:
    st.header("👤 Klienta dati")
    c_name = st.text_input("Klients", "SIA Klienta Uzņēmums")
    c_addr = st.text_input("Adrese", "Rīga, Latvija")
    c_bill = st.number_input("Esošais mēneša rēķins (€ bez PVN)", value=300.0)
    c_price_kwh = st.number_input("Elektrības cena (€/kWh)", value=0.16, step=0.01)
    
    st.divider()
    st.header("🏦 Finansējums")
    is_loan = st.checkbox("Iekļaut kredītu", value=True)
    loan_rate = st.slider("Likme (%)", 1.9, 12.0, 1.9) / 100
    loan_years = st.select_slider("Termiņš (Gadi)", options=list(range(1, 11)), value=5)
    grant_pct = st.slider("Valsts atbalsts (%)", 0, 50, 30) / 100

st.subheader("🛠️ Sistēmas Konfigurācija")
col1, col2, col3 = st.columns(3)

with col1:
    scenario = st.selectbox("Izvēlētais modelis", [
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
# 🧮 4. APRĒĶINU LOĢIKA
# =================================================================
calc_tier_kw = new_kw if new_kw > 0 else (bat_kwh / 2)
if calc_tier_kw < PRICING_CONFIG["small"]["max_kw"]: tier = "small"
elif calc_tier_kw < PRICING_CONFIG["medium"]["max_kw"]: tier = "medium"
else: tier = "large"

s_u = PRICING_CONFIG[tier]["solar_eur_kw"]
b_u = PRICING_CONFIG[tier]["bat_eur_kwh"]

inv_s = new_kw * s_u
inv_b = bat_kwh * b_u
total_neto = inv_s + inv_b
grant_val = total_neto * grant_pct
net_invest = total_neto - grant_val

# Detalizēts ietaupījums
solar_gen_ann = (new_kw + exist_kw) * TECHNICAL_PARAMS["solar_yield"]
solar_save_ann = solar_gen_ann * (c_price_kwh + TECHNICAL_PARAMS["grid_fee_save"])
bat_save_ann = bat_kwh * TECHNICAL_PARAMS["bat_cycles"] * TECHNICAL_PARAMS["arb_spread"] * TECHNICAL_PARAMS["bat_eff"]
total_save_ann = solar_save_ann + bat_save_ann
monthly_save = total_save_ann / 12

pmt = 0
if is_loan and net_invest > 0:
    r = loan_rate / 12
    n = loan_years * 12
    pmt = net_invest * (r * (1+r)**n) / ((1+r)**n - 1)

# =================================================================
# 📊 5. REZULTĀTI UN PDF ĢENERĒŠANA
# =================================================================
t1, t2 = st.tabs(["📋 Piedāvājuma kopsavilkums", "📈 ROI Grafiks"])

with t1:
    st.success(f"**Tīrais mēneša Cash-flow: {monthly_save - pmt:,.2f} €**")
    
    def generate_detailed_pdf():
        pdf = EstacijaPDF()
        pdf.add_page()
        
        # 1. Klienta un Ievades dati
        pdf.section_title("1. KLIENTA UN ENERĢIJAS DATI")
        pdf.set_font(pdf.font_family_name, "", 10)
        pdf.cell(100, 7, f"Klients: {c_name}")
        pdf.cell(0, 7, f"Esošais rēķins: {c_bill:,.2f} EUR/mēn", ln=True)
        pdf.cell(100, 7, f"Adrese: {c_addr}")
        pdf.cell(0, 7, f"Elektrības cena: {c_price_kwh} EUR/kWh", ln=True)
        pdf.ln(5)

        # 2. Tehniskie pieņēmumi
        pdf.section_title("2. TEHNISKIE PIEŅĒMUMI")
        pdf.set_font(pdf.font_family_name, "", 9)
        pdf.cell(95, 6, f"- Saules ražība: {TECHNICAL_PARAMS['solar_yield']} kWh/kWp gadā")
        pdf.cell(0, 6, f"- Sadales tīkla ietaupījums: {TECHNICAL_PARAMS['grid_fee_save']} EUR/kWh", ln=True)
        pdf.cell(95, 6, f"- Bateriju cikli: {TECHNICAL_PARAMS['bat_cycles']} reizes gadā")
        pdf.cell(0, 6, f"- Arbitrāžas peļņa: {TECHNICAL_PARAMS['arb_spread']} EUR/kWh", ln=True)
        pdf.cell(95, 6, f"- Bateriju lietderība: {TECHNICAL_PARAMS['bat_eff']*100}%")
        pdf.cell(0, 6, f"- Sistēmas nolietojums: {TECHNICAL_PARAMS['degradation']*100}% gadā", ln=True)
        pdf.ln(5)

        # 3. Sistēmas specifikācija un Izmaksas
        pdf.section_title("3. SISTĒMAS SPECIFIKĀCIJA UN INVESTĪCIJA")
        pdf.set_font(pdf.font_family_name, "B", 10)
        pdf.cell(90, 8, "Pozīcija", 1, 0, "L")
        pdf.cell(30, 8, "Daudzums", 1, 0, "C")
        pdf.cell(35, 8, "Vien. cena", 1, 0, "C")
        pdf.cell(35, 8, "Summa", 1, 1, "C")
        
        pdf.set_font(pdf.font_family_name, "", 10)
        if new_kw > 0:
            pdf.cell(90, 8, "Saules paneļu sistēma", 1)
            pdf.cell(30, 8, f"{new_kw} kW", 1, 0, "C")
            pdf.cell(35, 8, f"{s_u} EUR", 1, 0, "C")
            pdf.cell(35, 8, f"{inv_s:,.2f} EUR", 1, 1, "C")
        if bat_kwh > 0:
            pdf.cell(90, 8, "Bateriju krātuve", 1)
            pdf.cell(30, 8, f"{bat_kwh} kWh", 1, 0, "C")
            pdf.cell(35, 8, f"{b_u} EUR", 1, 0, "C")
            pdf.cell(35, 8, f"{inv_b:,.2f} EUR", 1, 1, "C")
        
        pdf.ln(2)
        pdf.set_font(pdf.font_family_name, "B", 10)
        pdf.cell(155, 8, "KOPĀ NETO:", 0, 0, "R")
        pdf.cell(35, 8, f"{total_neto:,.2f} EUR", 0, 1, "R")
        pdf.cell(155, 8, f"Valsts atbalsts ({int(grant_pct*100)}%):", 0, 0, "R")
        pdf.cell(35, 8, f"-{grant_val:,.2f} EUR", 0, 1, "R")
        pdf.cell(155, 8, "GALA INVESTĪCIJA:", 0, 0, "R")
        pdf.cell(35, 8, f"{net_invest:,.2f} EUR", 0, 1, "R")
        pdf.ln(5)

        # 4. ROI Aprēķins
        pdf.section_title("4. FINANŠU IEGUVUMA APRĒĶINS")
        pdf.set_font(pdf.font_family_name, "", 10)
        pdf.cell(0, 7, f"- Plānotā saules ražošana gadā: {solar_gen_ann:,.0f} kWh", ln=True)
        pdf.cell(0, 7, f"- Saules radītais ietaupījums: {solar_save_ann:,.2f} EUR/gadā", ln=True)
        pdf.cell(0, 7, f"- Bateriju arbitrāžas ieguvums: {bat_save_ann:,.2f} EUR/gadā", ln=True)
        pdf.set_font(pdf.font_family_name, "B", 10)
        pdf.cell(0, 10, f"KOPĒJAIS IETAUPĪJUMS 1. GADĀ: {total_save_ann:,.2f} EUR ({monthly_save:,.2f} EUR/mēn)", ln=True)
        
        if is_loan:
            pdf.ln(2)
            pdf.cell(0, 7, "FINANSĒJUMA MODELIS (KREDĪTS):", ln=True)
            pdf.set_font(pdf.font_family_name, "", 10)
            pdf.cell(0, 6, f"- Kredīta summa: {net_invest:,.2f} EUR", ln=True)
            pdf.cell(0, 6, f"- Procentu likme: {loan_rate*100}% | Termiņš: {loan_years} gadi", ln=True)
            pdf.cell(0, 6, f"- Ikmēneša maksājums: {pmt:,.2f} EUR", ln=True)
            pdf.set_font(pdf.font_family_name, "B", 10)
            pdf.cell(0, 10, f"TĪRAIS MĒNEŠA IEGUVUMS (Cash-flow): {monthly_save - pmt:,.2f} EUR", ln=True)

        return pdf.output()

    if st.button("Sagatavot pilno PDF atskaiti"):
        pdf_bytes = generate_detailed_pdf()
        st.download_button(
            label="📥 Lejupielādēt detalizētu PDF",
            data=bytes(pdf_bytes),
            file_name=f"ESTACIJA_Pamatojums_{c_name.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

with t2:
    # ROI Grafika loģika (Kā iepriekšējā kodā)
    years = np.arange(21)
    history = []
    curr_bal = -net_invest if not is_loan else 0
    for y in years:
        if y > 0:
            y_save = (total_save_ann) * ((1 + TECHNICAL_PARAMS["elec_inflation"])**y) * ((1 - TECHNICAL_PARAMS["degradation"])**y)
            y_loan = (pmt * 12) if (is_loan and y <= loan_years) else 0
            curr_bal += (y_save - y_loan)
        history.append(curr_bal)
    st.area_chart(history)