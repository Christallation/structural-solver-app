import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Pro Statics Solver", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #e5e7eb; }
    header {visibility: hidden;}
    .stMetric { background-color: #161b22; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE CALCULATION ENGINE (Unlimited Logic) ---
def solve_statics(L, p_loads, moments, udls):
    x = np.linspace(0, L, 1000)
    V = np.zeros_like(x)
    M = np.zeros_like(x)
    
    # Calculate Global Reactions (ΣMa = 0)
    # Rb * L = Σ(P*d) + ΣM_applied + Σ(w*len*dist_to_A)
    sum_p_moments = sum(p['mag'] * p['pos'] for p in p_loads)
    sum_m_applied = sum(m['mag'] for m in moments)
    sum_udl_moments = sum(u['mag'] * (u['end'] - u['start']) * ((u['start'] + u['end']) / 2) for u in udls)
    
    Rb = (sum_p_moments + sum_m_applied + sum_udl_moments) / L
    Ra = (sum(p['mag'] for p in p_loads) + sum(u['mag']*(u['end']-u['start']) for u in udls)) - Rb
    
    for i, xi in enumerate(x):
        # Internal Force at point xi (Method of Sections)
        # Sum of forces/moments to the LEFT of the cut
        v_xi = Ra
        m_xi = Ra * xi
        
        for p in p_loads:
            if xi > p['pos']:
                v_xi -= p['mag']
                m_xi -= p['mag'] * (xi - p['pos'])
        for m in moments:
            if xi > m['pos']:
                m_xi += m['mag'] # Applied clockwise moment increases internal moment
        for u in udls:
            if xi > u['start']:
                load_len = min(xi, u['end']) - u['start']
                v_xi -= u['mag'] * load_len
                m_xi -= u['mag'] * load_len * (xi - (u['start'] + min(xi, u['end'])) / 2)
                
        V[i] = v_xi
        M[i] = m_xi
        
    return x, V, M, Ra, Rb

# --- 3. DYNAMIC INPUTS ---
st.title("Statics & Mechanics: Multi-Load Solver")

with st.sidebar:
    st.header("📏 Beam Span")
    L = st.number_input("Total Length (m)", value=10.0, step=1.0)
    
    st.header("➕ Add Point Loads")
    num_p = st.number_input("Number of Point Loads", 0, 10, 1)
    p_loads = []
    for i in range(num_p):
        col1, col2 = st.columns(2)
        mag = col1.number_input(f"P{i+1} (kN)", value=10.0, key=f"p_mag_{i}")
        pos = col2.number_input(f"Dist (m)", value=L/2, key=f"p_pos_{i}")
        p_loads.append({'mag': mag, 'pos': pos})

    st.header("🔄 Add Moments")
    num_m = st.number_input("Number of Moments", 0, 10, 0)
    m_loads = []
    for i in range(num_m):
        col1, col2 = st.columns(2)
        mag = col1.number_input(f"M{i+1} (kNm)", value=5.0, key=f"m_mag_{i}")
        pos = col2.number_input(f"Dist (m)", value=L/2, key=f"m_pos_{i}")
        m_loads.append({'mag': mag, 'pos': pos})

    st.header("🟦 Add UDLs")
    num_u = st.number_input("Number of UDLs", 0, 5, 0)
    u_loads = []
    for i in range(num_u):
        c1, c2, c3 = st.columns(3)
        mag = c1.number_input(f"w{i+1} (kN/m)", value=2.0, key=f"u_mag_{i}")
        start = c2.number_input(f"Start (m)", value=0.0, key=f"u_s_{i}")
        end = c3.number_input(f"End (m)", value=L, key=f"u_e_{i}")
        u_loads.append({'mag': mag, 'start': start, 'end': end})

# --- 4. EXECUTION & RESULTS ---
x, V, M, Ra, Rb = solve_statics(L, p_loads, m_loads, u_loads)

# Metrics Display
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ra Reaction", f"{Ra:.2f} kN")
c2.metric("Rb Reaction", f"{Rb:.2f} kN")
c3.metric("Max Moment", f"{np.max(np.abs(M)):.2f} kNm")
c4.metric("Max Shear", f"{np.max(np.abs(V)):.2f} kN")

# --- 5. THE REAL BODY DIAGRAM ---
st.subheader("Annotated Structural Body")
fig_body, ax_b = plt.subplots(figsize=(12, 2.5))
ax_b.set_facecolor('#0d1117')
fig_body.patch.set_facecolor('#0d1117')

# Beam Geometry
ax_b.hlines(0, 0, L, colors='#3b82f6', lw=12)
ax_b.plot(0, 0, '^', color='#ef4444', markersize=18) 
ax_b.plot(L, 0, 'o', color='#ef4444', markersize=14)

# Reaction Annotations
ax_b.annotate(f'Ra={Ra:.1f}kN', xy=(0, 0), xytext=(-1.5, -2.5), color='white',
             arrowprops=dict(arrowstyle='->', color='yellow', lw=2), fontweight='bold')
ax_b.annotate(f'Rb={Rb:.1f}kN', xy=(L, 0), xytext=(L+0.5, -2.5), color='white',
             arrowprops=dict(arrowstyle='->', color='yellow', lw=2), fontweight='bold')

# Load Visualizations
for p in p_loads:
    ax_b.annotate('', xy=(p['pos'], 0), xytext=(p['pos'], 1.5), arrowprops=dict(arrowstyle='->', color='lime'))
for m in m_loads:
    ax_b.plot(m['pos'], 0, 'o', color='orange')
    ax_b.text(m['pos'], 0.5, f"{m['mag']}kNm", color='orange', ha='center')

ax_b.set_xlim(-2, L+2); ax_b.set_ylim(-4, 3); ax_b.axis('off')
st.pyplot(fig_body)

# --- 6. PLOTS ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7))
ax1.fill_between(x, V, color='dodgerblue', alpha=0.3); ax1.plot(x, V, color='dodgerblue'); ax1.set_title("Shear Force Diagram (V)")
ax2.fill_between(x, M, color='red', alpha=0.3); ax2.plot(x, M, color='red'); ax2.set_title("Bending Moment Diagram (M)")
st.pyplot(fig)

# --- 7. STEP-BY-STEP MATHEMATICAL DERIVATION ---
with st.expander("Step-by-Step Mathematical Derivation", expanded=True):
    st.markdown("### 1. Global Equilibrium (External Forces)")
    st.write("We solve for unknown reactions using the sum of moments at A.")
    st.latex(r"\sum M_A = 0 \implies R_B \cdot L - \sum (P_i \cdot x_i) - \sum M_i - \int (w \cdot x) dx = 0")
    
    st.markdown("### 2. Method of Sections (Internal Forces)")
    st.write("To draw the diagrams, we imagine a cut at an arbitrary distance $x$ from the left support. The internal forces are calculated by summing everything to the left of that cut:")
    
    st.markdown("**Internal Shear $V(x)$:**")
    st.latex(r"V(x) = R_A - \sum P_i [x > x_i] - \int_{0}^{x} w(x) dx")
    st.info("The shear jumps down every time a point load $P$ is encountered.")
    
    st.markdown("**Internal Moment $M(x)$:**")
    st.latex(r"M(x) = R_A \cdot x - \sum P_i (x - x_i) [x > x_i] + \sum M_i [x > x_i] - \text{Moment from UDL}")
    st.write("The internal moment is the integral of the shear diagram. Points of zero shear correspond to the maximum or minimum bending moments.")