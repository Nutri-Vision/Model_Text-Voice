import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Nutri-Vision Text Analyzer",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2E8B57;
        margin: 0.5rem 0;
    }
    .food-item {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .error-message {
        background-color: #ffebee;
        color: #c62828;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #c62828;
    }
    .success-message {
        background-color: #e8f5e8;
        color: #2e7d32;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #2e7d32;
    }
</style>
""", unsafe_allow_html=True)

def check_api_status():
    """Check if the FastAPI server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def analyze_food_text(text):
    """Send text to FastAPI backend for analysis"""
    try:
        payload = {"description": text}
        response = requests.post(
            f"{API_BASE_URL}/analyze-text",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            error_detail = response.json().get("detail", f"HTTP {response.status_code}")
            return None, f"API Error: {error_detail}"
    
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to API server. Make sure it's running on http://localhost:8000"
    except requests.exceptions.Timeout:
        return None, "Request timed out. The analysis is taking too long."
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def create_nutrition_chart(totals):
    """Create a donut chart for macronutrients"""
    macros = {
        'Protein': totals.get('protein_g', 0),
        'Carbs': totals.get('carbs_g', 0), 
        'Fat': totals.get('fat_g', 0)
    }
    
    # Filter out zero values
    macros = {k: v for k, v in macros.items() if v > 0}
    
    if not macros:
        return None
    
    fig = go.Figure(data=[go.Pie(
        labels=list(macros.keys()),
        values=list(macros.values()),
        hole=0.4,
        marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1']
    )])
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>%{value}g<br>%{percent}<extra></extra>'
    )
    
    fig.update_layout(
        title={
            'text': "Macronutrient Distribution",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2E8B57'}
        },
        font=dict(size=12),
        showlegend=True,
        width=400,
        height=400,
        margin=dict(t=60, b=40, l=40, r=40)
    )
    
    return fig

def create_calories_gauge(calories):
    """Create a gauge chart for calories"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = calories,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Calories", 'font': {'size': 18, 'color': '#2E8B57'}},
        gauge = {
            'axis': {'range': [None, max(2000, calories * 1.2)]},
            'bar': {'color': "#2E8B57"},
            'steps': [
                {'range': [0, 500], 'color': "lightgray"},
                {'range': [500, 1000], 'color': "gray"},
                {'range': [1000, 1500], 'color': "lightcoral"},
                {'range': [1500, 2000], 'color': "coral"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 2000
            }
        }
    ))
    
    fig.update_layout(
        width=400,
        height=400,
        margin=dict(t=60, b=40, l=40, r=40)
    )
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">🥗 Nutri-Vision Text Analyzer</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        1. **Start the API server** first:
           ```bash
           uvicorn app:app --reload
           ```
        
        2. **Enter your food description** in natural language
        
        3. **Click 'Analyze'** to get nutrition information
        
        **Examples:**
        - "I had 2 slices of bread and an apple"
        - "Lunch: 200g chicken breast with rice"
        - "Breakfast was oatmeal with banana and milk"
        """)
        
        # API Status Check
        st.header("🔧 System Status")
        if check_api_status():
            st.markdown('<div class="success-message">✅ API Server: Online</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-message">❌ API Server: Offline</div>', unsafe_allow_html=True)
            st.markdown("Start the server with: `uvicorn app:app --reload`")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 Food Description")
        
        # Text input
        text_input = st.text_area(
            "Describe what you ate:",
            height=150,
            placeholder="Example: I had 2 slices of whole wheat bread with peanut butter and a banana for breakfast",
            help="Describe your meal in natural language. Include quantities when possible."
        )
        
        # Sample texts
        st.subheader("📚 Try these examples:")
        col_ex1, col_ex2, col_ex3 = st.columns(3)
        
        sample_texts = [
            "2 slices of bread and 1 apple",
            "200g chicken breast with 1 cup rice", 
            "Bowl of oatmeal with banana and milk"
        ]
        
        for i, (col, sample) in enumerate(zip([col_ex1, col_ex2, col_ex3], sample_texts)):
            with col:
                if st.button(f"Example {i+1}", key=f"sample_{i}", use_container_width=True):
                    st.session_state.text_input = sample
                st.caption(sample)
    
    with col2:
        st.header("⚙️ Analysis Options")
        
        # Analysis button
        analyze_button = st.button(
            "🔍 Analyze Nutrition",
            type="primary",
            use_container_width=True,
            disabled=not text_input.strip()
        )
        
        # Options
        show_details = st.checkbox("Show detailed breakdown", value=True)
        show_charts = st.checkbox("Show nutrition charts", value=True)
    
    # Handle sample text selection
    if 'text_input' in st.session_state:
        text_input = st.session_state.text_input
        del st.session_state.text_input
        st.experimental_rerun()
    
    # Analysis results
    if analyze_button and text_input.strip():
        with st.spinner("🔄 Analyzing your food description..."):
            result, error = analyze_food_text(text_input.strip())
        
        if error:
            st.markdown(f'<div class="error-message">❌ {error}</div>', unsafe_allow_html=True)
        
        elif result:
            st.success("✅ Analysis complete!")
            
            # Extract data
            items = result.get('items', [])
            totals = result.get('totals', {})
            
            # Display totals prominently
            st.header("📊 Nutrition Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="🔥 Calories",
                    value=f"{totals.get('calories', 0):.1f}",
                    help="Total energy content"
                )
            
            with col2:
                st.metric(
                    label="🥩 Protein",
                    value=f"{totals.get('protein_g', 0):.1f}g",
                    help="Protein content in grams"
                )
            
            with col3:
                st.metric(
                    label="🍞 Carbs", 
                    value=f"{totals.get('carbs_g', 0):.1f}g",
                    help="Carbohydrate content in grams"
                )
            
            with col4:
                st.metric(
                    label="🧈 Fat",
                    value=f"{totals.get('fat_g', 0):.1f}g", 
                    help="Fat content in grams"
                )
            
            # Charts
            if show_charts and any(totals.get(k, 0) > 0 for k in ['calories', 'protein_g', 'carbs_g', 'fat_g']):
                st.header("📈 Nutrition Visualization")
                
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    calories_chart = create_calories_gauge(totals.get('calories', 0))
                    if calories_chart:
                        st.plotly_chart(calories_chart, use_container_width=True)
                
                with chart_col2:
                    macro_chart = create_nutrition_chart(totals)
                    if macro_chart:
                        st.plotly_chart(macro_chart, use_container_width=True)
            
            # Detailed breakdown
            if show_details and items:
                st.header("🔍 Detailed Food Items")
                
                for i, item in enumerate(items):
                    with st.expander(f"📦 {item.get('ingredient', 'Unknown')} ({item.get('quantity', 0)} {item.get('unit', 'serving')})", expanded=False):
                        
                        if item.get('note'):
                            st.warning(f"⚠️ {item['note']}")
                        
                        macros = item.get('macros', {})
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Calories", f"{macros.get('calories', 0):.1f}")
                        with col2:
                            st.metric("Protein", f"{macros.get('protein_g', 0):.1f}g")
                        with col3:
                            st.metric("Carbs", f"{macros.get('carbs_g', 0):.1f}g")
                        with col4:
                            st.metric("Fat", f"{macros.get('fat_g', 0):.1f}g")
                        
                        if item.get('usda_match_score'):
                            st.info(f"🎯 USDA Match Confidence: {item['usda_match_score']:.1%}")
            
            # Export option
            st.header("💾 Export Results")
            
            # Prepare data for export
            export_data = {
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'input_text': text_input,
                'total_nutrition': totals,
                'food_items': items
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                # JSON download
                st.download_button(
                    label="📄 Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"nutrition_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col2:
                # CSV download (items only)
                if items:
                    df_items = pd.DataFrame(items)
                    # Flatten macros
                    for macro in ['calories', 'protein_g', 'carbs_g', 'fat_g']:
                        df_items[macro] = df_items['macros'].apply(lambda x: x.get(macro, 0) if isinstance(x, dict) else 0)
                    
                    df_items = df_items.drop('macros', axis=1)
                    
                    st.download_button(
                        label="📊 Download CSV", 
                        data=df_items.to_csv(index=False),
                        file_name=f"nutrition_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

    # Footer
    st.markdown("---")
    st.markdown(
        "Built with ❤️ using Streamlit • Powered by USDA FoodData Central API",
        help="This app uses natural language processing to extract food items and nutritional information"
    )

if __name__ == "__main__":
    main()