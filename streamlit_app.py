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

st.set_page_config(page_title="ESTACIJA Piedāvājums & ROI", page_icon="📄", layout="wide")

# --- LOGO ---
st.image("New_logo1.png", width=250)
st.title("Piedāvājuma un ROI Ģenerators")

# --- 1. IEVADES SADAĻA ---
with st.sidebar:
    st.header("👤 Klienta Informācija")
    cust_name = st.text_input("Klients", "SIA Uzņēmums")
    cust_addr = st.text_input("Adrese", "Rīga, Latvija")
    offer_no = st.text_input("Piedāvājuma Nr.", "2026-OFF-001")
    elec_price = st.number_input("Elektrības cena (€/kWh)", value=0.16, step=0.01)
    grant_pct = st.slider("Valsts atbalsts (%) jaunajām iekārtām", 0, 50, 30) / 100

st.subheader("🛠️ Sistēmas konfigurācija")
col_sys1, col_sys2 = st.columns(2)

with col_sys1:
    sys_mode = st.selectbox(
        "Izvēlieties scenāriju",
        ["Saules paneļi + Baterijas", "Tikai Saules paneļi", "Tikai Baterijas", "Bateriju pievienošana esošai sistēmai"]
    )

# Dinamiskie mainīgie
new_solar_kw = 0.0
exist_solar_kw = 0.0
battery_kwh = 0.0

with col_sys2:
    if sys_mode == "Saules paneļi + Baterijas":
        new_solar_kw = st.number_input("Jaunā Saules jauda (kW)", min_value=0.0, value=10.0)
        battery_kwh = st.number_input("Bateriju ietilpība (kWh)", min_value=0.0, value=20.0)
    elif sys_mode == "Tikai Saules paneļi":
        new_solar_kw = st.number_input("Jaunā Saules jauda (kW)", min_value=0.0, value=10.0)
    elif sys_mode == "Tikai Baterijas":
        battery_kwh = st.number_input("Bateriju ietilpība (kWh)", min_value=0.0, value=20.0)
    elif sys_mode == "Bateriju pievienošana esošai sistēmai":
        exist_solar_kw = st.number_input("Esošā Saules jauda (kW)", min_value=0.0, value=10.0)
        battery_kwh = st.number_input("Bateriju ietilpība (kWh)", min_value=0.0, value=20.0)

# --- 2. APRĒĶINI ---
# Cenu noteikšana (bāzēta uz jauno komponentu apjomu)
tier_check = new_solar_kw if new_solar_kw > 0 else (battery_kwh / 2)
if tier_check < PRICING_CONFIG["small"]["max_kw"]: tier = "small"
elif tier_check < PRICING_CONFIG["medium"]["max_kw"]: tier = "medium"
else: tier = "large"

s_unit = PRICING_CONFIG[tier]["solar_eur_kw"]
b_unit = PRICING_CONFIG[tier]["bat_eur_kwh"]

inv_solar = new_solar_kw * s_unit
inv_battery = battery_kwh * b_unit
total_invest_neto = inv_solar + inv_battery
grant_val = total_invest_neto * grant_pct
final_invest = total_invest_neto - grant_val

# Ietaupījumu loģika (iekļaujot esošo sauli)
total_solar_kw = new_solar_kw + exist_solar_kw
ann_save_solar = (total_solar_kw * TECHNICAL_PARAMS["solar_yield"]) * (elec_price + TECHNICAL_PARAMS["grid_fee_save"])
ann_save_arb = (battery_kwh * TECHNICAL_PARAMS["bat_cycles"] * TECHNICAL_PARAMS["arb_spread"] * TECHNICAL_PARAMS["bat_eff"])
total_ann_save = ann_save_solar + ann_save_arb

# --- 3. REZULTĀTU CILNES ---
tab_offer, tab_roi = st.tabs(["📄 Piedāvājums", "📈 ROI Analīze"])

with tab_offer:
    st.markdown(f"### PIEDĀVĀJUMS: {cust_name} | {offer_no}")
    st.write(f"**Datums:** {date.today().strftime('%d.%m.%Y')} | **Objekts:** {cust_addr}")
    
    # Piedāvājuma tabula
    offer_items = []
    if new_solar_kw > 0:
        offer_items.append({"Pozīcija": "Saules paneļu sistēma", "Apjoms": f"{new_solar_kw} kW", "Cena": f"{s_unit} €", "Summa": f"{inv_solar:,.2f} €"})
    if battery_kwh > 0:
        offer_items.append({"Pozīcija": "Akumulatoru krātuve", "Apjoms": f"{battery_kwh} kWh", "Cena": f"{b_unit} €", "Summa": f"{inv_battery:,.2f} €"})
    
    st.table(offer_items)
    
    c_inv1, c_inv2 = st.columns(2)
    with c_inv1:
        st.write(f"**Kopā Neto:** {total_invest_neto:,.2f} €")
        st.write(f"**Valsts atbalsts ({int(grant_pct*100)}%):** -{grant_val:,.2f} €")
    with c_inv2:
        st.subheader(f"GALA INVESTĪCIJA: {final_invest:,.2f} €")

with tab_roi:
    st.subheader("Investīcijas atmaksāšanās grafiks")
    
    # Simulācija 20 gadiem
    years = np.arange(21)
    cash_flow = []
    current_bal = -final_invest
    
    for y in years:
        if y > 0:
            # Ietaupījums pieaug ar inflāciju, jauda krīt ar degradāciju
            y_save = total_ann_save * ((1 + TECHNICAL_PARAMS["elec_inflation"])**y) * ((1 - TECHNICAL_PARAMS["degradation"])**y)
            current_bal += y_save
        cash_flow.append(current_bal)
    
    st.area_chart(cash_flow)
    
    
    r_col1, r_col2 = st.columns(2)
    payback = final_invest / total_ann_save if total_ann_save > 0 else 0
    r_col1.metric("Atmaksāšanās periods", f"{payback:.1f} Gadi")
    r_col2.metric("20 gadu tīrā peļņa", f"{cash_flow[-1]:,.0f} €")

    if exist_solar_kw > 0:
        st.caption(f"ℹ️ Aprēķinā iekļauta esošā parka ({exist_solar_kw} kW) saražotā enerģija, kas palīdz ātrāk atpelnīt jauno bateriju investīciju.")

st.markdown("---")
st.caption("Piedāvājums sagatavots ESTACIJA sistēmā. Šis ir provizorisks aprēķins.")