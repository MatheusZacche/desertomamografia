# Desertos de Mamografia no SUS — Painel interativo

Painel que mapeia, por município, o equilíbrio entre a **oferta de mamografia no SUS** e a
**demanda** da população feminina de 50 a 69 anos (faixa do rastreamento bienal). Construído
apenas com dados públicos (CNES, SIA-SUS e Censo 2022/IBGE), sob a ótica da análise de
capacidade da Engenharia de Produção.

**Autor:** Matheus Zacche Caetano · **Orientação:** Profª. Joicce Paiva Tosta · FAESA, 2026.

## Recursos
- **Mapa coroplético** dos 5.570 municípios (cobertura ou classificação).
- **Consulta por município** com todos os indicadores e a série histórica.
- **Rankings** dos municípios em pior situação.
- KPIs nacionais (municípios sem mamógrafo, cobertura, déficit).

## Rodar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```
Abre em `http://localhost:8501`.

## Publicar (grátis) no Streamlit Community Cloud
1. Garanta que este repositório está no GitHub (público).
2. Acesse **https://share.streamlit.io** e faça login com o GitHub.
3. **New app** → selecione este repositório, branch `main`, arquivo `app.py`.
4. **Deploy**. Em ~1 min o painel fica online com uma URL pública.

## Dados e parâmetros
- Mamógrafos: **CNES** (Dez/2025). Exames: **SIA-SUS**, por local de atendimento (2020–2025).
  População: **IBGE / Censo 2022**.
- Produtividade de referência: **5.069 exames/ano** por mamógrafo (INCA/MS, 2015).
- Malha municipal: IBGE via [tbrugz/geodata-br](https://github.com/tbrugz/geodata-br) (simplificada).

## Limitações
Produção contada por local de atendimento (não de residência); capacidade inclui equipamentos
privados — o que torna os déficits **conservadores**. A soma dos municípios foi validada contra
os totais oficiais das três bases, sem discrepância.
