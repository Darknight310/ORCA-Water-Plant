import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        /* Global Dark Theme Background */
        .stApp {
            background-color: #0B0F19;
            color: #F8FAFC;
        }
        
        /* Hide default Streamlit header elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0F172A;
            border-right: 1px solid #1E293B;
        }
        [data-testid="stSidebar"] .block-container {
            padding-top: 2rem;
        }
        
        /* Top Header Bar */
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #0F172A;
            padding: 15px 25px;
            border-radius: 12px;
            border: 1px solid #1E293B;
            margin-bottom: 25px;
        }
        .header-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #FFFFFF;
            letter-spacing: -0.5px;
        }
        .header-subtitle {
            font-size: 0.85rem;
            color: #38BDF8;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Metric Cards Styling */
        div.stMetric {
            background-color: #111827;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            border: 1px solid #1F2937;
        }
        div.stMetric label { color: #94A3B8 !important; font-weight: 600 !important; font-size: 0.8rem !important; text-transform: uppercase; }
        div.stMetric [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: 700 !important; font-size: 1.5rem !important; }
        
        /* Dataframes & Tables */
        [data-testid="stDataFrame"] {
            background-color: #111827;
            border-radius: 10px;
            border: 1px solid #1F2937;
            padding: 10px;
        }
        
        /* Buttons */
        .stButton>button {
            background-color: #0284C7;
            color: white;
            border-radius: 8px;
            font-weight: 600;
            border: none;
            padding: 0.5rem 1rem;
        }
        .stButton>button:hover { background-color: #0369A1; color: white; }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: #111827;
            color: #FFFFFF;
            border-radius: 8px;
            border: 1px solid #1F2937;
        }
        </style>
    """, unsafe_allow_html=True)
