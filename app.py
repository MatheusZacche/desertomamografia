# -*- coding: utf-8 -*-
"""
Painel interativo — Desertos de Mamografia no SUS
Diagnostico da oferta vs. demanda de mamografia por municipio (CNES, SIA-SUS, IBGE).
Autor: Matheus Zacche Caetano · Orientacao: Profa. Joicce Paiva Tosta · FAESA, 2026
"""
import json
import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).parent / "data"
INK, ROYAL, BRIGHT = "#01053D", "#000494", "#1E55FF"
CLASSES = ["Deserto absoluto", "Deserto funcional", "Intermediario", "Adequado"]
CLASS_COR = {"Deserto absoluto": INK, "Deserto funcional": ROYAL,
             "Intermediario": "#7FA0FF", "Adequado": "#9FC0FF"}
CLASS_LABEL = {"Intermediario": "Intermediário"}

st.set_page_config(page_title="Desertos de Mamografia no SUS",
                   page_icon="🎗️", layout="wide", initial_sidebar_state="collapsed")

# ----------------------------- ESTILO -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&display=swap');
.stApp{background:#EEF1FB;}
.block-container{padding-top:1.4rem;padding-bottom:2.5rem;max-width:1280px;}
[data-testid="stHeader"]{background:transparent;}
#MainMenu,[data-testid="stToolbar"]{visibility:hidden;}
h2,h3,h4{font-family:'Playfair Display',Georgia,serif!important;color:#01053D;}

.hero{background:linear-gradient(120deg,#01053D 0%,#000494 100%);border-radius:22px;
padding:34px 46px;color:#fff;position:relative;overflow:hidden;margin-bottom:22px;}
.hero .eye{font-size:.78rem;letter-spacing:3.5px;text-transform:uppercase;color:#7FA0FF;font-weight:800;}
.hero h1{font-family:'Playfair Display',Georgia,serif;font-size:2.8rem;font-weight:800;
margin:.35rem 0 .5rem;line-height:1.08;}
.hero p{color:#C3CCF2;font-size:1.06rem;max-width:780px;margin:0;line-height:1.5;}
.hero .blob{position:absolute;border-radius:50%;background:#1E55FF;opacity:.22;}

.kpirow{display:flex;gap:18px;margin:2px 0 10px;}
.kpi{flex:1;background:#fff;border-radius:16px;padding:22px 24px;
box-shadow:0 12px 30px rgba(1,5,61,.10);border-left:6px solid #1E55FF;}
.kpi .n{font-family:'Playfair Display',Georgia,serif;font-size:2.45rem;font-weight:700;color:#1E55FF;line-height:1;}
.kpi .l{font-size:.95rem;color:#3a4360;margin-top:9px;font-weight:600;line-height:1.25;}
.kpi .s{font-size:.78rem;color:#9aa3c7;margin-top:3px;}

.stTabs [data-baseweb="tab-list"]{gap:4px;border-bottom:2px solid #DDE3F7;}
.stTabs [data-baseweb="tab"]{font-weight:600;color:#5B6275;font-size:1rem;}
.stTabs [aria-selected="true"]{color:#1E55FF!important;}
.stTabs [data-baseweb="tab-highlight"]{background:#1E55FF;}

[data-testid="stMetric"]{background:#fff;border-radius:14px;padding:14px 18px;
box-shadow:0 8px 22px rgba(1,5,61,.08);}
[data-testid="stMetricValue"]{color:#01053D;font-weight:700;}
[data-testid="stMetricLabel"] p{color:#5B6275;font-weight:600;}

.panel{background:#fff;border-radius:16px;padding:22px 26px;box-shadow:0 12px 30px rgba(1,5,61,.10);}
.munihead{font-family:'Playfair Display',Georgia,serif;font-size:1.7rem;font-weight:700;color:#01053D;}
.badge{display:inline-block;padding:5px 14px;border-radius:999px;font-weight:700;font-size:.9rem;}
.note{font-size:.86rem;color:#7d8aab;font-style:italic;}
.stDataFrame{border-radius:12px;overflow:hidden;}
a{color:#1E55FF;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def carregar():
    df = pd.read_csv(DATA / "indicadores_municipio.csv", dtype={"cod_ibge": str})
    df["municipio_nome"] = df["municipio"].str.replace(r"\s*-\s*[A-Z]{2}$", "", regex=True)
    df["label"] = df["municipio_nome"] + " (" + df["uf"] + ")"
    df["cob_pct"] = (df["cobertura_bienal_total"] * 100).round(1)
    df["ocio_pct"] = (df["taxa_ociosidade"] * 100).round(1)
    df["classe"] = df["classificacao"].replace(CLASS_LABEL)
    return df


@st.cache_data
def carregar_geo():
    return json.loads((DATA / "municipios.geojson").read_text(encoding="utf-8"))


@st.cache_data
def carregar_estados():
    geo = json.loads((DATA / "estados.geojson").read_text(encoding="utf-8"))
    centros = json.loads((DATA / "estados_centros.json").read_text(encoding="utf-8"))
    return geo, centros


@st.cache_data
def agg_uf():
    g = df.groupby("uf").apply(lambda x: pd.Series({
        "cobertura": x["rast_bienio"].sum() / x["pop_feminina_50a69"].sum(),
        "deficit": int(x["deficit_anual"].sum()),
        "sem_n": int((x["mamografos_existentes"] == 0).sum()),
        "municipios": len(x),
        "pop": int(x["pop_feminina_50a69"].sum()),
        "mamografos": int(x["mamografos_em_uso"].sum()),
    }), include_groups=False).reset_index()
    g["cob_pct"] = (g["cobertura"] * 100).round(1)
    g["sem_pct"] = (g["sem_n"] / g["municipios"] * 100).round(0)
    return g


def br(n):
    return f"{int(n):,}".replace(",", ".")


df = carregar()
geo = carregar_geo()
geo_uf, centros = carregar_estados()
df_uf = agg_uf()
N = len(df)
sem = int((df["mamografos_existentes"] == 0).sum())
cob_nac = df["rast_bienio"].sum() / df["pop_feminina_50a69"].sum()
defi = int(df["deficit_anual"].sum())
maq = int(df["mamografos_em_uso"].sum())

# ----------------------------- HERO -----------------------------
st.markdown(f"""
<div class="hero">
  <div class="blob" style="width:340px;height:340px;right:-90px;top:-110px;"></div>
  <div class="blob" style="width:170px;height:170px;right:120px;bottom:-90px;opacity:.16;"></div>
  <div class="eye">Engenharia de Produção · FAESA · 2026</div>
  <h1>Desertos de Mamografia no SUS</h1>
  <p>Onde a oferta do exame está abaixo da necessidade — um diagnóstico por município,
  a partir de dados públicos (CNES, SIA-SUS e Censo 2022/IBGE).</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------- KPIs -----------------------------
st.markdown(f"""
<div class="kpirow">
  <div class="kpi"><div class="n">{br(sem)}</div><div class="l">municípios sem mamógrafo</div><div class="s">{sem/N:.0%} do país</div></div>
  <div class="kpi"><div class="n">{cob_nac:.1%}</div><div class="l">cobertura bienal nacional</div><div class="s">meta: 70%</div></div>
  <div class="kpi"><div class="n">{defi/1e6:.1f} mi</div><div class="l">déficit anual estimado</div><div class="s">exames/ano</div></div>
  <div class="kpi"><div class="n">{br(maq)}</div><div class="l">mamógrafos em uso</div><div class="s">no Brasil</div></div>
</div>
""", unsafe_allow_html=True)

st.write("")
aba_mapa, aba_mun, aba_rank, aba_sobre = st.tabs(
    ["🗺️  Mapa", "🔎  Consulta por município", "📊  Rankings", "ℹ️  Sobre"])

# ----------------------------- Aba Mapa -----------------------------
with aba_mapa:
    uf_sel = st.session_state.get("uf_sel")

    if not uf_sel:
        c1, c2 = st.columns([1.15, 1])
        modo = c1.radio("Colorir os estados por:",
                        ["Cobertura bienal", "% sem mamógrafo"], horizontal=True, key="modo_uf")
        escolha = c2.selectbox("Ou escolha um estado:",
                               [""] + sorted(df["uf"].unique()),
                               format_func=lambda x: "— selecione —" if x == "" else x,
                               key="sel_uf")
        if modo == "Cobertura bienal":
            col, rng, cs = "cob_pct", (0, 70), ["#b91c1c", "#f59e0b", BRIGHT, INK]
        else:
            col, rng, cs = "sem_pct", (0, 100), [INK, BRIGHT, "#f59e0b", "#b91c1c"]
        figu = px.choropleth_mapbox(
            df_uf, geojson=geo_uf, locations="uf", featureidkey="properties.id",
            color=col, color_continuous_scale=cs, range_color=rng,
            mapbox_style="carto-positron", center={"lat": -14.5, "lon": -54},
            zoom=2.95, opacity=0.84, hover_name="uf",
            hover_data={"cob_pct": True, "sem_pct": True, "deficit": ":,.0f", "uf": False},
            labels={"cob_pct": "Cobertura %", "sem_pct": "% s/ máquina", "deficit": "Déficit/ano"})
        figu.update_layout(margin=dict(l=0, r=0, t=6, b=0), height=540,
                           paper_bgcolor="rgba(0,0,0,0)", coloraxis_colorbar_title="")
        ev = st.plotly_chart(figu, on_select="rerun", selection_mode="points",
                             key="ufmap", use_container_width=True)
        clicked = None
        try:
            pts = ev["selection"]["points"]
            if pts:
                clicked = pts[0].get("location")
        except Exception:
            clicked = None
        alvo = clicked or (escolha if escolha else None)
        if alvo:
            st.session_state.uf_sel = alvo
            st.rerun()
        st.markdown('<p class="note">🖱️ Clique em um estado (ou use a caixa) para dar zoom nos '
                    'municípios. Vermelho = pior situação.</p>', unsafe_allow_html=True)
    else:
        ur = df_uf[df_uf["uf"] == uf_sel].iloc[0]
        uf_nome = df[df["uf"] == uf_sel]["uf_nome"].iloc[0]
        a, b = st.columns([1, 4])
        if a.button("← Voltar ao Brasil", use_container_width=True):
            st.session_state.uf_sel = None
            st.rerun()
        b.markdown(f"<div class='munihead' style='font-size:1.4rem'>{uf_nome} ({uf_sel})</div>",
                   unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Cobertura bienal", f"{ur['cob_pct']:.1f}%")
        k2.metric("Municípios s/ mamógrafo", f"{int(ur['sem_n'])} ({ur['sem_pct']:.0f}%)")
        k3.metric("Mamógrafos em uso", br(ur["mamografos"]))
        k4.metric("Déficit/ano", br(ur["deficit"]))
        codes = set(df[df["uf"] == uf_sel]["cod_ibge"])
        sub = {"type": "FeatureCollection",
               "features": [f for f in geo["features"] if str(f["properties"]["id"]) in codes]}
        dsub = df[df["uf"] == uf_sel].assign(
            cob_plot=lambda x: x["cobertura_bienal_total"].clip(upper=1.0) * 100)
        cen = centros.get(uf_sel, {"lat": -14.5, "lon": -54, "span": 6})
        zoom = max(4.2, min(7.4, 8.0 - math.log2(cen["span"] + 0.6)))
        figm = px.choropleth_mapbox(
            dsub, geojson=sub, locations="cod_ibge", featureidkey="properties.id",
            color="cob_plot", color_continuous_scale=["#b91c1c", "#f59e0b", BRIGHT, INK],
            range_color=(0, 70), mapbox_style="carto-positron",
            center={"lat": cen["lat"], "lon": cen["lon"]}, zoom=zoom, opacity=0.82,
            hover_name="label",
            hover_data={"cob_pct": True, "mamografos_em_uso": True,
                        "deficit_anual": ":,.0f", "cod_ibge": False, "cob_plot": False},
            labels={"cob_pct": "Cobertura", "mamografos_em_uso": "Mamógrafos",
                    "deficit_anual": "Déficit/ano"})
        figm.update_layout(margin=dict(l=0, r=0, t=6, b=0), height=520,
                           paper_bgcolor="rgba(0,0,0,0)", coloraxis_colorbar_title="Cobertura %")
        st.plotly_chart(figm, use_container_width=True, key="munimap")
        st.markdown(f'<p class="note">Municípios de {uf_sel} coloridos pela cobertura bienal. '
                    'Cinza = sem polígono na malha.</p>', unsafe_allow_html=True)

# ----------------------- Aba Consulta por municipio -----------------------
with aba_mun:
    sel = st.selectbox("Escolha um município:", df.sort_values("label")["label"].tolist(),
                       index=None, placeholder="Digite o nome do município...")
    if sel:
        r = df[df["label"] == sel].iloc[0]
        cor = {"Deserto absoluto": INK, "Deserto funcional": ROYAL,
               "Intermediário": "#3f74ff", "Adequado": "#2e9e6b"}.get(r["classe"], "#777")
        st.markdown(
            f'<div class="munihead">{r["municipio_nome"]} '
            f'<span style="font-size:1.1rem;color:#5B6275">— {r["uf_nome"]}</span></div>'
            f'<span class="badge" style="background:{cor}1a;color:{cor};margin-top:6px">'
            f'{r["classe"]}</span>', unsafe_allow_html=True)
        st.write("")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Mulheres 50–69", br(r["pop_feminina_50a69"]))
        m2.metric("Mamógrafos (em uso)", f"{int(r['mamografos_existentes'])} ({int(r['mamografos_em_uso'])})")
        m3.metric("Cobertura bienal", f"{r['cob_pct']:.1f}%")
        m4.metric("Déficit anual", br(r["deficit_anual"]))
        n1, n2, n3 = st.columns(3)
        n1.metric("Demanda anual", br(r["demanda_anual"]))
        n2.metric("Ociosidade", "—" if pd.isna(r["taxa_ociosidade"]) else f"{r['ocio_pct']:.0f}%")
        rank_def = int((df["deficit_anual"] > r["deficit_anual"]).sum()) + 1
        n3.metric("Posição nacional em déficit", f"{rank_def}º de {br(N)}")

        anos = list(range(2020, 2026))
        serie = pd.DataFrame({"Ano": anos,
                              "Rastreamento": [int(r[f"rast_{a}"]) for a in anos],
                              "Diagnóstica": [int(r[f"diag_{a}"]) for a in anos]})
        figm = px.bar(serie, x="Ano", y=["Rastreamento", "Diagnóstica"],
                      color_discrete_sequence=[BRIGHT, "#9FB4FF"],
                      title="Mamografias realizadas por ano")
        figm.update_layout(height=300, margin=dict(t=44, b=0, l=0, r=0),
                           legend_title="", yaxis_title="exames",
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(figm, use_container_width=True)
    else:
        st.info("Selecione um município acima para ver o diagnóstico detalhado.")

# ----------------------------- Aba Rankings -----------------------------
with aba_rank:
    st.markdown("#### Os municípios em pior situação")
    cols_show = ["municipio_nome", "uf", "pop_feminina_50a69", "mamografos_existentes",
                 "cob_pct", "deficit_anual", "classe"]
    nomes = {"municipio_nome": "Município", "uf": "UF", "pop_feminina_50a69": "Pop. 50–69",
             "mamografos_existentes": "Mamógrafos", "cob_pct": "Cobertura %",
             "deficit_anual": "Déficit/ano", "classe": "Classe"}
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("**🔴 Maiores desertos absolutos** — sem máquina, por população")
        t = (df[df["mamografos_existentes"] == 0]
             .sort_values("pop_feminina_50a69", ascending=False).head(50)[cols_show])
        st.dataframe(t.rename(columns=nomes), hide_index=True, use_container_width=True, height=430)
    with r2:
        st.markdown("**🟠 Maiores déficits** — demanda não atendida, por ano")
        t = df.sort_values("deficit_anual", ascending=False).head(50)[cols_show]
        st.dataframe(t.rename(columns=nomes), hide_index=True, use_container_width=True, height=430)

# ----------------------------- Aba Sobre -----------------------------
with aba_sobre:
    st.markdown(f"""<div class="panel">

**O que é este painel.** Um diagnóstico, por município, do equilíbrio entre a oferta de
mamografia no SUS e a demanda da população feminina de 50 a 69 anos — a faixa do
rastreamento bienal (Lei nº 11.664/2008).

**Fontes.** **CNES** (mamógrafos, Dez/2025) · **SIA-SUS** (exames por local de atendimento,
2020–2025) · **IBGE / Censo 2022** (população-alvo).

**Parâmetros.** Produtividade de referência de **5.069 exames/ano** por mamógrafo
(INCA/MS, 2015); cobertura calculada sobre o biênio 2024–2025.

**Limitações.** Produção contada por local de atendimento (não de residência); a capacidade
inclui equipamentos privados — o que torna os déficits **conservadores**.

**Validação.** A soma dos {br(N)} municípios reproduz os totais nacionais oficiais das três
bases, sem discrepância.

</div>""", unsafe_allow_html=True)
    st.caption("Matheus Zacche Caetano · Orientação: Profª. Joicce Paiva Tosta · "
               "Engenharia de Produção, FAESA, 2026.")
