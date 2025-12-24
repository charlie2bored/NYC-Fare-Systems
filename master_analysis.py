import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import sys

warnings.filterwarnings('ignore')

class NYCFareAnalysis:
    def __init__(self, excel_file_path=None):
        default_path = Path(r"C:\Users\iamch\OneDrive\Desktop\Data Project\NYC_Subway_Full_OD_Data.xlsx")
        self.excel_file = Path(excel_file_path) if excel_file_path else default_path
        
        # Updated with accurate MTA 2023 data
        self.MTA_ANNUAL_TRIPS = 1_700_000_000  # ~1.7 billion annual trips
        self.MTA_ANNUAL_REVENUE = 3_800_000_000  # ~$3.8 billion annual fare revenue 
        self.CURRENT_FARE = 2.90
        self.BASE_FARE_MEDIUM = 2.00
        self.RATE_PER_KM_MEDIUM = 0.15 # Matches HTML presentation: $2.00 + $0.15/km

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        return 2 * R * np.arcsin(np.sqrt(np.sin((lat2 - lat1)/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1)/2)**2))

    def run_complete_analysis(self):
        print("🚀 Processing 1,000,000 rows...")
        self.od_data = pd.read_excel(self.excel_file, sheet_name=0)
        
        # Phase 3: Distances
        coords = ['origin_latitude', 'origin_longitude', 'destination_latitude', 'destination_longitude']
        for col in coords: self.od_data[col] = pd.to_numeric(self.od_data[col], errors='coerce')
        
        self.od_data['distance_km'] = self.haversine_distance(self.od_data['origin_latitude'], self.od_data['origin_longitude'], self.od_data['destination_latitude'], self.od_data['destination_longitude'])
        self.od_data['distance_miles'] = self.od_data['distance_km'] * 0.621371
        
        # Phase 4/5/6: Fares
        ridership = pd.to_numeric(self.od_data['estimated_average_ridership'], errors='coerce').fillna(0)
        self.od_data['current_revenue'] = ridership * self.CURRENT_FARE
        self.od_data['fare_dist_based'] = self.BASE_FARE_MEDIUM + (self.od_data['distance_km'] * self.RATE_PER_KM_MEDIUM)
        self.od_data['dist_revenue'] = ridership * self.od_data['fare_dist_based']
        self.od_data['fare_change'] = self.od_data['fare_dist_based'] - self.CURRENT_FARE

        # Phase 7/8/9: Better Borough Detection
        def get_borough(name):
            name = str(name)
            if 'Bk' in name or 'Brooklyn' in name: return 'Brooklyn'
            if 'Bx' in name or 'Bronx' in name: return 'Bronx'
            if 'M' in name or 'Manhattan' in name: return 'Manhattan'
            if 'Q' in name or 'Queens' in name: return 'Queens'
            if 'SI' in name or 'Staten' in name: return 'Staten Island'
            return 'Other/Unknown'

        self.od_data['Origin_Borough'] = self.od_data['origin_station_complex_name'].apply(get_borough)
        self.od_data['Dest_Borough'] = self.od_data['destination_station_complex_name'].apply(get_borough)

        # Phase 10: Save
        output_path = self.excel_file.parent / "Final_Fare_Project_Results.xlsx"
        print(f"💾 Saving to {output_path}...")
        
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Sheet 1: The big data
            self.od_data.to_excel(writer, sheet_name='Main_Analysis', index=False)
            
            # Sheet 2: Borough Impact
            b_matrix = self.od_data.pivot_table(values='fare_change', index='Origin_Borough', columns='Dest_Borough', aggfunc='mean')
            b_matrix.to_excel(writer, sheet_name='Borough_Impact_Matrix')
            
            # Sheet 3: Equity
            self.od_data.groupby(pd.cut(self.od_data['distance_miles'], [0,3,7,12,100]))['fare_change'].mean().to_excel(writer, sheet_name='Equity_Analysis')

        print("✅ DONE! You are ready to make your charts.")

if __name__ == "__main__":
    NYCFareAnalysis().run_complete_analysis()