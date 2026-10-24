import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <stylemock>
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

        /* Transform Sidebar Radio Items into Large Clickable Tiles */
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            font-size: 0.95rem;
            font-weight: 600;
        }

        div[role="radiogroup"] {
            gap: 10px;
        }

        div[role="radiogroup"] > label {
            background-color: #111827 !important;
            border: 1px solid #1F2937 !important;
            border-radius: 10px !important;
            padding: 14px 16px !important;
            margin-bottom: 4px !important;
            width: 100% !important;
            transition: all 0.2s ease-in-out !important;
            cursor: pointer !important;
        }

        div[role="radiogroup"] > label:hover {
            border-color: #38BDF8 !important;
            background-color: #1E293B !important;
            transform: translateY(-1px);
        }

        /* Active Selected Tile Styling */
        div[role="radiogroup"] > label[data-checked="true"] {
            background-color: #1E293B !important;
            border-color: #38BDF8 !important;
            box-shadow: 0 4px 12px rgba(56, 189, 248, 0.15) !important;
        }

        div[role="radiogroup"] > label[data-checked="true"] p {
            color: #38BDF8 !important;
            font-weight: 700 !important;
        }

        /* Hide Default Radio Circles for Clean Tile Look */
        div[role="radiogroup"] [data-testid="stRadioButtonIcon"] {
            display: none !important;
        }
        </stylemock>
    """.replace("stylemock", "style"), unsafe_allow_html=True)
