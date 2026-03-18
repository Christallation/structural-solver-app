import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Pro Statics Solver", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #e5e7eb; }
    header {visibility: hidden;}
    .stMetric { background-color: #161b22; padding: 10px; border-radius: 5px; border: 1px solid #30363d; }
    /* This makes input boxes look cleaner on mobile */
    .stNumberInput { margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE CALCULATION ENGINE ---
def solve_statics(L, p_loads, moments, udls):
    x = np.linspace(0, L, 1000)
    V = np.zeros_like(x)
    M = np.zeros_like(x)
    
    sum_p_m = sum(p['mag'] * p['pos'] for p in p_loads)
    sum_m_m = sum(m['mag'] for m in moments)
    sum_u_m = sum(u['mag'] * (u['end'] - u['start']) * ((u['start'] + u['end']) / 2) for u in udls)
    
    Rb = (sum_p_m + sum_m_m + sum_u_m) / (L if L > 0 else 1)
    Ra = (sum(p['mag'] for p in p_loads) + sum(u['mag']*(u['end']-u['start']) for u in udls)) - Rb
    
    for i, xi in enumerate(x):
        v_xi, m_xi = Ra, Ra * xi
        for p in p_loads:
            if xi > p['pos']:
                v_xi -= p['mag']
                m_xi -= p['mag'] * (xi - p['pos'])
        for m in moments:
            if xi > m['pos']:
                m_xi += m['mag']
        for u in udls:
            if xi > u['start']:
                load_len = min(xi, u['end']) - u['start']
                v_xi -= u['mag'] * load_len
                m_xi -= u['mag'] * load_len * (xi - (u['start'] + min(xi, u['end'])) / 2)
        V[i], M[i] = v_xi, m_xi
        
    return x, V, M, Ra, Rb

# --- 3. MAIN PAGE INPUTS (No Sidebar) ---
st.title("Statics & Mechanics Solver")

st.header("📏 1. Beam Geometry")
L = st.number_input("Total Length (m)", value=10.0, step=1.0)

st.divider()
st.header("➕ 2. Add Point Loads")
num_p = st.number_input("How many point loads?", 0, 10, 1)
p_loads = []
if num_p > 0:
    for i in range(num_p):
        c1, c2 = st.columns(2)
        mag = c1.number_input(f"P{i+1} Magnitude (kN)", value=10.0, key=f"p_mag_{i}")
        pos = c2.number_input(f"P{i+1} Distance (m)", value=L/2, key=f"p_pos_{i}")
        p_loads.append({'mag': mag, 'pos': pos})

st.divider()
st.header("🔄 3. Add Moments")
num_m = st.number_input("How many moments?", 0, 10, 0)
m_loads = []
if num_m > 0:
    for i in range(num_m):
        c1, c2 = st.columns(2)
        mag = c1.number_input(f"M{i+1} Magnitude (kNm)", value=5.0, key=f"m_mag_{i}")
        pos = c2.number_input(f"M{i+1} Distance (m)", value=L/2, key=f"m_pos_{i}")
        m_loads.append({'mag': mag, 'pos': pos})

# --- 4. EXECUTION & VISUALS ---
x, V, M, Ra, Rb = solve_statics(L, p_loads, m_loads, [])

st.divider()
st.subheader("Results & Diagrams")
col_r1, col_r2 = st.columns(2)
col_r1.metric("Ra Reaction", f"{Ra:.2f} kN")
col_r2.metric("Rb Reaction", f"{Rb:.2f} kN")

# Real Body Diagram
fig_b, ax_b = plt.subplots(figsize=(10, 2))
ax_b.set_facecolor('#0d1117'); fig_b.patch.set_facecolor('#0d1117')
ax_b.hlines(0, 0, L, colors='#3b82f6', lw=10)
ax_b.plot(0, 0, '^', color='#ef4444', ms=15)
ax_b.plot(L, 0, 'o', color='#ef4444', ms=12)
ax_b.annotate(f'Ra={Ra:.1f}', xy=(0,0), xytext=(-1,-2), color='white', arrowprops=dict(arrowstyle='->', color='yellow'))
ax_b.annotate(f'Rb={Rb:.1f}', xy=(L,0), xytext=(L+0.2,-2), color='white', arrowprops=dict(arrowstyle='->', color='yellow'))
ax_b.axis('off')
st.pyplot(fig_b)

# SFD and BMD
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
ax1.fill_between(x, V, color='dodgerblue', alpha=0.3); ax1.plot(x, V, color='dodgerblue'); ax1.set_title("Shear (V)")
ax2.fill_between(x, M, color='red', alpha=0.3); ax2.plot(x, M, color='red'); ax2.set_title("Moment (M)")
st.pyplot(fig)

with st.expander("Show Mathematical Derivation"):
    st.write("Using **Method of Sections**:")
    st.latex(r"V(x) = R_A - \sum P_{left}")
    st.latex(r"M(x) = R_A(x) - \sum P_{left}(x - x_i) + \sum M_{applied}")
