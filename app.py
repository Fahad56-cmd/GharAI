import streamlit as st
import pandas as pd
from agent import run_gharai
from price_loader import get_meta

st.set_page_config(page_title="GharAI", page_icon="🏠", layout="wide")

st.markdown("""
<style>
.big-title { font-size: 2.4rem; font-weight: 700; color: #c9a84c; margin-bottom: 0; }
.subtitle  { font-size: 1rem; color: #888; margin-top: 0; margin-bottom: 1.5rem; }
.agent-log-box { background: #0f1923; color: #00ff88;
                 font-family: monospace; font-size: 0.85rem;
                 padding: 1rem; border-radius: 8px; }
.metric-card { background: #1a2535; border-radius: 10px;
               padding: 1rem 1.5rem; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────
st.markdown('<p class="big-title">GharAI 🏠</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Multi-Agent Interior Design Estimator — Pakistan</p>', unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### How it works")
    st.info("3 AI agents run in sequence:\n\n"
            "1. **Extractor** — reads your brief\n"
            "2. **Cost Analyst** — calculates PKR costs\n"
            "3. **Design Advisor** — gives suggestions")

    st.markdown("### Price database")
    meta = get_meta()
    st.caption(f"Last updated: **{meta['last_updated']}**")
    st.caption(f"Source: {meta['source']}")
    st.caption(f"Currency: {meta['currency']}")

    st.markdown("### Example briefs")
    st.code("3 bedroom apartment Karachi, marble floors, textured walls, modern, PKR 800,000")
    st.code("1 drawing room Lahore, porcelain tiles, painted walls, classic style, PKR 200,000")
    st.code("2 bedroom flat Islamabad, marble, texture, contemporary, PKR 500,000")

# ── Input ────────────────────────────────────────────────────────────
brief = st.text_area(
    "Describe your project:",
    placeholder="e.g. 3 bedroom apartment in Karachi, marble floors, textured walls, modern style, budget PKR 800,000",
    height=100
)

run_btn = st.button("Run All Agents", type="primary", use_container_width=True)

# ── Results ──────────────────────────────────────────────────────────
if run_btn and brief.strip():
    with st.spinner("Agents are working..."):
        result = run_gharai(brief)

    room     = result["room"]
    analysis = result["analysis"]
    advice   = result["advice"]
    log      = result["agent_log"]

    st.divider()

    # Agent log — show this first, proves MAS to judges
    st.markdown("#### Agent log")
    log_text = "\n".join(log)
    st.markdown(f'<div class="agent-log-box">{log_text}</div>', unsafe_allow_html=True)

    st.divider()

    # Room dimensions detected
    st.markdown("#### Room dimensions detected")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Length",        f"{room['length']} ft")
    c2.metric("Width",         f"{room['width']} ft")
    c3.metric("Height",        f"{room['height']} ft")
    c4.metric("No. of rooms",  room.get('num_rooms', 1))

    st.divider()

    # Areas calculated
    st.markdown("#### Areas calculated")
    a1, a2, a3 = st.columns(3)
    a1.metric("Floor area",   f"{analysis['areas']['floor_area']:,.0f} sqft")
    a2.metric("Wall area",    f"{analysis['areas']['wall_area']:,.0f} sqft")
    a3.metric("Ceiling area", f"{analysis['areas']['ceiling_area']:,.0f} sqft")

    st.divider()

    # Cost breakdown
    st.markdown("#### Cost breakdown (PKR)")
    cost_df = pd.DataFrame(
        list(analysis["cost_breakdown"].items()),
        columns=["Item", "Cost (PKR)"]
    )
    cost_df["Cost (PKR)"] = cost_df["Cost (PKR)"].apply(lambda x: f"PKR {x:,.0f}")
    st.dataframe(cost_df, use_container_width=True, hide_index=True)

    # Total vs budget
    st.divider()
    total   = analysis["total_cost"]
    budget  = room.get("budget_pkr", 0)
    gap     = analysis["budget_gap"]
    delta   = f"PKR {abs(gap):,.0f} {'over' if gap > 0 else 'under'} budget"
    st.metric("Total estimated cost",
              f"PKR {total:,.0f}",
              delta=delta,
              delta_color="inverse")

    st.divider()

    # Design suggestions
    st.markdown("#### Design advisor suggestions")
    for i, tip in enumerate(advice.get("suggestions", []), 1):
        st.info(f"**Tip {i}:** {tip}")

    if advice.get("style_note"):
        st.caption(f"Style note: {advice['style_note']}")

elif run_btn:
    st.warning("Please type a project brief first.")