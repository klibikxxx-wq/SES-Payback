import streamlit as st
from datetime import date

# =================================================================
# ⚙️ IEKŠĒJIE CENU PARAMETRI (Tādi paši kā ROI kalkulatorā)
# =================================================================
PRICING_CONFIG = {
    "small":  {"max_kw": 20, "solar_eur_kw": 700, "bat_eur_kwh": 250},
    "medium": {"max_kw": 50, "solar_eur_kw": 650, "bat_eur_kwh": 220},
    "large":  {"solar_eur_kw": 600, "bat_eur_kwh": 200}
}

st.set_page_config(page_title="ESTACIJA Piedāvājumu Ģenerators", page_icon="📄", layout="centered")

# --- LOGO UN VIRSRAKSTS ---
st.image("New_logo1.png", width=250)
st.title("Piedāvājuma Ģenerators")
st.markdown("---")

# --- 1. KLIENTA INFORMĀCIJA ---
with st.sidebar:
    st.header("👤 Klienta dati")
    cust_name = st.text_input("Uzņēmuma nosaukums", "SIA Klienta Uzņēmums")
    cust_addr = st.text_input("Objekta adrese", "Rīga, Latvija")
    offer_no = st.text_input("Piedāvājuma Nr.", "2026-001")
    offer_date = date.today().strftime("%d.%m.%Y")

# --- 2. SISTĒMAS KONFIGURĀCIJA ---
st.subheader("🛠️ Sistēmas parametri")
col1, col2 = st.columns(2)

with col1:
    sys_type = st.selectbox(
        "Sistēmas veids",
        ["Saules paneļi + Baterijas", "Tikai Saules paneļi", "Tikai Baterijas", "Bateriju pievienošana esošai sistēmai"]
    )

with col2:
    grant_pct = st.slider("Valsts atbalsts (%)", 0, 50, 30) / 100

# Dinamiski rādīt ievades laukus atkarībā no izvēles
solar_kw = 0.0
battery_kwh = 0.0

c1, c2 = st.columns(2)
if "Saules" in sys_type:
    with c1:
        solar_kw = st.number_input("Saules sistēmas jauda (kW)", min_value=0.0, value=10.0, step=0.1)
if "Baterija" in sys_type or "Bateriju" in sys_type:
    with c2:
        battery_kwh = st.number_input("Bateriju ietilpība (kWh)", min_value=0.0, value=20.0, step=0.1)

# --- 3. CENU APRĒĶINS ---
# Noteikt cenu līmeni (tier) bāzējoties uz lielāko komponenti
check_kw = solar_kw if solar_kw > 0 else (battery_kwh / 2)

if check_kw < PRICING_CONFIG["small"]["max_kw"]:
    tier = "small"
elif check_kw < PRICING_CONFIG["medium"]["max_kw"]:
    tier = "medium"
else:
    tier = "large"

s_price_unit = PRICING_CONFIG[tier]["solar_eur_kw"]
b_price_unit = PRICING_CONFIG[tier]["bat_eur_kwh"]

solar_total = solar_kw * s_price_unit
battery_total = battery_kwh * b_price_unit
total_neto = solar_total + battery_total
grant_amount = total_neto * grant_pct
final_total = total_neto - grant_amount

# --- 4. OFICIĀLĀ PIEDĀVĀJUMA SKATS ---
st.markdown("---")
st.markdown(f"""
### 📄 PIEDĀVĀJUMS Nr. {offer_no}
**Datums:** {offer_date}  
**Klients:** {cust_name}  
**Objekts:** {cust_addr}
""")

# Tabula ar pozīcijām
st.markdown(f"""
| Pozīcija | Apraksts | Daudzums | Cena (vien.) | Summa |
| :--- | :--- | :--- | :--- | :--- |
| **Saules paneļu sistēma** | Pilns komplekts ar uzstādīšanu | {solar_kw} kW | {s_price_unit} € | {solar_total:,.2f} € |
| **Akumulatoru krātuve** | Litija-dzelzs-fosfāta (LFP) BESS | {battery_kwh} kWh | {b_price_unit} € | {battery_total:,.2f} € |
| | | | | |
| **KOPĀ NETO** | | | | **{total_neto:,.2f} €** |
| **Valsts atbalsts** | lēstais ({int(grant_pct*100)}%) | | | -{grant_amount:,.2f} € |
| --- | --- | --- | --- | --- |
| **GALA INVESTĪCIJA** | | | | **{final_total:,.2f} €** |
""")

st.info("**Piedāvājumā iekļauts:** Iekārtas, montāžas darbi, dokumentācijas sakārtošana un sistēmas nodošana ekspluatācijā.")

# --- 5. RĪCĪBAS POGA ---
if st.button("Ģenerēt PDF / Printēt"):
    st.write("💡 *Padoms: Izmanto Ctrl+P (vai Cmd+P) savā pārlūkā un saglabā kā PDF.*")

# --- PAPILDUS: ROI ATSAUCE ---
with st.expander("📈 Provizoriskais ieguvums"):
    st.write(f"Šī sistēma saražos aptuveni **{solar_kw * 1050:,.0f} kWh** gadā.")
    st.write(f"Baterijas palīdzēs ietaupīt papildus, veicot enerģijas arbitrāžu un nodrošinot pašpatēriņu.")