import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        /* Global Background & Typography */
        .main {
            background-color: #0B0F17;
            color: #F8FAFC;
        }
        
        /* Header Container */
        .header-container {
            background-color: #111827;
            border: 1px solid #1F2937;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header-title {
            color: #FFFFFF;
            font-size: 1.5rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: -0.5px;
        }
        
        .header-subtitle {
            color: #38BDF8;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }

        /* Clean Sidebar Radio Spacing */
        div[role="radiogroup"] {
            gap: 6px;
        }
        div[role="radiogroup"] label {
            padding: 4px 0px;
        }
        </style>
    """, unsafe_allow_html=True)
