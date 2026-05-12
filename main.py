import streamlit as st
import math
from PIL import Image
import os
from fpdf import FPDF
import base64

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gota Perfeita", layout="centered", initial_sidebar_state="collapsed")

# Estilo CSS para Mobile e Interface
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    div[data-testid="stExpander"] { border: 1px solid #ddd; border-radius: 10px; }
    .instrucao-pressao { font-size: 0.85em; color: #555; margin-bottom: -15px; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÃO TÉCNICA DE GOTAS (Ajustado para "OU") ---
objetivos = {
    "Herbicida Hormonal": {"gotas": "Extremamente Grossa ou Ultra Grossa", "cor": "#FFFFFF", "txt": "#000000"},
    "Herbicida": {"gotas": "Média, Grossa ou Muito Grossa", "cor": "#FFFF00", "txt": "#000000"},
    "Inseticida": {"gotas": "Fina ou Média", "cor": "#FF8C00", "txt": "#FFFFFF"},
    "Fungicida": {"gotas": "Muito Fina, Fina ou Média", "cor": "#FF0000", "txt": "#FFFFFF"}
}

class PDF(FPDF):
    def header(self):
        self.set_fill_color(255, 255, 255)
        self.rect(0, 0, 210, 297, 'F') 
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 25)
        self.set_font('helvetica', 'B', 14)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, 'Relatório de Calibração Técnica', 0, 1, 'R')
        self.ln(5)

def gerar_pdf(taxa, vel, esp, vazao, pontas_selecionadas, unidade, objetivo, info_gotas):
    pdf = PDF()
    pdf.add_page()
    
    # Cabeçalho de Parâmetros
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("helvetica", 'B', 11)
    pdf.cell(0, 10, "Parâmetros de Operação", 1, 1, 'L', 1)
    pdf.set_font("helvetica", size=10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 7, f"Objetivo principal da aplicação: {objetivo}", 0, 1)
    pdf.cell(0, 7, f"Alvo de Gotas: {info_gotas}", 0, 1)
    pdf.cell(0, 7, f"Taxa de Aplicação: {taxa} L/ha | Velocidade: {vel} km/h", 0, 1)
    pdf.cell(0, 7, f"Volume/Ponta (Caneca): {vazao:.3f} L/min", 0, 1)
    pdf.ln(5)
    
    pdf.set_font("helvetica", 'B', 11)
    pdf.cell(0, 10, "Sugestões Técnicas de Pontas", 0, 1, 'L')
    pdf.ln(2)

    for i, p in enumerate(pontas_selecionadas):
        pdf.set_fill_color(p['rgb'][0], p['rgb'][1], p['rgb'][2])
        pdf.set_text_color(p['txt_rgb'][0], p['txt_rgb'][1], p['txt_rgb'][2])
        pdf.set_font("helvetica", 'B', 11)
        pdf.cell(0, 10, f" {i+1}ª Opção: {p['nome']}", 1, 1, 'L', 1)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", size=10)
        info = (f"-> Pressão exata para o alvo: {p['pressao']:.2f} {unidade}\n"
                f"-> Janela de Velocidade permitida: {p['v_min']:.1f} a {p['v_max']:.1f} km/h")
        pdf.multi_cell(0, 8, info, 1)
        pdf.ln(3)
    return pdf.output()

def exibir_pdf_iframe(pdf_bytes):
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" style="background-color: white; border-radius: 10px;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- 2. LOGO E TITULO ---
if os.path.exists("logo.png"):
    st.image(Image.open("logo.png"), width=120)

st.title("Calculadora de Aplicação")

# --- 3. INPUTS ---
# Objetivo principal da aplicação (Ajuste de texto conforme solicitado)
obj_selecionado = st.selectbox("🎯 Objetivo principal da aplicação:", list(objetivos.keys()))
info_g = objetivos[obj_selecionado]

st.markdown(f"""
    <div style="background-color: {info_g['cor']}; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #ccc; margin-bottom: 20px;">
        <span style="color: {info_g['txt']}; font-weight: bold;">Gota Requerida: {info_g['gotas']}</span>
    </div>
""", unsafe_allow_html=True)

with st.expander("⚙️ Ajustar Parâmetros", expanded=True):
    v_kmh = st.number_input("Velocidade (km/h)", min_value=0.1, value=8.0, step=0.5)
    taxa_lha = st.number_input("Taxa (L/ha)", min_value=1.0, value=100.0, step=5.0)
    esp_cm = st.number_input("Espaçamento (cm)", min_value=1.0, value=50.0, step=5.0)
    unidade_p = st.selectbox("Unidade de Pressão:", ["psi", "bar", "kPa"])
    
    st.markdown('<p class="instrucao-pressao">Informe a pressão inicial e final de trabalho do modelo da ponta escolhida:</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    defaults = {"psi": (30.0, 60.0), "bar": (2.0, 4.0), "kPa": (200.0, 400.0)}
    p_min_input = c1.number_input(f"P. Mínima", value=defaults[unidade_p][0])
    p_max_input = c2.number_input(f"P. Máxima", value=defaults[unidade_p][1])

# --- 4. CÁLCULO ---
vazao_alvo = (taxa_lha * v_kmh * esp_cm) / 60000
st.metric(label="Volume Coletado (Caneca)", value=f"{vazao_alvo:.3f} L/min")

tabela_iso = {
    "ISO 01 (Laranja)": {"vazao": 0.38, "cor_bg": "#FF8C00", "rgb": (255, 140, 0), "txt_rgb": (255, 255, 255), "cor_txt": "white"},
    "ISO 015 (Verde)": {"vazao": 0.57, "cor_bg": "#32CD32", "rgb": (50, 205, 50), "txt_rgb": (255, 255, 255), "cor_txt": "white"},
    "ISO 02 (Amarelo)": {"vazao": 0.76, "cor_bg": "#FFFF00", "rgb": (255, 255, 0), "txt_rgb": (0, 0, 0), "cor_txt": "black"},
    "ISO 025 (Lilás)": {"vazao": 0.95, "cor_bg": "#DA70D6", "rgb": (218, 112, 214), "txt_rgb": (255, 255, 255), "cor_txt": "white"},
    "ISO 03 (Azul)": {"vazao": 1.14, "cor_bg": "#0000FF", "rgb": (0, 0, 255), "txt_rgb": (255, 255, 255), "cor_txt": "white"},
    "ISO 035 (Vinho)": {"vazao": 1.33, "cor_bg": "#800000", "rgb": (128, 0, 0), "txt_rgb": (255, 255, 255), "cor_txt": "white"},
    "ISO 04 (Vermelho)": {"vazao": 1.52, "cor_bg": "#FF0000", "rgb": (255, 0, 0), "txt_rgb": (255, 255, 255), "cor_txt": "white"},
    "ISO 05 (Marrom)": {"vazao": 1.89, "cor_bg": "#8B4513", "rgb": (139, 69, 19), "txt_rgb": (255, 255, 255), "cor_txt": "white"}
}

pontas_possiveis = []
for nome, dados in tabela_iso.items():
    fator = {"bar": 14.5038, "kPa": 0.145038, "psi": 1.0}[unidade_p]
    v_min_p = dados["vazao"] * math.sqrt((p_min_input * fator) / 40)
    v_max_p = dados["vazao"] * math.sqrt((p_max_input * fator) / 40)
    
    if v_min_p <= vazao_alvo <= v_max_p:
        p_ex_f = (((vazao_alvo / dados["vazao"]) ** 2) * 40) / fator
        pontas_possiveis.append({
            "nome": nome, "pressao": p_ex_f, 
            "v_min": (v_min_p * 60000) / (taxa_lha * esp_cm), 
            "v_max": (v_max_p * 60000) / (taxa_lha * esp_cm),
            "rgb": dados['rgb'], "txt_rgb": dados['txt_rgb'], "cor_bg": dados['cor_bg'], "cor_txt": dados['cor_txt']
        })

# --- 5. RESULTADOS ---
if pontas_possiveis:
    st.subheader("Seleção de Pontas")
    escolhidas = st.multiselect("Defina a ordem do relatório:", [p['nome'] for p in pontas_possiveis], default=[p['nome'] for p in pontas_possiveis])
    pontas_finais = [p for name in escolhidas for p in pontas_possiveis if p['nome'] == name]

    if pontas_finais:
        for i, p in enumerate(pontas_finais):
            st.markdown(f"""
                <div style="background-color: {p['cor_bg']}; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 8px; border: 1px solid #444;">
                    <b style="color: {p['cor_txt']};">{i+1}ª: {p['nome']}</b><br>
                    <span style="color: {p['cor_txt']};">{p['pressao']:.2f} {unidade_p} | {p['v_min']:.1f}-{p['v_max']:.1f} km/h</span>
                </div>
            """, unsafe_allow_html=True)
        
        pdf_raw = gerar_pdf(taxa_lha, v_kmh, esp_cm, vazao_alvo, pontas_finais, unidade_p, obj_selecionado, info_g['gotas'])
        st.divider()
        st.download_button("📥 Baixar Relatório Técnico", data=bytes(pdf_raw), file_name="relatorio_calibracao.pdf", mime="application/pdf")
        with st.expander("👁️ Prévia do Relatório"):
            exibir_pdf_iframe(pdf_raw)
else:
    st.warning("Nenhuma ponta atende aos critérios de vazão e pressão.")