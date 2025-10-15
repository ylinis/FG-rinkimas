# app.py

import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- Programos Konfigūracija ---
st.set_page_config(
    page_title="FG Duomenų Suvestinė",
    layout="wide"
)

st.title("📈 Fear & Greed Indeksų Duomenų Suvestinė")
st.markdown("Rankinis CNN ir Crypto F&G indeksų suvedimas su nuolatiniu išsaugojimu.")

# --- Duomenų Failo Kelias ---
DATA_FILE = "fg_data.csv"

# --- Duomenų Užkrovimo Funkcija ---
def load_data():
    """Užkrauna duomenis iš CSV failo arba sukuria tuščią DataFrame."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, parse_dates=['Data'])
        # Konvertuojame į Int64, kad palaikytų tuščias reikšmes (NaN)
        df['CNN FG'] = df['CNN FG'].astype('Int64')
        df['Crypto FG'] = df['Crypto FG'].astype('Int64')
        return df.set_index('Data')
    else:
        # Jei failo nėra, sukuriame tuščią struktūrą
        return pd.DataFrame({
            'Data': pd.to_datetime([]),
            'CNN FG': pd.Series([], dtype='Int64'),
            'Crypto FG': pd.Series([], dtype='Int64')
        }).set_index('Data')

# --- Duomenų Išsaugojimo Funkcija ---
def save_data(df):
    """Išsaugo DataFrame į CSV failą."""
    df_to_save = df.reset_index()
    df_to_save.to_csv(DATA_FILE, index=False)

# --- Duomenų Būsenos Inicializavimas ---
# Užkrauname duomenis tik vieną kartą per sesiją
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
                st.success(f"Įrašas pridėtas. Paspauskite 'Išsaugoti pakeitimus', kad išsaugotumėte.")
                st.rerun() # Iškart atnaujiname pagrindinę lentelę

# --- PAGRINDINIS LANGAS: Duomenų Redagavimas ir Išsaugojimas ---
st.header("✍️ Redaguoti duomenis")

if st.session_state.fg_data.empty:
    st.info("Kol kas nėra jokių duomenų. Pridėkite naują įrašą šoninėje juostoje.")
else:
    # `st.data_editor` grąžina pakeistą DataFrame, kurį laikinai išsaugome
    redaguoti_duomenys = st.data_editor(
        st.session_state.fg_data,
        use_container_width=True,
        num_rows="dynamic"
    )
    
    # Rodyti išsaugojimo mygtuką tik jei yra pakeitimų
    if not redaguoti_duomenys.equals(st.session_state.fg_data):
        st.warning("⚠️ Jūs atlikote pakeitimų. Paspauskite mygtuką, kad juos išsaugotumėte.")
        if st.button("💾 Išsaugoti pakeitimus", type="primary", use_container_width=True):
            save_data(redaguoti_duomenys)
            st.session_state.fg_data = redaguoti_duomenys # Atnaujiname pagrindinę būseną
            st.success("✅ Pakeitimai sėkmingai išsaugoti!")
            st.rerun()
    
    # --- CSV Atsisiuntimo Mygtukas ---
    st.header("📥 Atsisiųsti CSV")
    # Visada siūlome atsisiųsti naujausią, išsaugotą versiją
    csv_df = st.session_state.fg_data.reset_index()
    csv_df['Data'] = csv_df['Data'].dt.strftime('%Y-%m-%d')
    csv_failas = csv_df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
       label="Atsisiųsti išsaugotus duomenis kaip CSV",
       data=csv_failas,
       file_name=f"fg_indeksai_{datetime.now().strftime('%Y-%m-%d')}.csv",
       mime='text/csv',
       use_container_width=True
    )
