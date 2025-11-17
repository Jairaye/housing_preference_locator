"""
Data preparation script for Home Locator app
Merges housing, election, gun law, population, exotic animal, and marijuana data
"""
import pandas as pd
import numpy as np
import os

def prepare_data():
    print("Loading data files...")
    
    # Check if data folder exists, if not, use current directory
    if os.path.exists('data'):
        data_path = 'data/'
    else:
        data_path = ''
        print("Note: Using files from current directory (no data/ folder found)")
    
    # 1. Load ALL housing data files
    print("Loading housing data (all bedroom types)...")
    housing_general = pd.read_csv(f'{data_path}County_zhvi_uc_sfr_tier_0.33_0.67_sm_sa_month.csv')
    
    try:
        housing_4br = pd.read_csv(f'{data_path}County_zhvi_bdrmcnt_4_uc_sfrcondo_tier_0.33_0.67_sm_sa_month (1).csv')
        print("✓ Loaded 4-bedroom data")
    except:
        print("⚠ 4-bedroom file not found")
        housing_4br = None
    
    try:
        housing_5br = pd.read_csv(f'{data_path}County_zhvi_bdrmcnt_5_uc_sfrcondo_tier_0.33_0.67_sm_sa_month (1).csv')
        print("✓ Loaded 5-bedroom data")
    except:
        print("⚠ 5-bedroom file not found")
        housing_5br = None
    
    # Process general housing
    housing_general['county_fips'] = (
        housing_general['StateCodeFIPS'].astype(str).str.zfill(2) + 
        housing_general['MunicipalCodeFIPS'].astype(str).str.zfill(3)
    ).astype(float)
    
    date_cols = [col for col in housing_general.columns if col.startswith('20')]
    housing_general['median_home_value'] = housing_general[date_cols[-1]]
    housing_general['median_home_value_all'] = housing_general['median_home_value']
    
    housing_clean = housing_general[['county_fips', 'RegionName', 'StateName', 'State', 'median_home_value_all']].copy()
    housing_clean.columns = ['county_fips', 'county_name', 'state_name', 'state_code', 'median_home_value_all']
    
    # Add 4-bedroom data
    if housing_4br is not None:
        housing_4br['county_fips'] = (
            housing_4br['StateCodeFIPS'].astype(str).str.zfill(2) + 
            housing_4br['MunicipalCodeFIPS'].astype(str).str.zfill(3)
        ).astype(float)
        date_cols_4 = [col for col in housing_4br.columns if col.startswith('20')]
        housing_4br['median_home_value_4br'] = housing_4br[date_cols_4[-1]]
        housing_clean = housing_clean.merge(
            housing_4br[['county_fips', 'median_home_value_4br']], 
            on='county_fips', how='left'
        )
    
    # Add 5-bedroom data
    if housing_5br is not None:
        housing_5br['county_fips'] = (
            housing_5br['StateCodeFIPS'].astype(str).str.zfill(2) + 
            housing_5br['MunicipalCodeFIPS'].astype(str).str.zfill(3)
        ).astype(float)
        date_cols_5 = [col for col in housing_5br.columns if col.startswith('20')]
        housing_5br['median_home_value_5br'] = housing_5br[date_cols_5[-1]]
        housing_clean = housing_clean.merge(
            housing_5br[['county_fips', 'median_home_value_5br']], 
            on='county_fips', how='left'
        )
    
    print(f"Loaded {len(housing_clean)} counties with housing data")
    
    # 2. Load and process election data
    elections = pd.read_csv(f'{data_path}countypres_2000-2024.csv')
    elec_2024 = elections[elections['year'] == 2024].copy()
    
    elec_pivot = elec_2024.pivot_table(
        index=['state_po', 'county_name', 'county_fips'],
        columns='party',
        values='candidatevotes',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    if 'DEMOCRAT' not in elec_pivot.columns:
        elec_pivot['DEMOCRAT'] = 0
    if 'REPUBLICAN' not in elec_pivot.columns:
        elec_pivot['REPUBLICAN'] = 0
        
    elec_pivot['total_votes'] = elec_pivot.get('DEMOCRAT', 0) + elec_pivot.get('REPUBLICAN', 0)
    elec_pivot['dem_pct'] = (elec_pivot.get('DEMOCRAT', 0) / elec_pivot['total_votes'] * 100).round(1)
    elec_pivot['rep_pct'] = (elec_pivot.get('REPUBLICAN', 0) / elec_pivot['total_votes'] * 100).round(1)
    elec_pivot['lean_score'] = (elec_pivot['dem_pct'] - elec_pivot['rep_pct']).round(1)
    
    elec_clean = elec_pivot[['county_fips', 'dem_pct', 'rep_pct', 'lean_score']].copy()
    print(f"Processed {len(elec_clean)} counties with 2024 election data")
    
    # 3. Load gun law grades
    gun_laws = pd.read_csv(f'{data_path}gun_law_grades_2024.csv')
    
    # 4. Load population data
    population = pd.read_csv(f'{data_path}county_population_estimates.csv')
    
    # 5. Load NEW data - exotic animals
    try:
        exotic_animals = pd.read_csv(f'{data_path}exotic_animal_laws_2024.csv')
        print(f"✓ Loaded exotic animal laws for {len(exotic_animals)} states")
    except:
        print("⚠ Exotic animal laws file not found")
        exotic_animals = None
    
    # 6. Load NEW data - marijuana
    try:
        marijuana = pd.read_csv(f'{data_path}marijuana_legality_2025.csv')
        print(f"✓ Loaded marijuana legality for {len(marijuana)} states")
    except:
        print("⚠ Marijuana legality file not found")
        marijuana = None
    
    # 7. Merge everything
    print("\nMerging datasets...")
    
    merged = housing_clean.copy()
    merged = merged.merge(elec_clean, on='county_fips', how='left')
    merged = merged.merge(gun_laws[['state_code', 'gun_law_grade', 'gun_death_rate']], 
                         left_on='state_code', right_on='state_code', how='left')
    merged = merged.merge(population[['county_fips', 'population']], 
                         on='county_fips', how='left')
    
    # Add exotic animal laws
    if exotic_animals is not None:
        merged = merged.merge(
            exotic_animals[['state_code', 'exotic_animal_rating', 'allows_primates', 'allows_big_cats', 'allows_reptiles']], 
            on='state_code', how='left'
        )
    
    # Add marijuana legality
    if marijuana is not None:
        merged = merged.merge(
            marijuana[['state_code', 'marijuana_status', 'recreational_legal', 'medical_legal', 'permissiveness_score']], 
            on='state_code', how='left'
        )
    
    # Clean up
    merged = merged.dropna(subset=['median_home_value_all'])
    
    # Create derived fields
    merged['median_home_value_all_formatted'] = merged['median_home_value_all'].apply(
        lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
    )
    
    if 'median_home_value_4br' in merged.columns:
        merged['median_home_value_4br_formatted'] = merged['median_home_value_4br'].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
        )
    
    if 'median_home_value_5br' in merged.columns:
        merged['median_home_value_5br_formatted'] = merged['median_home_value_5br'].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
        )
    
    # Political lean category
    def categorize_lean(score):
        if pd.isna(score):
            return "Unknown"
        elif score > 20:
            return "Strong Democrat"
        elif score > 5:
            return "Lean Democrat"
        elif score > -5:
            return "Swing"
        elif score > -20:
            return "Lean Republican"
        else:
            return "Strong Republican"
    
    merged['political_lean'] = merged['lean_score'].apply(categorize_lean)
    
    # Gun law category
    def categorize_gun_law(grade):
        if pd.isna(grade):
            return "Unknown"
        elif grade in ['A+', 'A', 'A-']:
            return "Strong"
        elif grade in ['B+', 'B', 'B-']:
            return "Moderate"
        elif grade in ['C+', 'C', 'C-']:
            return "Weak"
        elif grade in ['D+', 'D', 'D-']:
            return "Very Weak"
        else:
            return "Minimal"
    
    merged['gun_law_strength'] = merged['gun_law_grade'].apply(categorize_gun_law)
    
    # Save
    if not os.path.exists('data'):
        os.makedirs('data')
        print("\n✓ Created data/ folder")
    
    output_path = 'data/merged_county_data.csv'
    merged.to_csv(output_path, index=False)
    
    print(f"\n✓ Successfully merged data for {len(merged)} counties")
    print(f"✓ Saved to: {output_path}")
    
    # Print summary stats
    print("\n=== Summary Statistics ===")
    print(f"Median home value range: ${merged['median_home_value_all'].min():,.0f} - ${merged['median_home_value_all'].max():,.0f}")
    print(f"States covered: {merged['state_code'].nunique()}")
    print(f"\nPolitical lean distribution:")
    print(merged['political_lean'].value_counts())
    print(f"\nGun law strength distribution:")
    print(merged['gun_law_strength'].value_counts())
    
    if 'marijuana_status' in merged.columns:
        print(f"\nMarijuana legality distribution:")
        print(merged['marijuana_status'].value_counts())
    
    if 'exotic_animal_rating' in merged.columns:
        print(f"\nExotic animal law distribution:")
        print(merged['exotic_animal_rating'].value_counts())
    
    return merged

if __name__ == "__main__":
    df = prepare_data()