# -*- coding: utf-8 -*-
"""
Painel interativo — Desertos de Mamografia no SUS
Diagnostico da oferta vs. demanda de mamografia por municipio (CNES, SIA-SUS, IBGE).
Autor: Matheus Zacche Caetano · Orientacao: Profa. Joicce Paiva Tosta · FAESA, 2026
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).parent / "data"
INK, ROYAL, BRIGHT = "#01053D", "#000494", "#1E55FF"
CLASSES = ["Deserto absoluto", "Deserto funcional", "Intermediario", "Adequado"]
CLASS_COR = {"Deserto absoluto": INK, "Deserto funcional": ROYAL,
             "Intermediario": "#7FA0FF", "Adequado": "#Bcc"}
CLASS_COR["Adequado"] = "#9FC0FF"
CLASS_LABEL = {"Intermediario": "Intermediário"}

st.set_page_config(page_title="Desertos de Mamografia no SUS",
                   page_icon="🎗️", layout="wide")


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


df = carregar()
geo = carregar_geo()
N = len(df)

# ----------------------------- Cabecalho -----------------------------
st.markdown(
    f"<h1 style='color:{INK};margin-bottom:0'>Desertos de Mamografia no SUS</h1>"
    "<p style='color:#5B6275;font-size:1.05rem;margin-top:.2rem'>"
    "Diagnóstico da oferta de mamografia frente à demanda populacional, "
    "por município — a partir de CNES, SIA-SUS e Censo 2022 (IBGE).</p>",
    unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
sem = int((df["mamografos_existentes"] == 0).sum())
cob_nac = df["rast_bienio"].sum() / df["pop_feminina_50a69"].sum()
defi = int(df["deficit_anual"].sum())
c1.metric("Municípios sem mamógrafo", f"{sem:,}".replace(",", "."), f"{sem/N:.0%} do país",
          delta_color="off")
c2.metric("Cobertura bienal nacional", f"{cob_nac:.1%}", "meta: 70%", delta_color="off")
c3.metric("Déficit anual estimado", f"{defi/1e6:.1f} mi", "exames/ano", delta_color="off")
c4.metric("Mamógrafos em uso", f"{int(df['mamografos_em_uso'].sum()):,}".replace(",", "."),
          "no Brasil", delta_color="off")

aba_mapa, aba_mun, aba_rank, aba_sobre = st.tabs(
    ["🗺️ Mapa", "🔎 Consulta por município", "📊 Rankings", "ℹ️ Sobre"])

# ----------------------------- Aba Mapa -----------------------------
with aba_mapa:
    e1, e2 = st.columns([1, 1])
    indicador = e1.radio("Colorir o mapa por:", ["Cobertura bienal", "Classificação"],
                         horizontal=True)
    ufs = e2.multiselect("Filtrar UF (opcional):", sorted(df["uf"].unique()))
    dmap = df[df["uf"].isin(ufs)] if ufs else df

    if indicador == "Cobertura bienal":
        dmap = dmap.assign(cob_plot=dmap["cobertura_bienal_total"].clip(upper=1.0) * 100)
        fig = px.choropleth_mapbox(
            dmap, geojson=geo, locations="cod_ibge", featureidkey="properties.id",
            color="cob_plot", color_continuous_scale=["#b91c1c", "#f59e0b", BRIGHT, INK],
            range_color=(0, 70), mapbox_style="carto-positron",
            center={"lat": -14.5, "lon": -54}, zoom=3.1, opacity=0.78,
            hover_name="label",
            hover_data={"cob_pct": True, "mamografos_em_uso": True,
                        "deficit_anual": ":,.0f", "cod_ibge": False, "cob_plot": False},
            labels={"cob_plot": "Cobertura (%)", "cob_pct": "Cobertura",
                    "mamografos_em_uso": "Mamógrafos", "deficit_anual": "Déficit/ano"})
        fig.update_coloraxes(colorbar_title="Cobertura<br>bienal (%)")
    else:
        fig = px.choropleth_mapbox(
            dmap, geojson=geo, locations="cod_ibge", featureidkey="properties.id",
            color="classe", color_discrete_map={CLASS_LABEL.get(k, k): v for k, v in CLASS_COR.items()},
            category_orders={"classe": [CLASS_LABEL.get(c, c) for c in CLASSES]},
            mapbox_style="carto-positron", center={"lat": -14.5, "lon": -54},
            zoom=3.1, opacity=0.8, hover_name="label",
            hover_data={"cob_pct": True, "mamografos_em_uso": True,
                        "cod_ibge": False, "classe": False})
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=560,
                      legend=dict(title="", orientation="h", y=-0.04))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Passe o mouse sobre um município para ver os indicadores. "
               "Cinza = sem dado na malha. Cobertura por local de atendimento.")

# ----------------------- Aba Consulta por municipio -----------------------
with aba_mun:
    sel = st.selectbox("Escolha um município:", df.sort_values("label")["label"].tolist(),
                       index=None, placeholder="Digite o nome do município...")
    if sel:
        r = df[df["label"] == sel].iloc[0]
        st.markdown(f"### {r['municipio_nome']} — {r['uf_nome']}")
        badge = {"Deserto absoluto": "🔴", "Deserto funcional": "🟠",
                 "Intermediário": "🟡", "Adequado": "🟢"}.get(r["classe"], "⚪")
        st.markdown(f"**Classificação:** {badge} {r['classe']}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Mulheres 50–69", f"{int(r['pop_feminina_50a69']):,}".replace(",", "."))
        m2.metric("Mamógrafos (em uso)", f"{int(r['mamografos_existentes'])} ({int(r['mamografos_em_uso'])})")
        m3.metric("Cobertura bienal", f"{r['cob_pct']:.1f}%")
        m4.metric("Déficit anual", f"{int(r['deficit_anual']):,}".replace(",", "."))
        n1, n2, n3 = st.columns(3)
        n1.metric("Demanda anual", f"{int(r['demanda_anual']):,}".replace(",", "."))
        ocio = "—" if pd.isna(r["taxa_ociosidade"]) else f"{r['ocio_pct']:.0f}%"
        n2.metric("Ociosidade", ocio)
        rank_def = int((df["deficit_anual"] > r["deficit_anual"]).sum()) + 1
        n3.metric("Posição nacional em déficit", f"{rank_def}º de {N}")

        anos = list(range(2020, 2026))
        serie = pd.DataFrame({"Ano": anos,
                              "Rastreamento": [int(r[f"rast_{a}"]) for a in anos],
                              "Diagnóstica": [int(r[f"diag_{a}"]) for a in anos]})
        figm = px.bar(serie, x="Ano", y=["Rastreamento", "Diagnóstica"],
                      color_discrete_sequence=[BRIGHT, "#9FB4FF"],
                      title="Mamografias realizadas por ano")
        figm.update_layout(height=300, margin=dict(t=40, b=0, l=0, r=0),
                           legend_title="", yaxis_title="exames")
        st.plotly_chart(figm, use_container_width=True)

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
        st.markdown("**Maiores desertos absolutos** (sem máquina, por população)")
        t = (df[df["mamografos_existentes"] == 0]
             .sort_values("pop_feminina_50a69", ascending=False).head(50)[cols_show])
        st.dataframe(t.rename(columns=nomes), hide_index=True, use_container_width=True, height=420)
    with r2:
        st.markdown("**Maiores déficits** (demanda não atendida, por ano)")
        t = df.sort_values("deficit_anual", ascending=False).head(50)[cols_show]
        st.dataframe(t.rename(columns=nomes), hide_index=True, use_container_width=True, height=420)

# ----------------------------- Aba Sobre -----------------------------
with aba_sobre:
    st.markdown(f"""
**O que é este painel.** Um diagnóstico, por município, do equilíbrio entre a oferta de
mamografia no SUS e a demanda da população feminina de 50 a 69 anos — a faixa do
rastreamento bienal (Lei nº 11.664/2008).

**Fontes de dados.**
- **CNES** — mamógrafos instalados e em uso (competência Dez/2025).
- **SIA-SUS** — mamografias realizadas, por local de atendimento (2020–2025).
- **IBGE / Censo 2022** — população feminina de 50 a 69 anos por município.

**Parâmetros.** Produtividade de referência de **5.069 exames/ano** por mamógrafo
(INCA/MS, 2015); cobertura calculada sobre o biênio 2024–2025.

**Indicadores.** Cobertura bienal, capacidade instalada, taxa de ociosidade, déficit
anual e a classificação (deserto absoluto / funcional / intermediário / adequado).

**Limitações.** A produção é contada por local de atendimento (não de residência), e a
capacidade inclui equipamentos privados — o que torna os déficits **conservadores**.

**Validação.** A soma dos {N:,} municípios reproduz os totais nacionais oficiais das três
bases, sem discrepância.

---
Matheus Zacche Caetano · Orientação: Profª. Joicce Paiva Tosta · Engenharia de Produção, FAESA, 2026.
""".replace(",", "."))
