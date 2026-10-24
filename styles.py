import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        /* Global App Theme */
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

        /* Sidebar Styling & Clean Navigation List */
        [data-testid="stSidebar"] {
            background-color: #0B0F17;
            border-right: 1px solid #1F2937;
        }

        div[role="radiogroup"] {
            gap: 8px;
        }
        
        div[role="radiogroup"] > label {
            background-color: #111827;
            border: 1px solid #1F2937;
            border-radius: 8px;
            padding: 10px 14px;
            width: 100%;
            transition: all 0.2s ease;
        }
        
        div[role="radiogroup"] > label:hover {
            border-color: #38BDF8;
            background-color: #1E293B;
        }
        </style>
    """, unsafe_allow_html=True)
