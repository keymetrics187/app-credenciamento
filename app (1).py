import streamlit as st
import pandas as pd
import gspread
import streamlit.components.v1 as components
import json
from oauth2client.service_account import ServiceAccountCredentials

def carregar_dados():
    sheet_id = "1ZsHsE0OVq9v_gHiYuSkkkXv6IElW0QA6zpD3eBUQNs0"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    df = pd.read_csv(url)
    return df

def atualizar_checkin_google(nome, checkin_status):
    creds_dict = json.loads(st.secrets["google"]["credentials"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gc = gspread.authorize(credentials)

    sh = gc.open_by_key('1ZsHsE0OVq9v_gHiYuSkkkXv6IElW0QA6zpD3eBUQNs0')
    worksheet = sh.worksheet('Página1')
    lista_nomes = worksheet.col_values(1)
    for idx, nome_planilha in enumerate(lista_nomes):
        if nome_planilha.strip().lower() == nome.strip().lower():
            worksheet.update_cell(idx + 1, 4, checkin_status)
            break

def leitor_qr_html():
    html_code = '''
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <div id="reader" style="width:100%"></div>
    <div id="qr_debug" style="margin-top:10px; font-weight: bold;"></div>
    <script>
        function onScanSuccess(decodedText, decodedResult) {
            document.getElementById("qr_debug").innerText = "QR Capturado: " + decodedText;
            window.location.href = window.location.href.split("?")[0] + "?qr_code=" + encodeURIComponent(decodedText);
        }

        var html5QrcodeScanner = new Html5QrcodeScanner(
            "reader",
            {
                fps: 10,
                qrbox: 250,
                rememberLastUsedCamera: true,
                facingMode: { exact: "environment" }
            },
            false
        );
        html5QrcodeScanner.render(onScanSuccess);
    </script>
    '''
    components.html(html_code, height=500)

st.set_page_config(page_title="Controle de Credenciamento", layout="centered")
st.title('Controle de Credenciamento (modo debug)')

if "df_participantes" not in st.session_state:
    st.session_state.df_participantes = carregar_dados()
if "mostrar_scanner" not in st.session_state:
    st.session_state.mostrar_scanner = False

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("📷 Abrir Scanner"):
        st.session_state.mostrar_scanner = True
        st.rerun()
with col2:
    if st.button("❌ Fechar Scanner"):
        st.session_state.mostrar_scanner = False
        st.rerun()

if st.session_state.mostrar_scanner:
    leitor_qr_html()

qr_code = st.query_params.get("qr_code", [None])[0]

if qr_code:
    st.code(qr_code, language='text')
    st.info(f"QR Lido: `{qr_code}`")
    df = st.session_state.df_participantes
    st.subheader("🔍 Comparando QR com cada linha da planilha:")
    match_found = False

    for idx, row in df.iterrows():
        valor_planilha = str(row['eTicket']).strip()
        comparado = qr_code.strip()
        if valor_planilha == comparado:
            st.success(f"✅ Linha {idx}: BATEU com {valor_planilha}")
            nome = row['Nome']
            st.session_state.df_participantes.loc[idx, 'Checkin'] = 'Sim'
            atualizar_checkin_google(nome, 'Sim')
            st.success(f"Check-in realizado para {nome}")
            match_found = True
            break
        else:
            st.warning(f"❌ Linha {idx}: {valor_planilha} ≠ {comparado}")

    if not match_found:
        st.error("⚠️ Nenhuma correspondência encontrada com o QR escaneado.")

    st.session_state.mostrar_scanner = False
    st.experimental_set_query_params()
    st.stop()

# (O resto do app continua igual...)