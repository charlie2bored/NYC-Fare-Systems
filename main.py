import pandas as pd
import numpy as np

# --- 1. CONFIGURATION & CONSTANTS ---
FILE_PATH = 'data/1M_Stop_Pairings.csv' # Correct path to data directory
ANNUAL_RIDERSHIP_2024 = 1194866357  # Actual total from MTA data
BASE_FARE = 2.00
PER_MILE_RATE = 0.24
CURRENT_FLAT_FARE = 2.90
EARTH_RADIUS_MILES = 3958.8

# Required column names based on the actual CSV structure
REQUIRED_COLS = [
    'origin_latitude', 'origin_longitude', 
    'destination_latitude', 'destination_longitude', 
    'estimated_average_ridership'
]

# --- 2. DATA LOADING & VALIDATION ---
def load_and_validate_data(path):
    try:
        df = pd.read_csv(path)
        print(f"Data loaded successfully. Shape: {df.shape}")
        print(f"Available columns: {df.columns.tolist()}")
        
        # Check for missing columns
        missing = [col for col in REQUIRED_COLS if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns in CSV: {missing}")
        
        # Clean Data: Remove rows with missing coordinates or zero ridership
        initial_count = len(df)
        df = df.dropna(subset=REQUIRED_COLS)
        df = df[df['estimated_average_ridership'] > 0]
        
        # Convert ridership to float to preserve decimals (critical for accuracy)
        df['estimated_average_ridership'] = pd.to_numeric(df['estimated_average_ridership'], errors='coerce')
        
        print(f"Data Cleaned: {len(df)}/{initial_count} rows valid.")
        return df
    except Exception as e:
        print(f"Critical Error: {e}")
        exit()

# --- 3. CORE CALCULATIONS ---
def calculate_haversine(lat1, lon1, lat2, lon2):
    """Accurate distance calculation using Haversine formula"""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    return 2 * np.arcsin(np.sqrt(a)) * EARTH_RADIUS_MILES

# Execute
print("Starting MTA Fare Analysis...")
df = load_and_validate_data(FILE_PATH)

# Calculate Distance & Fare
print("Calculating distances and fares...")
df['distance_mi'] = calculate_haversine(
    df['origin_latitude'], df['origin_longitude'],
    df['destination_latitude'], df['destination_longitude']
)
df['proposed_fare'] = BASE_FARE + (df['distance_mi'] * PER_MILE_RATE)

# --- 4. REVENUE ANNUALIZATION ---
# Calculate scaling factor: Actual Annual Rides / Sum of Sample Hourly Rides
sample_hourly_sum = df['estimated_average_ridership'].sum()
annual_scale_factor = ANNUAL_RIDERSHIP_2024 / sample_hourly_sum

print(f"Sample hourly ridership sum: {sample_hourly_sum:,.0f}")
print(f"Annual scaling factor: {annual_scale_factor:,.2f}x")

# Proposed Annual Revenue
df['annual_rev_proposed'] = (df['proposed_fare'] * df['estimated_average_ridership']) * annual_scale_factor

# Current Annual Revenue (Flat $2.90)
df['annual_rev_flat'] = (CURRENT_FLAT_FARE * df['estimated_average_ridership']) * annual_scale_factor

# --- 5. FINAL RESULTS ---
total_proposed = df['annual_rev_proposed'].sum()
total_flat = df['annual_rev_flat'].sum()

print("\n" + "="*50)
print("FINAL REVENUE PROJECTION")
print("="*50)
print(f"Proposed Model Total: ${total_proposed:,.2f}")
print(f"Current Flat Total:   ${total_flat:,.2f}")
print(f"Annual Delta:         ${total_proposed - total_flat:,.2f}")
print(f"Percentage Change:    {(total_proposed - total_flat) / total_flat * 100:+.1f}%")
print("="*50)

# Additional insights
winners = len(df[df['proposed_fare'] < CURRENT_FLAT_FARE])
losers = len(df[df['proposed_fare'] > CURRENT_FLAT_FARE])
neutral = len(df[df['proposed_fare'] == CURRENT_FLAT_FARE])

print(f"\nFare Impact Analysis:")
print(f"Winners (pay less): {winners:,} trips ({winners/len(df)*100:.1f}%)")
print(f"Losers (pay more):  {losers:,} trips ({losers/len(df)*100:.1f}%)")
print(f"Neutral (same):     {neutral:,} trips ({neutral/len(df)*100:.1f}%)")

# Save results for GitHub
output_file = 'mta_final_analysis.csv'
df.to_csv(output_file, index=False)
print(f"\nResults saved to: {output_file}")