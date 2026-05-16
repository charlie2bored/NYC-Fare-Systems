# NYC Subway Fare Analysis: Distance-Based vs Flat Fare Systems

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![pandas](https://img.shields.io/badge/pandas-1.3+-orange.svg)](https://pandas.pydata.org/)
[![matplotlib](https://img.shields.io/badge/matplotlib-3.5+-green.svg)](https://matplotlib.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📊 Overview

This comprehensive analysis examines whether New York City's current flat subway fare system ($2.90 per ride) should be replaced with distance-based pricing. Using 1,000,000+ origin-destination trip records from the MTA, this study evaluates equity impacts, revenue implications, and international best practices.

**Key Finding**: Distance-based fares ($2.00 + $0.24/mile) would generate **$913 million additional annual revenue** (+26.4%) when distance is measured along the actual subway network. The original Haversine (straight-line) analysis gave +$280.5M / +8.1% — the corrected methodology shows the original under-priced long trips, so the case for distance-based pricing is ~3× stronger than first reported. 14.8% of trips become cheaper under the corrected model (vs. 29% under Haversine).

## 📁 Data Files

### Included in Repository:
- `data/Master_Stations.csv` - MTA station metadata (GTFS data)
- `data/All_Stops.csv` - Simplified station list
- `data/Fare_Structures.csv` - International fare comparisons

### Sample Data (Included)
- `data/sample_od.csv` (~2 MB, 10k rows) — stratified sample of the full OD dataset, sufficient for quick demos and CI. Run with `python main.py --od-path data/sample_od.csv`.

### Full Dataset (Download)
The full origin-destination CSV is too large for git (211 MB). It's attached to the [latest release](https://github.com/charlie2bored/NYC-Fare-Systems/releases) and downloaded by a small script:

```bash
python scripts/download_data.py
```

This pulls `data/1M_Stop_Pairings.csv`, verifies SHA256, and resumes/skips if already present.

To re-host on your own fork, override the URL:
```bash
python scripts/download_data.py --url https://your-host.example/od.csv.gz
# or
NYCFARE_OD_URL=https://your-host.example/od.csv.gz python scripts/download_data.py
```

## 🎯 Research Question

Should NYC modernize its subway fare system from a flat $2.90 fare to distance-based pricing that charges users based on service consumed?

## 📋 Quick Results

### Revenue Impact (Network distance — corrected v2)
- **Proposed Distance-Based Model**: $4.38 Billion annually
- **Current Flat Fare System**: $3.47 Billion annually
- **Annual Revenue Increase**: $913 Million (+26.4%)

### Revenue Impact (Haversine — original v1, kept for comparison)
- **Proposed**: $3.75 Billion · **Delta**: +$280.5M (+8.1%)

### Fare Impact on Riders (v2)
- **Winners (Pay Less)**: 148,410 trips (14.8%)
- **Losers (Pay More)**: 851,590 trips (85.2%)
- **Breakeven distance**: 3.75 mi (set by the fare formula, not the distance method)

## 🚀 Quick Start

### Prerequisites
```bash
pip install pandas numpy matplotlib
```

### Run the Analysis
```bash
# Quick run on the committed sample (~2s)
python main.py --od-path data/sample_od.csv

# Full run on the 1M-trip dataset (requires download_data.py first)
python main.py                                  # Haversine baseline
python main.py --distance-method network        # corrected: real subway routes
```

## 📊 Methodology

### Distance Calculation
Two methods, selectable via `--distance-method`:
- **Haversine** (great-circle): fast, vectorized, but systematically under-estimates real subway distance.
- **Network** (shortest-path along the subway graph): builds a graph from `Master_Stations.csv` — intra-line edges via 2-nearest-neighbor within each `line`, transfer edges via shared `complex_id`, auto-bridging of stranded components within 0.5 mi to capture track-level mergers (Pelham↔Lexington at 149 St, Nostrand↔Eastern Pky at Franklin Av, and 8 others the raw data doesn't mark). Origin and destination are snapped to nearest station, then Dijkstra. Trips spanning disconnected components (Staten Island, Rockaway) fall back to Haversine.

### Fare Model
- $2.00 base + $0.24 per mile
- **Annual Scaling**: Hourly ridership scaled to MTA's annual total of 1.19 billion rides (557.33×).
- **Sensitivity check** included: re-weights short trips (<2 mi) by 0.5×–1.5× to bound how much the headline number depends on whether the sample's short/long-trip mix matches the annual mix.

### Data Sources
- **MTA Origin-Destination Data**: 1,000,000+ subway trips
- **MTA GTFS Feeds**: Station coordinates and network data
- **International Comparisons**: Fare structures from global cities

## 💡 Key Insights

### 1. **Revenue Generation**
Distance-based pricing generates significant additional revenue for MTA improvements while maintaining system accessibility.

### 2. **Equity Considerations**
Short-distance commuters (29% of trips) receive immediate fare relief, while longer commutes contribute proportionally to system maintenance.

### 3. **Technology Ready**
NYC's OMNY contactless payment system can support distance-based fares with tap-in/tap-out functionality.

## 🛡️ Recommended Solution

**Distance-Based Fare System ($2.00 + $0.24/mile):**
- **Base Fare**: $2.00
- **Distance Rate**: $0.24 per mile
- **Equity Protections**: Maintain senior/disabled discounts and free transfers

**Benefits:**
- ✅ **Fair Pricing**: Users pay for service consumed
- ✅ **Revenue Positive**: +$280.5M annually for system improvements
- ✅ **Proven Technology**: OMNY system ready for implementation
- ✅ **Global Standard**: Aligns with international best practices

## 🔧 Technical Details

### Data Processing
- **Input**: Raw MTA OD data with station coordinates
- **Distance Calculation**: Haversine formula implementation
- **Fare Modeling**: Multiple scenarios with revenue calculations
- **Annual Scaling**: 557.33x factor to reach actual MTA annual ridership

### Analysis Stack
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **matplotlib**: Data visualization

## 🤝 Contributing

This is an open analysis project. Contributions welcome:

1. Fork the repository
2. Create a feature branch
3. Add your analysis or improvements
4. Submit a pull request

## 📞 Contact

**Project Author**: Charles Vargas  
**Email**: iamcharlesvargas@gmail.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**⭐ Star this repository if you found the analysis helpful!**

*This analysis demonstrates how data science can inform public policy decisions, showing that NYC's subway fare system is due for modernization to align with global best practices while maintaining equity and revenue stability.*
