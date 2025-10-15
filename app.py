# app.py

import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- Programos Konfigūracija ---
st.set_page_config(
    page_title="FG Duomenų Suvestinė",
    layout="wide"
)

st.title("📈 Fear & Greed Indeksų Duomenų Suvestinė (su Google Sheets)")
st.markdown("Rankinis CNN ir Crypto F&G indeksų suvedimas su nuolatiniu išsaugojimu.")

# --- Prisijungimas prie Google Sheets ---
conn = st.connection("gcs", type=GSheetsConnection)

# --- Duomenų Užkrovimo Funkcija ---
def load_data():
    """Užkrauna duomenis iš Google Sheets."""
    df = conn.read(usecols=[0, 1, 2], ttl="5s")
    df.dropna(how="all", inplace=True)
    df['Data'] = pd.to_datetime(df['Data'])
    df['CNN FG'] = pd.to_numeric(df['CNN FG'], errors='coerce').astype('Int64')
    df['Crypto FG'] = pd.to_numeric(df['Crypto FG'], errors='coerce').astype('Int64')
    return df.set_index('Data')

# --- Duomenų Būsenos Inicializavimas ---
if 'fg_data' not in st.session_state:
    st.session_state.fg_data = load_data()

# --- ŠONINĖ JUOSTA: Naujų Duomenų Įvedimas ---
with st.sidebar:
    st.header("➕ Pridėti naują įrašą")
    with st.form("new_entry_form", clear_on_submit=True):
        ivesta_data = st.date_input("Pasirinkite datą", value=datetime.now())
        cnn_fg = st.number_input("CNN F&G Reikšmė", min_value=0, max_value=100, step=1, value=None)
        crypto_fg = st.number_input("Crypto F&G Reikšmė", min_value=0, max_value=100, step=1, value=None)
        submitted = st.form_submit_button("Pridėti")

        if submitted:
            pd_data = pd.to_datetime(ivesta_data)
            if pd_data in st.session_state.fg_data.index:
                st.warning(f"Įrašas datai {ivesta_data.strftime('%Y-%m-%d')} jau egzistuoja.")
            else:
                naujas_irasas = pd.DataFrame({
                    'CNN FG': [cnn_fg],
                    'Crypto FG': [crypto_fg]
                }, index=[pd_data])
                st.session_state.fg_data = pd.concat([st.session_state.fg_data, naujas_irasas])
                st.session_state.fg_data.sort_index(ascending=False, inplace=True)
                st.success("Įrašas pridėtas. Paspauskite 'Išsaugoti pakeitimus'.")
                st.rerun()

# --- PAGRINDINIS LANGAS: Duomenų Redagavimas ir Išsaugojimas ---
st.header("✍️ Redaguoti duomenis")

if st.session_state.fg_data.empty:
    st.info("Kol kas nėra jokių duomenų.")
else:
    redaguoti_duomenys = st.data_editor(
        st.session_state.fg_data,
        use_container_width=True,
        num_rows="dynamic"
    )
    
    if not redaguoti_duomenys.equals(st.session_state.fg_data):
        st.warning("⚠️ Jūs atlikote pakeitimų. Paspauskite mygtuką, kad juos išsaugotumėte.")
        if st.button("💾 Išsaugoti pakeitimus į Google Sheets", type="primary", use_container_width=True):
            df_to_save = redaguoti_duomenys.reset_index()
            # Prieš išsaugant, nurodome lapo pavadinimą. Įsitikinkite, kad jis teisingas!
            conn.update(worksheet="Pirmas lapas", data=df_to_save) 
            st.session_state.fg_data = redaguoti_duomenys
            st.success("✅ Pakeitimai sėkmingai išsaugoti!")
            st.rerun()

# --- CSV Atsisiuntimo Mygtukas ---
st.header("📥 Atsisiųsti CSV")
if not st.session_state.fg_data.empty:
    # Sukuriame kopiją, kad nepakeistume originalių duomenų
    df_to_download = st.session_state.fg_data.copy()
    
    # PATAISYMAS: Užtikriname, kad indekso pavadinimas yra teisingas
    df_to_download.index.name = 'Data'
    
    csv_df = df_to_download.reset_index()
    csv_df['Data'] = csv_df['Data'].dt.strftime('%Y-%m-%d')
    csv_failas = csv_df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
       label="Atsisiųsti išsaugotus duomenis kaip CSV",
       data=csv_failas,
       file_name=f"fg_indeksai_{datetime.now().strftime('%Y-%m-%d')}.csv",
       mime='text/csv',
       use_container_width=True # Ateityje pakeiskite į width='stretch'
    )
