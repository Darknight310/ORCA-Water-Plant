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

        /* Metric Tile Containers */
        [data-testid="stMetric"] {
            background-color: #111827;
            border: 1px solid #1F2937;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0B0F17;
            border-right: 1px solid #1F2937;
        }
        </style>
    """, unsafe_allow_html=True)
