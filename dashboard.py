import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import create_engine, text

from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_TABLE

st.set_page_config(
    page_title="World Bank Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

THEME = {
    "app": "#0b0f14", "surface": "#111821", "surface_2": "#17212c", "surface_3": "#1f2b36",
    "text": "#f4f7fb", "muted": "#9aa8b7", "subtle": "#6f8194", "border": "#253444",
    "primary": "#3fb7b4", "primary_2": "#82d8d4",
    "amber": "#e5a84b", "green": "#5fd18b", "red": "#ef6f6c", "blue": "#6da7ff", "purple": "#b07ef5",
    "grid": "rgba(154,168,183,0.16)",
}

INDICATOR_KEYS = {
    "PIB":            "GDP (current US$)",
    "Crecimiento PIB":"GDP growth (annual %)",
    "Población":      "Population, total",
    "Inflación":      "Inflation, consumer prices (annual %)",
    "Desempleo":      "Unemployment, total (% of total labor force) (modeled ILO estimate)",
}
INDICATOR_LABELS = {v: k for k, v in INDICATOR_KEYS.items()}

KPI_ACCENTS = {
    "PIB":             THEME["primary"],
    "Crecimiento PIB": THEME["red"],
    "PIB per cápita":  THEME["purple"],
    "Población":       THEME["blue"],
    "Inflación":       THEME["amber"],
    "Desempleo":       THEME["green"],
}

PAGES = ["Inicio", "PIB", "Crecimiento PIB", "Población", "Inflación", "Desempleo", "Comparación"]

PAIS_ORDER = ["Chile", "Peru", "Argentina"]
PAIS_FLAGS = {"Chile": "🇨🇱", "Peru": "🇵🇪", "Argentina": "🇦🇷"}

st.markdown(f"""
<style>
  html, body, [class*="css"] {{ font-family: "Inter", system-ui, sans-serif; }}
  .stApp {{
      color: {THEME["text"]};
      background:
        radial-gradient(ellipse at 8% 0%,   rgba(63,183,180,0.18), transparent 28rem),
        radial-gradient(ellipse at 92% 100%, rgba(229,168,75,0.08), transparent 36rem),
        linear-gradient(180deg, #0d131a 0%, {THEME["app"]} 38%, #090d12 100%);
  }}
  .block-container {{ max-width: 1680px; padding: 1rem 1.6rem 0.5rem; }}
  header[data-testid="stHeader"] {{ background: transparent; }}
  #MainMenu, footer {{ visibility: hidden; }}
  [data-testid="stSidebar"] {{
      background: radial-gradient(ellipse at 50% 0%, rgba(63,183,180,0.15), transparent 50%),
        linear-gradient(180deg, #0f1520 0%, {THEME["app"]} 55%, #090d12 100%);
      border-right: 1px solid rgba(63,183,180,0.12);
  }}
  section[data-testid="stSidebar"] > div:first-child {{ padding: 1.1rem 1.1rem 0.8rem; }}
  [data-testid="stSidebarCollapseButton"], [data-testid="stBaseButton-headerNoPadding"] {{ display:none!important; }}
  .sidebar-divider {{ border:none; border-top:1px solid {THEME["border"]}; margin:0.6rem 0; }}
  .hero-kicker {{ color:{THEME["primary_2"]}; font-size:0.68rem; font-weight:800; letter-spacing:0.12em; text-transform:uppercase; }}
  .hero-title  {{ color:{THEME["text"]}; font-size:1.4rem; font-weight:800; margin:0.15rem 0 0.3rem; }}
  .hero-copy   {{ color:{THEME["muted"]}; font-size:0.75rem; line-height:1.45; }}
  /* KPI card base */
  .kpi-card {{
      position:relative; box-sizing:border-box; overflow:hidden;
      display:flex; flex-direction:column;
      border:1px solid rgba(63,183,180,0.14); border-radius:10px;
      background:linear-gradient(150deg,{THEME["surface_2"]} 0%,{THEME["surface"]} 60%,#0d131a 100%);
      box-shadow:0 8px 24px rgba(0,0,0,0.38), inset 0 1px 0 rgba(255,255,255,0.10);
      padding:0.75rem 1rem 0.7rem; height:110px;
  }}
  /* Large KPI for Inicio */
  .kpi-card.large {{ height:170px; }}
  .kpi-card::after {{
      content:""; position:absolute; top:-12px; left:50%; transform:translateX(-50%);
      width:65%; height:48px; background:var(--accent,{THEME["primary"]}); opacity:0.12;
      filter:blur(20px); border-radius:50%; pointer-events:none;
  }}
  .kpi-label  {{ color:{THEME["muted"]}; font-size:0.70rem; font-weight:800; letter-spacing:0.07em; text-transform:uppercase; }}
  .kpi-value  {{ color:{THEME["text"]}; font-weight:800; line-height:1.08; margin-top:0.3rem; word-break:break-word; font-size:clamp(0.95rem,1.3vw,1.3rem); }}
  .kpi-value.large {{ font-size:clamp(1.5rem,2.2vw,2.4rem); margin-top:0.5rem; }}
  .kpi-note   {{ color:{THEME["subtle"]}; font-size:0.68rem; font-weight:600; margin-top:auto; line-height:1.3; }}
  .section-title {{ color:{THEME["text"]}; font-size:0.82rem; font-weight:800; letter-spacing:0.02em; margin:0.4rem 0 0.2rem; }}
  .section-title span {{ color:{THEME["subtle"]}; font-weight:700; }}
  .insight-box {{
      border:1px solid rgba(63,183,180,0.15); border-radius:8px;
      background:rgba(17,24,33,0.72); padding:0.7rem 1rem;
      font-size:0.76rem; color:{THEME["muted"]}; line-height:1.55;
  }}
  .insight-box b {{ color:{THEME["text"]}; }}
  div[data-testid="stDataFrame"] {{
      border:1px solid rgba(63,183,180,0.12); border-radius:8px;
      background:{THEME["surface"]}; box-shadow:0 4px 14px rgba(0,0,0,0.26);
  }}
  /* Twemoji — limita tamaño de todos los emojis convertidos a SVG */
  img.emoji {
      height: 1em !important;
      width: 1em !important;
      vertical-align: -0.12em;
      display: inline-block;
  }
  /* Sidebar nav — radio group styled as nav list */
  [data-testid="stSidebar"] .stRadio > div:first-child {{ display:none; }}
  [data-testid="stSidebar"] .stRadio [role="radiogroup"] {{
      display:flex; flex-direction:column; gap:1px;
  }}
  [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {{
      display:flex; align-items:center; gap:0.55rem;
      padding:0.44rem 0.75rem; border-radius:6px;
      font-size:0.79rem; font-weight:600; letter-spacing:0.01em;
      color:{THEME["subtle"]}; cursor:pointer;
      border-left:2px solid transparent;
      transition:background 0.14s, color 0.14s, border-color 0.14s;
  }}
  [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover {{
      background:rgba(63,183,180,0.07); color:{THEME["text"]};
  }}
  [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label[data-checked="true"] {{
      background:rgba(63,183,180,0.12); color:{THEME["primary_2"]};
      border-left:2px solid {THEME["primary"]};
  }}
  [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label > div:first-child {{
      display:none;
  }}
</style>""", unsafe_allow_html=True)

# Twemoji: convierte emojis de banderas en SVGs para que Chrome en Windows los muestre
components.html("""
<script src="https://cdn.jsdelivr.net/npm/twemoji@14.0.2/dist/twemoji.min.js" crossorigin="anonymous"></script>
<script>
(function () {
    var opts = { folder: "svg", ext: ".svg" };
    function parse() { twemoji.parse(parent.document.body, opts); }
    if (document.readyState === "complete") { parse(); }
    else { window.addEventListener("load", parse); }
    new MutationObserver(parse).observe(parent.document.body, { childList: true, subtree: true });
})();
</script>
""", height=0)


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_num(v):
    if pd.isna(v): return "—"
    if abs(v) >= 1e12: return f"${v/1e12:.2f}T"
    if abs(v) >= 1e9:  return f"${v/1e9:.2f}B"
    if abs(v) >= 1e6:  return f"${v/1e6:.2f}M"
    return f"{v:,.2f}"

def fmt_kpi(v, label):
    if pd.isna(v): return "—"
    if label in ("PIB", "PIB per cápita"): return fmt_num(v)
    if label == "Población": return f"{v/1e6:.2f}M" if v >= 1e6 else f"{v:,.0f}"
    return f"{v:.2f}%"

def kpi_card(label, value, note="", accent="", large=False):
    style  = f' style="--accent:{accent};"' if accent else ""
    c_cls  = "kpi-card large" if large else "kpi-card"
    v_cls  = "kpi-value large" if large else "kpi-value"
    note_h = f'<div class="kpi-note">{escape(note)}</div>' if note else ""
    return (f'<div class="{c_cls}"{style}>'
            f'<div class="kpi-label">{escape(label)}</div>'
            f'<div class="{v_cls}">{escape(value)}</div>'
            f'{note_h}</div>')

def section_title(title, detail=""):
    d = f" <span>{detail}</span>" if detail else ""
    st.markdown(f'<div class="section-title">{title}{d}</div>', unsafe_allow_html=True)

def base_layout(fig, height=290):
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=22, b=8),
        paper_bgcolor=THEME["surface"], plot_bgcolor=THEME["surface"],
        font=dict(color=THEME["muted"], family="Inter, sans-serif", size=12),
        hovermode="x unified",
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=THEME["muted"]),
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor=THEME["grid"], zeroline=False, tickfont=dict(color=THEME["muted"])),
        yaxis=dict(gridcolor=THEME["grid"], zeroline=False, tickfont=dict(color=THEME["muted"])),
    )
    return fig

def pearson_r(x, y):
    m = ~(np.isnan(x) | np.isnan(y))
    return float(np.corrcoef(x[m], y[m])[0, 1]) if m.sum() >= 4 else None

def linear_forecast(x, y, years=4):
    m = ~np.isnan(y); x, y = x[m], y[m]
    if len(x) < 6: return None, None, None, None
    c = np.polyfit(x[-12:], y[-12:], 1)
    std = np.std(y[-12:] - np.polyval(c, x[-12:]))
    fx = np.arange(x[-1]+1, x[-1]+years+1)
    fy = np.polyval(c, fx)
    return fx, fy, fy - 1.5*std, fy + 1.5*std

def trend_chart(x, y, pais, color, title="", forecast=True):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines", name="Histórico",
        line=dict(color=color, width=2.8),
        hovertemplate=f"<b>{pais}</b> %{{x:.0f}}: %{{y:.2f}}<extra></extra>",
    ))
    if forecast:
        fx, fy, fl, fu = linear_forecast(x, y)
        if fx is not None:
            fig.add_trace(go.Scatter(
                x=np.concatenate([[x[-1]], fx]), y=np.concatenate([[y[-1]], fy]),
                mode="lines", name="Proyección",
                line=dict(color=color, width=2, dash="dash"),
                hovertemplate="Forecast %{x:.0f}: %{y:.2f}<extra></extra>",
            ))
            r, g, b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
            fig.add_trace(go.Scatter(
                x=np.concatenate([fx, fx[::-1]]), y=np.concatenate([fu, fl[::-1]]),
                fill="toself", fillcolor=f"rgba({r},{g},{b},0.10)",
                line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip",
            ))
    return base_layout(fig)

def get_series(df_pais, ind_key):
    s = df_pais[df_pais["indicador"] == ind_key].sort_values("fecha")
    return s["fecha"].values.astype(float), s["valor"].values.astype(float)

def latest_val(df_pais, ind_key):
    s = df_pais[df_pais["indicador"] == ind_key].dropna(subset=["valor"])
    if s.empty: return float("nan"), "—"
    yr = int(s["fecha"].max())
    return s[s["fecha"] == yr]["valor"].values[0], str(yr)

def trend_label(s):
    s = s.dropna()
    if len(s) < 5: return "sin datos"
    slope = np.polyfit(range(len(s)), s.values, 1)[0]
    if abs(slope)/(abs(s.mean())+1e-9) < 0.005: return "estable"
    return "creciente 📈" if slope > 0 else "decreciente 📉"


# ── Data ─────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    return create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

@st.cache_data(ttl=3600)
def load_data():
    with get_engine().connect() as conn:
        df = pd.read_sql(text(f"SELECT * FROM {DB_TABLE}"), conn)
    df["fecha"] = pd.to_numeric(df["fecha"], errors="coerce")
    df = df.dropna(subset=["valor", "fecha"])
    df["indicador_corto"] = df["indicador"].map(INDICATOR_LABELS).fillna(df["indicador"])
    return df

def build_wide(df_sub):
    w = df_sub.pivot_table(index=["pais","fecha"], columns="indicador_corto", values="valor", aggfunc="mean").reset_index()
    if "PIB" in w.columns and "Población" in w.columns:
        w["PIB per cápita"] = w["PIB"] / w["Población"]
    return w

df = load_data()
if df.empty:
    st.error("Sin datos. Corre el pipeline primero.")
    st.stop()

paises    = [p for p in PAIS_ORDER if p in df["pais"].unique()]
anios     = sorted(df["fecha"].dropna().unique())
color_map = {"Chile": THEME["primary_2"], "Peru": THEME["amber"], "Argentina": THEME["blue"]}


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div class="hero-kicker">Banco Mundial</div>
<div class="hero-title">🌍 Macro Dashboard</div>
<div class="hero-copy">Indicadores macroeconómicos — Chile, Perú y Argentina.</div>
""", unsafe_allow_html=True)
st.sidebar.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

page = st.sidebar.radio("Sección", PAGES, label_visibility="collapsed")

st.sidebar.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
anio_range = st.sidebar.slider(
    "Rango de años", int(anios[0]), int(anios[-1]),
    (max(int(anios[0]), int(anios[-1]) - 29), int(anios[-1])),
)


# ── Country tabs ──────────────────────────────────────────────────────────────
tab_labels   = [f"{PAIS_FLAGS.get(p, '')} {p}" for p in paises]
country_tabs = st.tabs(tab_labels)

for tab, pais in zip(country_tabs, paises):
    with tab:
        col_c     = color_map[pais]
        df_fil    = df[(df["fecha"] >= anio_range[0]) & (df["fecha"] <= anio_range[1])]
        df_pais   = df_fil[df_fil["pais"] == pais]
        wide_all  = build_wide(df_fil)
        wide_pais = wide_all[wide_all["pais"] == pais].sort_values("fecha")


        # ════════════════════════════════════════════════════
        # 🏠 INICIO
        # ════════════════════════════════════════════════════
        if page == "Inicio":
            st.markdown('<div style="margin-top:0.6rem"></div>', unsafe_allow_html=True)

            kpi_layout = [
                ["PIB", "Crecimiento PIB", "PIB per cápita"],
                ["Población", "Inflación", "Desempleo"],
            ]
            for row_names in kpi_layout:
                cols = st.columns(3)
                for col_st, name in zip(cols, row_names):
                    if name == "PIB per cápita":
                        sub = wide_pais.dropna(subset=["PIB per cápita"])
                        val = sub["PIB per cápita"].iloc[-1] if not sub.empty else float("nan")
                        yr  = str(int(sub["fecha"].iloc[-1])) if not sub.empty else "—"
                    else:
                        val, yr = latest_val(df_pais, INDICATOR_KEYS[name])
                    col_st.markdown(
                        kpi_card(name, fmt_kpi(val, name), f"Año {yr}", KPI_ACCENTS[name], large=True),
                        unsafe_allow_html=True,
                    )
                st.markdown('<div style="margin-top:0.5rem"></div>', unsafe_allow_html=True)


        # ════════════════════════════════════════════════════
        # 📊 PIB
        # ════════════════════════════════════════════════════
        elif page == "PIB":
            val, yr = latest_val(df_pais, INDICATOR_KEYS["PIB"])
            sub_pc  = wide_pais.dropna(subset=["PIB per cápita"])
            val_pc  = sub_pc["PIB per cápita"].iloc[-1] if not sub_pc.empty else float("nan")
            yr_pc   = str(int(sub_pc["fecha"].iloc[-1])) if not sub_pc.empty else "—"

            c1, c2 = st.columns(2)
            c1.markdown(kpi_card("PIB", fmt_kpi(val, "PIB"), f"Año {yr} · {pais}", KPI_ACCENTS["PIB"]), unsafe_allow_html=True)
            c2.markdown(kpi_card("PIB per cápita", fmt_kpi(val_pc, "PIB per cápita"), f"Año {yr_pc} · {pais}", KPI_ACCENTS["PIB per cápita"]), unsafe_allow_html=True)

            st.markdown('<div style="margin-top:0.5rem"></div>', unsafe_allow_html=True)
            c_l, c_r = st.columns(2)

            with c_l:
                section_title("PIB nominal", f"{pais} · {anio_range[0]}–{anio_range[1]}")
                x, y = get_series(df_pais, INDICATOR_KEYS["PIB"])
                fig = trend_chart(x, y, pais, col_c)
                fig.update_yaxes(tickprefix="$", tickformat=".2s")
                st.plotly_chart(fig, width="stretch")

            with c_r:
                section_title("PIB per cápita", f"{pais} · {anio_range[0]}–{anio_range[1]}")
                s = wide_pais.dropna(subset=["PIB per cápita"])
                x2, y2 = s["fecha"].values.astype(float), s["PIB per cápita"].values.astype(float)
                fig2 = trend_chart(x2, y2, pais, col_c)
                fig2.update_yaxes(tickprefix="$", tickformat=",.0f")
                st.plotly_chart(fig2, width="stretch")

            section_title("Datos históricos", "PIB y PIB per cápita")
            cols_t = [c for c in ["PIB","PIB per cápita"] if c in wide_pais.columns]
            df_t = wide_pais[["fecha"]+cols_t].rename(columns={"fecha":"Año"}).sort_values("Año", ascending=False).head(20).copy()
            df_t["Año"] = df_t["Año"].astype(int)
            for c in cols_t: df_t[c] = df_t[c].apply(lambda v: f"{v:.2f}" if pd.notna(v) else "—")
            st.dataframe(df_t, width="stretch", hide_index=True, height=280)


        # ════════════════════════════════════════════════════
        # 📈 CRECIMIENTO PIB
        # ════════════════════════════════════════════════════
        elif page == "Crecimiento PIB":
            val, yr = latest_val(df_pais, INDICATOR_KEYS["Crecimiento PIB"])
            st.markdown(kpi_card("Crecimiento PIB real", fmt_kpi(val, "Crecimiento PIB"), f"Año {yr} · {pais}", KPI_ACCENTS["Crecimiento PIB"]), unsafe_allow_html=True)
            st.markdown('<div style="margin-top:0.5rem"></div>', unsafe_allow_html=True)

            section_title("Crecimiento PIB real (%)", f"{pais} · {anio_range[0]}–{anio_range[1]}")
            x, y = get_series(df_pais, INDICATOR_KEYS["Crecimiento PIB"])
            fig = trend_chart(x, y, pais, col_c)
            fig.add_hline(y=0, line=dict(color=THEME["subtle"], width=1, dash="dot"))
            fig.update_yaxes(ticksuffix="%")
            st.plotly_chart(fig, width="stretch")

            # Insight
            s = df_pais[df_pais["indicador"] == INDICATOR_KEYS["Crecimiento PIB"]]["valor"]
            if len(s) >= 5:
                avg = s.mean(); best = s.max(); worst = s.min()
                st.markdown(f"""
<div class="insight-box">
  <b>Análisis {pais}</b> · período {anio_range[0]}–{anio_range[1]}<br><br>
  📊 Crecimiento promedio: <b>{avg:.2f}%</b><br>
  🏆 Mejor año: <b>{best:.2f}%</b> &nbsp;|&nbsp; ⚠️ Peor año: <b>{worst:.2f}%</b><br>
  📈 Tendencia: <b>{trend_label(s)}</b>
</div>""", unsafe_allow_html=True)


        # ════════════════════════════════════════════════════
        # 👥 POBLACIÓN
        # ════════════════════════════════════════════════════
        elif page == "Población":
            val, yr = latest_val(df_pais, INDICATOR_KEYS["Población"])
            st.markdown(kpi_card("Población", fmt_kpi(val, "Población"), f"Año {yr} · {pais}", KPI_ACCENTS["Población"]), unsafe_allow_html=True)
            st.markdown('<div style="margin-top:0.5rem"></div>', unsafe_allow_html=True)

            section_title("Evolución de la población", f"{pais} · {anio_range[0]}–{anio_range[1]}")
            x, y = get_series(df_pais, INDICATOR_KEYS["Población"])
            fig = trend_chart(x, y, pais, col_c)
            fig.update_yaxes(tickformat=".2s")
            st.plotly_chart(fig, width="stretch")

            section_title("Datos históricos", "Población")
            s = df_pais[df_pais["indicador"] == INDICATOR_KEYS["Población"]][["fecha","valor"]].rename(columns={"fecha":"Año","valor":"Población"})
            s = s.sort_values("Año", ascending=False).head(20).copy()
            s["Año"] = s["Año"].astype(int)
            s["Población"] = s["Población"].apply(lambda v: f"{v:.2f}" if pd.notna(v) else "—")
            st.dataframe(s, width="stretch", hide_index=True, height=280)


        # ════════════════════════════════════════════════════
        # 💹 INFLACIÓN
        # ════════════════════════════════════════════════════
        elif page == "Inflación":
            val, yr = latest_val(df_pais, INDICATOR_KEYS["Inflación"])
            val_d, yr_d = latest_val(df_pais, INDICATOR_KEYS["Desempleo"])
            c1, c2 = st.columns(2)
            c1.markdown(kpi_card("Inflación", fmt_kpi(val, "Inflación"), f"Año {yr} · {pais}", KPI_ACCENTS["Inflación"]), unsafe_allow_html=True)
            c2.markdown(kpi_card("Desempleo", fmt_kpi(val_d, "Desempleo"), f"Año {yr_d} · {pais}", KPI_ACCENTS["Desempleo"]), unsafe_allow_html=True)

            st.markdown('<div style="margin-top:0.5rem"></div>', unsafe_allow_html=True)
            c_l, c_r = st.columns(2)

            with c_l:
                section_title("Inflación anual (%)", f"{pais} · {anio_range[0]}–{anio_range[1]}")
                x, y = get_series(df_pais, INDICATOR_KEYS["Inflación"])
                fig = trend_chart(x, y, pais, col_c)
                fig.update_yaxes(ticksuffix="%")
                st.plotly_chart(fig, width="stretch")

            with c_r:
                section_title("Curva de Phillips", f"Inflación vs Desempleo · {pais}")
                wc = wide_pais.dropna(subset=["Inflación","Desempleo"])
                if not wc.empty:
                    xv = wc["Desempleo"].values.astype(float)
                    yv = wc["Inflación"].values.astype(float)
                    r  = pearson_r(xv, yv)
                    fig_s = go.Figure()
                    fig_s.add_trace(go.Scatter(
                        x=xv, y=yv, mode="markers",
                        marker=dict(color=col_c, size=7, opacity=0.8),
                        hovertemplate="Desempleo: %{x:.2f}%<br>Inflación: %{y:.2f}%<extra></extra>",
                        showlegend=False,
                    ))
                    if r is not None:
                        c_fit = np.polyfit(xv, yv, 1)
                        xl = np.array([xv.min(), xv.max()])
                        fig_s.add_trace(go.Scatter(
                            x=xl, y=np.polyval(c_fit, xl), mode="lines",
                            line=dict(color=THEME["red"], width=1.5, dash="dash"), showlegend=False,
                        ))
                    base_layout(fig_s)
                    fig_s.update_xaxes(title_text="Desempleo (%)", ticksuffix="%")
                    fig_s.update_yaxes(title_text="Inflación (%)", ticksuffix="%")
                    fig_s.update_layout(title=dict(text=f"r = {r:.2f}" if r else "", font=dict(color=THEME["muted"], size=11), x=0.5))
                    st.plotly_chart(fig_s, width="stretch")


        # ════════════════════════════════════════════════════
        # 💼 DESEMPLEO
        # ════════════════════════════════════════════════════
        elif page == "Desempleo":
            val, yr = latest_val(df_pais, INDICATOR_KEYS["Desempleo"])
            st.markdown(kpi_card("Desempleo", fmt_kpi(val, "Desempleo"), f"Año {yr} · {pais}", KPI_ACCENTS["Desempleo"]), unsafe_allow_html=True)
            st.markdown('<div style="margin-top:0.5rem"></div>', unsafe_allow_html=True)

            c_l, c_r = st.columns(2)
            with c_l:
                section_title("Tasa de desempleo (%)", f"{pais} · {anio_range[0]}–{anio_range[1]}")
                x, y = get_series(df_pais, INDICATOR_KEYS["Desempleo"])
                fig = trend_chart(x, y, pais, col_c)
                fig.update_yaxes(ticksuffix="%")
                st.plotly_chart(fig, width="stretch")

            with c_r:
                section_title("Desempleo vs Crecimiento PIB", f"{pais}")
                wc = wide_pais.dropna(subset=["Desempleo","Crecimiento PIB"])
                if not wc.empty:
                    xv = wc["Crecimiento PIB"].values.astype(float)
                    yv = wc["Desempleo"].values.astype(float)
                    r  = pearson_r(xv, yv)
                    fig_s = go.Figure()
                    fig_s.add_trace(go.Scatter(
                        x=xv, y=yv, mode="markers",
                        marker=dict(color=col_c, size=7, opacity=0.8),
                        hovertemplate="Crecimiento: %{x:.2f}%<br>Desempleo: %{y:.2f}%<extra></extra>",
                        showlegend=False,
                    ))
                    if r is not None:
                        c_fit = np.polyfit(xv, yv, 1)
                        xl = np.array([xv.min(), xv.max()])
                        fig_s.add_trace(go.Scatter(
                            x=xl, y=np.polyval(c_fit, xl), mode="lines",
                            line=dict(color=THEME["red"], width=1.5, dash="dash"), showlegend=False,
                        ))
                    base_layout(fig_s)
                    fig_s.update_xaxes(title_text="Crecimiento PIB (%)", ticksuffix="%")
                    fig_s.update_yaxes(title_text="Desempleo (%)", ticksuffix="%")
                    fig_s.update_layout(title=dict(text=f"r = {r:.2f}" if r else "", font=dict(color=THEME["muted"], size=11), x=0.5))
                    st.plotly_chart(fig_s, width="stretch")

            s = df_pais[df_pais["indicador"] == INDICATOR_KEYS["Desempleo"]]["valor"]
            if len(s) >= 5:
                st.markdown(f"""
<div class="insight-box">
  <b>Análisis desempleo · {pais}</b> · {anio_range[0]}–{anio_range[1]}<br><br>
  📊 Promedio: <b>{s.mean():.2f}%</b> &nbsp;|&nbsp;
  🏆 Mínimo: <b>{s.min():.2f}%</b> &nbsp;|&nbsp;
  ⚠️ Máximo: <b>{s.max():.2f}%</b><br>
  📈 Tendencia: <b>{trend_label(s)}</b>
</div>""", unsafe_allow_html=True)


        # ════════════════════════════════════════════════════
        # 🌍 COMPARACIÓN
        # ════════════════════════════════════════════════════
        elif page == "Comparación":
            # PIB per cápita comparativo
            section_title("PIB per cápita", f"todos los países · {anio_range[0]}–{anio_range[1]}")
            fig_pc = go.Figure()
            for p in paises:
                s = wide_all[wide_all["pais"] == p].sort_values("fecha").dropna(subset=["PIB per cápita"])
                fig_pc.add_trace(go.Scatter(
                    x=s["fecha"], y=s["PIB per cápita"], mode="lines", name=p,
                    line=dict(color=color_map[p], width=2.5),
                    hovertemplate=f"<b>{p}</b> %{{x:.0f}}: $%{{y:,.0f}}<extra></extra>",
                ))
            base_layout(fig_pc, height=250)
            fig_pc.update_yaxes(tickprefix="$", tickformat=",.0f")
            st.plotly_chart(fig_pc, width="stretch")

            # Crecimiento PIB comparativo
            section_title("Crecimiento PIB real (%)", f"todos los países · {anio_range[0]}–{anio_range[1]}")
            fig_gr = go.Figure()
            for p in paises:
                s = df_fil[(df_fil["pais"]==p) & (df_fil["indicador"]==INDICATOR_KEYS["Crecimiento PIB"])].sort_values("fecha")
                if s.empty: continue
                fig_gr.add_trace(go.Scatter(
                    x=s["fecha"], y=s["valor"], mode="lines", name=p,
                    line=dict(color=color_map[p], width=2.5),
                    hovertemplate=f"<b>{p}</b> %{{x:.0f}}: %{{y:.2f}}%<extra></extra>",
                ))
            fig_gr.add_hline(y=0, line=dict(color=THEME["subtle"], width=1, dash="dot"))
            base_layout(fig_gr, height=240)
            fig_gr.update_yaxes(ticksuffix="%")
            st.plotly_chart(fig_gr, width="stretch")

            # 4 subgráficos
            ind_bar = {k: v for k, v in INDICATOR_KEYS.items() if k != "Crecimiento PIB"}
            section_title("Comparación por indicador", "último año disponible")
            fig_comp = make_subplots(rows=2, cols=2, subplot_titles=list(ind_bar.keys()))
            for idx, (short, long_key) in enumerate(ind_bar.items()):
                r, c = divmod(idx, 2)
                for p in paises:
                    sub = df[(df["pais"]==p) & (df["indicador"]==long_key)].dropna(subset=["valor"])
                    if sub.empty: continue
                    yr  = int(sub["fecha"].max())
                    val = sub[sub["fecha"]==yr]["valor"].values[0]
                    fig_comp.add_trace(go.Bar(
                        name=p, x=[p], y=[val], marker_color=color_map[p],
                        showlegend=(idx==0),
                        text=[str(yr)], textposition="outside",
                        textfont=dict(size=10, color=THEME["muted"]),
                    ), row=r+1, col=c+1)
            fig_comp.update_layout(
                height=310, margin=dict(l=8, r=8, t=36, b=8),
                paper_bgcolor=THEME["surface"], plot_bgcolor=THEME["surface"],
                font=dict(color=THEME["muted"], family="Inter, sans-serif", size=11),
                barmode="group",
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=THEME["muted"]),
                            orientation="h", y=1.07, x=1, xanchor="right"),
            )
            fig_comp.update_xaxes(showgrid=False, showticklabels=False)
            fig_comp.update_yaxes(gridcolor=THEME["grid"], zeroline=False, tickfont=dict(color=THEME["muted"], size=9))
            fig_comp.update_annotations(font=dict(color=THEME["muted"], size=10))
            st.plotly_chart(fig_comp, width="stretch")

            # Tabla resumen
            section_title("Resumen comparativo", "último año con datos")
            rows_t = []
            for p in paises:
                row_d = {"País": p}
                dp = df[df["pais"] == p]
                for short, long_key in INDICATOR_KEYS.items():
                    s = dp[dp["indicador"] == long_key].dropna(subset=["valor"])
                    if s.empty: row_d[short] = "—"
                    else:
                        yr  = int(s["fecha"].max())
                        val = s[s["fecha"]==yr]["valor"].values[0]
                        row_d[short] = f"{val:.2f}"
                rows_t.append(row_d)
            st.dataframe(pd.DataFrame(rows_t), width="stretch", hide_index=True)
