"""
Home Locator - Find your ideal place to live
Filter by housing costs, politics, gun laws, population, exotic animals, and marijuana laws
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="Home Locator",
    page_icon="🏠",
    layout="wide"
)

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('data/merged_county_data.csv')

df = load_data()

# Header
st.title("🏠 Home Locator")
st.markdown("Find your ideal county based on housing, politics, gun laws, exotic pets, marijuana, and more")

# Sidebar filters
st.sidebar.header("Filter Counties")

# NEW: Bedroom type selector
st.sidebar.subheader("🏡 Home Type")
bedroom_options = ["All Homes"]
if 'median_home_value_4br' in df.columns:
    bedroom_options.append("4 Bedrooms")
if 'median_home_value_5br' in df.columns:
    bedroom_options.append("5+ Bedrooms")

bedroom_type = st.sidebar.selectbox(
    "Bedroom Count",
    options=bedroom_options
)

# Determine which price column to use
if bedroom_type == "4 Bedrooms":
    price_col = 'median_home_value_4br'
    price_col_formatted = 'median_home_value_4br_formatted'
elif bedroom_type == "5+ Bedrooms":
    price_col = 'median_home_value_5br'
    price_col_formatted = 'median_home_value_5br_formatted'
else:
    price_col = 'median_home_value_all'
    price_col_formatted = 'median_home_value_all_formatted'

# Filter out counties without data for selected bedroom type
df_filtered_bedrooms = df[df[price_col].notna()].copy()

# Price filter
st.sidebar.subheader("💰 Home Value")
price_min, price_max = st.sidebar.slider(
    "Price Range",
    min_value=int(df_filtered_bedrooms[price_col].min()),
    max_value=int(df_filtered_bedrooms[price_col].max()),
    value=(int(df_filtered_bedrooms[price_col].min()), int(df_filtered_bedrooms[price_col].max())),
    step=10000,
    format="$%d"
)

# Political filters
st.sidebar.subheader("🗳️ Politics")
lean_categories = ['Strong Democrat', 'Lean Democrat', 'Swing', 'Lean Republican', 'Strong Republican', 'Unknown']
selected_leans = st.sidebar.multiselect(
    "Political Lean",
    options=lean_categories,
    default=lean_categories
)

# Gun law filter
st.sidebar.subheader("🔫 Gun Laws")
gun_law_categories = ['Strong', 'Moderate', 'Weak', 'Very Weak', 'Minimal', 'Unknown']
selected_gun_laws = st.sidebar.multiselect(
    "Gun Law Strength",
    options=gun_law_categories,
    default=gun_law_categories
)

# NEW: Marijuana filter
if 'marijuana_status' in df.columns:
    st.sidebar.subheader("🌿 Marijuana")
    marijuana_options = sorted(df['marijuana_status'].dropna().unique())
    selected_marijuana = st.sidebar.multiselect(
        "Marijuana Legality",
        options=marijuana_options,
        default=marijuana_options
    )

# NEW: Exotic animal filters
if 'exotic_animal_rating' in df.columns:
    st.sidebar.subheader("🦎 Exotic Animals")
    exotic_ratings = sorted(df['exotic_animal_rating'].dropna().unique())
    selected_exotic_ratings = st.sidebar.multiselect(
        "Overall Permissiveness",
        options=exotic_ratings,
        default=exotic_ratings
    )
    
    # Individual animal filters
    with st.sidebar.expander("🐒 Specific Animals"):
        filter_primates = st.checkbox("Allow Primates", value=False)
        filter_big_cats = st.checkbox("Allow Big Cats", value=False)
        filter_reptiles = st.checkbox("Allow Exotic Reptiles", value=False)

# Population filter
st.sidebar.subheader("👥 Population")
pop_min, pop_max = st.sidebar.slider(
    "Population Range",
    min_value=int(df['population'].min()),
    max_value=int(df['population'].max()),
    value=(int(df['population'].min()), int(df['population'].max())),
    step=10000
)

# State filter
st.sidebar.subheader("📍 Location")
states = sorted(df['state_name'].unique())
selected_states = st.sidebar.multiselect(
    "States",
    options=states,
    default=[]
)

# Apply filters
filtered_df = df_filtered_bedrooms[
    (df_filtered_bedrooms[price_col] >= price_min) &
    (df_filtered_bedrooms[price_col] <= price_max) &
    (df_filtered_bedrooms['political_lean'].isin(selected_leans)) &
    (df_filtered_bedrooms['gun_law_strength'].isin(selected_gun_laws)) &
    (df_filtered_bedrooms['population'] >= pop_min) &
    (df_filtered_bedrooms['population'] <= pop_max)
]

# Marijuana filter
if 'marijuana_status' in df.columns:
    filtered_df = filtered_df[filtered_df['marijuana_status'].isin(selected_marijuana)]

# Exotic animal filters
if 'exotic_animal_rating' in df.columns:
    filtered_df = filtered_df[filtered_df['exotic_animal_rating'].isin(selected_exotic_ratings)]
    
    # Individual animal filters
    if filter_primates and 'allows_primates' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['allows_primates'].isin(['Yes', 'Limited'])]
    if filter_big_cats and 'allows_big_cats' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['allows_big_cats'].isin(['Yes', 'Limited'])]
    if filter_reptiles and 'allows_reptiles' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['allows_reptiles'] == 'Yes']

if selected_states:
    filtered_df = filtered_df[filtered_df['state_name'].isin(selected_states)]

# Main content
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Counties Found", len(filtered_df))
with col2:
    avg_price = filtered_df[price_col].mean()
    st.metric(f"Avg {bedroom_type} Price", f"${avg_price:,.0f}")
with col3:
    avg_pop = filtered_df['population'].mean()
    st.metric("Avg Population", f"{avg_pop:,.0f}")
with col4:
    states_count = filtered_df['state_code'].nunique()
    st.metric("States", states_count)

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Table", "🗺️ Map View", "📈 Analysis", "ℹ️ About"])

with tab1:
    st.subheader(f"Filtered Counties - {bedroom_type}")
    
    # Build display columns based on available data
    display_cols = ['county_name', 'state_code', price_col_formatted, 'population', 'political_lean', 'gun_law_grade', 'lean_score']
    display_names = ['County', 'State', f'{bedroom_type} Value', 'Population', 'Political Lean', 'Gun Grade', 'Lean Score']
    
    if 'marijuana_status' in filtered_df.columns:
        display_cols.append('marijuana_status')
        display_names.append('Marijuana')
    
    if 'exotic_animal_rating' in filtered_df.columns:
        display_cols.append('exotic_animal_rating')
        display_names.append('Exotic Pets')
    
    display_df = filtered_df[display_cols].copy()
    display_df.columns = display_names
    
    # Sort options
    sort_by = st.selectbox(
        "Sort by:",
        options=display_names
    )
    
    display_df = display_df.sort_values(by=sort_by, ascending=(sort_by == 'County'))
    
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        height=500
    )
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download Results as CSV",
        data=csv,
        file_name="home_locator_results.csv",
        mime="text/csv"
    )

with tab2:
    st.subheader("County Map")
    
    if len(filtered_df) > 0:
        fig = px.scatter_geo(
            filtered_df,
            locations='state_code',
            locationmode='USA-states',
            color=price_col,
            hover_name='county_name',
            hover_data={
                'state_code': False,
                price_col: ':$,.0f',
                'population': ':,',
                'political_lean': True,
                'gun_law_grade': True,
                'marijuana_status': True if 'marijuana_status' in filtered_df.columns else False,
                'exotic_animal_rating': True if 'exotic_animal_rating' in filtered_df.columns else False
            },
            size='population',
            color_continuous_scale='Viridis',
            scope='usa',
            title=f'{len(filtered_df)} Counties Matching Your Criteria'
        )
        
        fig.update_layout(
            height=600,
            geo=dict(
                scope='usa',
                showland=True,
                landcolor='rgb(243, 243, 243)',
                coastlinecolor='rgb(204, 204, 204)',
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No counties match your filters. Try adjusting your criteria.")

with tab3:
    st.subheader("Analysis")
    
    if len(filtered_df) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            # Political lean distribution
            lean_counts = filtered_df['political_lean'].value_counts()
            fig1 = px.pie(
                values=lean_counts.values,
                names=lean_counts.index,
                title="Political Lean Distribution"
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Gun law grade distribution
            gun_counts = filtered_df['gun_law_grade'].value_counts().sort_index()
            fig2 = px.bar(
                x=gun_counts.index,
                y=gun_counts.values,
                title="Gun Law Grade Distribution",
                labels={'x': 'Grade', 'y': 'Number of Counties'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # NEW: Marijuana & Exotic Animals charts
        if 'marijuana_status' in filtered_df.columns and 'exotic_animal_rating' in filtered_df.columns:
            col3, col4 = st.columns(2)
            
            with col3:
                marijuana_counts = filtered_df['marijuana_status'].value_counts()
                fig_mj = px.bar(
                    x=marijuana_counts.index,
                    y=marijuana_counts.values,
                    title="Marijuana Legality Distribution",
                    labels={'x': 'Status', 'y': 'Number of Counties'}
                )
                st.plotly_chart(fig_mj, use_container_width=True)
            
            with col4:
                exotic_counts = filtered_df['exotic_animal_rating'].value_counts()
                fig_ex = px.bar(
                    x=exotic_counts.index,
                    y=exotic_counts.values,
                    title="Exotic Pet Laws Distribution",
                    labels={'x': 'Permissiveness', 'y': 'Number of Counties'}
                )
                st.plotly_chart(fig_ex, use_container_width=True)
        
        # Price vs Population scatter
        fig3 = px.scatter(
            filtered_df,
            x='population',
            y=price_col,
            color='political_lean',
            hover_name='county_name',
            title=f'{bedroom_type} Value vs Population',
            labels={
                'population': 'Population',
                price_col: f'{bedroom_type} Median Value ($)'
            }
        )
        fig3.update_xaxes(type='log')
        st.plotly_chart(fig3, use_container_width=True)
        
        # Top 10 affordable counties
        st.subheader(f"Top 10 Most Affordable Counties - {bedroom_type}")
        affordable_cols = ['county_name', 'state_code', price_col_formatted, 'population', 'political_lean', 'gun_law_grade']
        affordable_names = ['County', 'State', 'Home Value', 'Population', 'Political Lean', 'Gun Grade']
        
        affordable = filtered_df.nsmallest(10, price_col)[affordable_cols]
        affordable.columns = affordable_names
        st.dataframe(affordable, hide_index=True, use_container_width=True)
    else:
        st.warning("No counties to analyze. Adjust your filters.")

with tab4:
    st.subheader("About This Tool")
    st.markdown("""
    This home locator helps you find counties that match your lifestyle preferences.
    
    **Data Sources:**
    - **Housing**: Zillow Home Value Index (ZHVI) - Oct 2025
    - **Politics**: MIT Election Data Lab - 2024 Presidential Results
    - **Gun Laws**: Giffords Law Center Annual Scorecard 2024
    - **Marijuana**: DISA Global Solutions - 2025 State Laws
    - **Exotic Pets**: FindLaw & Born Free USA - 2024 Regulations
    - **Population**: US Census Bureau Estimates 2024
    
    **Bedroom Options:**
    - All Homes: General single-family residences
    - 4 Bedrooms: Median prices for 4BR homes
    - 5+ Bedrooms: Median prices for 5+ BR homes
    
    **Lean Score Explained:**
    The "Lean Score" = Democrat % - Republican %
    - Positive scores = Democrat-leaning
    - Negative scores = Republican-leaning
    - Near zero = Swing counties
    
    **Future Enhancements:**
    🔜 Border county information (neighboring state data)
    🔜 Cost of living indices
    🔜 Climate data
    🔜 School ratings
    """)
    
    st.info("💡 **Tip**: Use the sidebar filters to narrow down counties that match your specific needs!")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Stats")
st.sidebar.markdown(f"""
- **Total Counties**: {len(df):,}
- **States**: 50 + DC
- **Data Updated**: November 2025
""")