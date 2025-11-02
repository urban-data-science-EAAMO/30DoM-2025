"""
Roosevelt Island Tramway Flow Map - COVID-19 Impact
#30DayMapChallenge 2025 - Flow Lines

Shows the dramatic impact of COVID-19 on tramway ridership
- Timeline: January 2019 → December 2020 (24 months)
- Watch ridership CRASH in March 2020
- Line thickness = monthly ridership
- Two-tone: Dark (residents) + Light (tourists)
- Bottom: COVID-19 intervention timeline

Upload edited.csv to Google Colab and run!
"""

# ============================================================================
# Install (run once in Colab)
# ============================================================================
# !pip install matplotlib pandas numpy -q

# ============================================================================
# Imports
# ============================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon, Rectangle
from matplotlib.patches import FancyBboxPatch
import warnings
warnings.filterwarnings('ignore')

# Styling
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Georgia', 'Times New Roman', 'Palatino', 'DejaVu Serif']
plt.rcParams['figure.dpi'] = 150

# ============================================================================
# Load 2019-2020 Data (NO AVERAGING)
# ============================================================================

def load_covid_period_data(filepath='edited.csv'):
    """
    Load CSV and filter for 2019-2020 only
    Returns monthly data for each direction
    """
    
    df = pd.read_csv(filepath)
    df['From Date'] = pd.to_datetime(df['From Date'])
    df['To Date'] = pd.to_datetime(df['To Date'])
    
    # Filter for 2019-2020 only
    df = df[(df['From Date'].dt.year >= 2019) & (df['From Date'].dt.year <= 2020)]
    
    # Filter tram stations
    tram_df = df[df['Remote Station ID'].isin(['R468', 'R469'])].copy()
    
    # DEBUG: Check how many weekly records we have
    print(f"Total weekly records in 2019-2020: {len(tram_df)}")
    print(f"  R468 (Manhattan→Island): {len(tram_df[tram_df['Remote Station ID']=='R468'])}")
    print(f"  R469 (Island→Manhattan): {len(tram_df[tram_df['Remote Station ID']=='R469'])}")
    
    # Extract year and month
    tram_df['Year'] = tram_df['From Date'].dt.year
    tram_df['Month'] = tram_df['From Date'].dt.month
    tram_df['YearMonth'] = tram_df['From Date'].dt.to_period('M')
    
    # Clean numeric columns
    for col in tram_df.columns:
        if tram_df[col].dtype == 'object':
            try:
                tram_df[col] = pd.to_numeric(tram_df[col].str.replace(',', ''), errors='ignore')
            except:
                pass
    
    # Calculate splits
    tram_df['Tourist'] = tram_df['Full Fare']
    tram_df['Resident'] = tram_df['Total Ridership'] - tram_df['Full Fare']
    
    # DEBUG: Show records per month to verify we're summing weeks
    records_per_month = tram_df.groupby(['YearMonth', 'Remote Station ID']).size().reset_index(name='weekly_records')
    avg_weeks = records_per_month['weekly_records'].mean()
    print(f"\nWeekly records per month (average): {avg_weeks:.1f}")
    print(f"  Expected: ~4-5 weeks per month")
    print(f"  Range: {records_per_month['weekly_records'].min()} to {records_per_month['weekly_records'].max()}")
    
    # Aggregate by YearMonth and direction (sum all weeks in each month)
    monthly = tram_df.groupby(['YearMonth', 'Year', 'Month', 'Remote Station ID']).agg({
        'Total Ridership': 'sum',  # SUM for the month, not average
        'Tourist': 'sum',
        'Resident': 'sum'
    }).reset_index()
    
    # DEBUG: Verify aggregation worked
    print(f"\nAfter aggregation to monthly:")
    print(f"  Monthly records: {len(monthly)}")
    print(f"  Expected: 48 (24 months × 2 directions)")
    
    # Show sample to verify summing
    sample_month = monthly[monthly['YearMonth'] == '2019-01']
    if len(sample_month) > 0:
        print(f"\nSample - January 2019:")
        for _, row in sample_month.iterrows():
            station = "Manhattan→Island" if row['Remote Station ID'] == 'R468' else "Island→Manhattan"
            print(f"  {station}: {row['Total Ridership']:,.0f} total riders")
    
    # Separate directions
    manhattan_to_island = monthly[monthly['Remote Station ID'] == 'R468'].sort_values('YearMonth')
    island_to_manhattan = monthly[monthly['Remote Station ID'] == 'R469'].sort_values('YearMonth')
    
    return manhattan_to_island, island_to_manhattan

# ============================================================================
# COVID Timeline Events
# ============================================================================

def get_covid_timeline():
    """
    Key COVID-19 events for NYC
    Returns dict with month index (1-24) and event description
    """
    timeline = {
        # 2019 - Normal operations
        1: ("Jan 2019", "Normal Operations", "#9BA17B"),
        12: ("Dec 2019", "Normal Operations", "#9BA17B"),
    
        # 2020 - Warnings (tan instead of bright yellow)
        13: ("Jan 2020", "Normal Operations", "#9BA17B"),
        14: ("Feb 2020", "First US Cases", "#D4C5A9"),
        
        # Lockdown (muted terracotta/rust instead of bright red)
        15: ("Mar 2020", "NYC LOCKDOWN BEGINS", "#A0522D"),
        16: ("Apr 2020", "Peak Deaths", "#8B4513"),
        
        # Reopening (pale peach/cream instead of bright orange)
        17: ("May 2020", "Phase 1 Reopening", "#D2B48C"),
        18: ("Jun 2020", "Phase 2 Reopening", "#C9B699"),
        
        # Recovery (muted blue-gray instead of bright blue)
        24: ("Dec 2020", "Vaccines Begin", "#8B9BA3")
    }
    return timeline





# ============================================================================
# Elevation Arc Function
# ============================================================================

def get_elevation_arc(x_positions):
    """
    Create elevation arc mimicking tram path
    Peak at midpoint
    """
    x_mid = (x_positions[0] + x_positions[-1]) / 2
    
    elevation = []
    for x in x_positions:
        normalized_dist = (x - x_mid) / (len(x_positions) / 2)
        height = 1 - normalized_dist**2
        elevation.append(height)
    
    return np.array(elevation)

# ============================================================================
# Create COVID Impact Flow Map
# ============================================================================

def create_covid_impact_map(manhattan_to_island, island_to_manhattan, 
                            output_file='roosevelt_tramway_covid_impact.png'):
    """
    Create Minard-style map showing COVID-19 impact on ridership
    """
    
    # Create month labels for 24 months
    month_labels = []
    for year in [2019, 2020]:
        for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
            month_labels.append(f"{month}\n'{str(year)[-2:]}")
    
    # Create figure
    fig = plt.figure(figsize=(24, 11), facecolor='#f8f8f0')
    gs = fig.add_gridspec(3, 1, height_ratios=[5, 0.2, 2], hspace=0.25)
    ax_flow = fig.add_subplot(gs[0])
    ax_covid = fig.add_subplot(gs[2])
    
    ax_flow.set_facecolor('#f8f8f0')
    
    # ========================================================================
    # Setup
    # ========================================================================
    
    # X positions for 24 months
    x_positions = np.arange(1, 25)
    
    # Y positions for flows
    y_upper_base = 8.0  # Manhattan → Roosevelt Island (TOP - west to east)
    y_lower_base = 2.0  # Roosevelt Island → Manhattan (BOTTOM - east to west)
    
    # Get elevation arc
    elevation_arc = get_elevation_arc(x_positions)
    elevation_scale = 1.5
    
    # Normalize ridership to line thickness
    all_ridership = pd.concat([
        manhattan_to_island['Total Ridership'],
        island_to_manhattan['Total Ridership']
    ])
    max_ridership = all_ridership.max()
    min_ridership = all_ridership.min()
    
    print(f"\nScaling parameters:")
    print(f"  Max ridership (used for scaling): {max_ridership:,.0f}")
    print(f"  Min ridership: {min_ridership:,.0f}")
    print(f"  This ensures both flows use the same absolute scale\n")
    
    def normalize_thickness(ridership, max_thickness=2.0, min_thickness=0.1):
        """
        Convert ridership to half-thickness using ABSOLUTE scale
        This ensures both flows are comparable - if one has 2x ridership, it's 2x as thick
        """
        if max_ridership == 0:
            return min_thickness
        # Use direct proportion from max ridership
        normalized = ridership / max_ridership
        return min_thickness + (max_thickness - min_thickness) * normalized
    
    # Colors
    
    COLOR_MAN_TO_RI_RESIDENT = '#554F3F'  # Charcoal gray
    COLOR_MAN_TO_RI_TOURIST = '#A99E81'   # Light gray

    # Roosevelt Island → Manhattan (Warm tones)
    COLOR_RI_TO_MAN_RESIDENT = '#4F3E36'  # Saddle brown
    COLOR_RI_TO_MAN_TOURIST = '#9A7E71'   # Tan/beige
    
    # ========================================================================
    # Manhattan → Roosevelt Island (UPPER FLOW)
    # ========================================================================
    
    print("Creating Manhattan → Roosevelt Island flow (UPPER)...")
    
    # Get monthly data for all 24 months
    upper_total = []
    upper_tourist = []
    
    # Ensure we have exactly 24 months
    all_periods = pd.period_range(start='2019-01', end='2020-12', freq='M')
    
    for period in all_periods:
        month_data = manhattan_to_island[manhattan_to_island['YearMonth'] == period]  # CHANGED: was island_to_manhattan
        if len(month_data) > 0:
            upper_total.append(month_data['Total Ridership'].values[0])
            upper_tourist.append(month_data['Tourist'].values[0])
        else:
            # Handle missing data
            upper_total.append(0)
            upper_tourist.append(0)
    
    upper_total = np.array(upper_total)
    upper_tourist = np.array(upper_tourist)
    
    # DEBUG: Show ridership values
    print(f"  Upper flow (R469) ridership range: {upper_total.min():,.0f} to {upper_total.max():,.0f}")
    print(f"  Sample values - Jan 2019: {upper_total[0]:,.0f}, Mar 2020: {upper_total[14]:,.0f}")
    
    # Calculate thicknesses
    upper_half_thickness = np.array([normalize_thickness(t) for t in upper_total])
    
    # Apply elevation arc
    y_upper_with_elevation = y_upper_base + elevation_arc * elevation_scale
    
    # Create RESIDENT layer polygon
    upper_top = []
    upper_bottom = []
    
    for i, (x, y_base, thickness) in enumerate(zip(x_positions, y_upper_with_elevation, upper_half_thickness)):
        upper_top.append([x, y_base + thickness])
        upper_bottom.insert(0, [x, y_base - thickness])
    
    resident_polygon_upper = Polygon(
        upper_top + upper_bottom,
        facecolor=COLOR_MAN_TO_RI_RESIDENT,  # CHANGED: Blue for Manhattan→RI
        edgecolor='white',
        linewidth=1.5,
        alpha=0.9,
        zorder=10
    )
    ax_flow.add_patch(resident_polygon_upper)
    
    # Create TOURIST layer
    tourist_top_upper = []
    tourist_bottom_upper = []
    
    for i, (x, y_base, thickness) in enumerate(zip(x_positions, y_upper_with_elevation, upper_half_thickness)):
        tourist_ratio = upper_tourist[i] / upper_total[i] if upper_total[i] > 0 else 0
        tourist_thickness = thickness * tourist_ratio
        
        tourist_top_upper.append([x, y_base + thickness])
        tourist_bottom_upper.insert(0, [x, y_base + thickness - tourist_thickness])
    
    tourist_polygon_upper = Polygon(
        tourist_top_upper + tourist_bottom_upper,
        facecolor=COLOR_MAN_TO_RI_TOURIST,  # CHANGED: Light blue for Manhattan→RI tourists
        edgecolor=None,
        alpha=0.95,
        zorder=11
    )
    ax_flow.add_patch(tourist_polygon_upper)
    
    # ========================================================================
    # Roosevelt Island → Manhattan (LOWER FLOW)
    # ========================================================================
    
    print("Creating Roosevelt Island → Manhattan flow (LOWER)...")
    
    lower_total = []
    lower_tourist = []
    
    for period in all_periods:
        month_data = island_to_manhattan[island_to_manhattan['YearMonth'] == period]  # CHANGED: was manhattan_to_island
        if len(month_data) > 0:
            lower_total.append(month_data['Total Ridership'].values[0])
            lower_tourist.append(month_data['Tourist'].values[0])
        else:
            lower_total.append(0)
            lower_tourist.append(0)
    
    lower_total = np.array(lower_total)
    lower_tourist = np.array(lower_tourist)

    # DEBUG: Show ridership values
    print(f"  Lower flow (R468) ridership range: {lower_total.min():,.0f} to {lower_total.max():,.0f}")
    print(f"  Sample values - Jan 2019: {lower_total[0]:,.0f}, Mar 2020: {lower_total[14]:,.0f}")
    
    # Calculate thicknesses
    lower_half_thickness = np.array([normalize_thickness(t) for t in lower_total])
    
    # Apply elevation arc
    y_lower_with_elevation = y_lower_base + elevation_arc * elevation_scale
    
    # Create RESIDENT layer
    lower_top = []
    lower_bottom = []
    
    for i, (x, y_base, thickness) in enumerate(zip(x_positions, y_lower_with_elevation, lower_half_thickness)):
        lower_top.append([x, y_base + thickness])
        lower_bottom.insert(0, [x, y_base - thickness])
    
    resident_polygon_lower = Polygon(
        lower_top + lower_bottom,
        facecolor=COLOR_RI_TO_MAN_RESIDENT,  # CHANGED: Orange for RI→Manhattan
        edgecolor='white',
        linewidth=1.5,
        alpha=0.9,
        zorder=10
    )
    ax_flow.add_patch(resident_polygon_lower)
    
    # Create TOURIST layer
    tourist_top_lower = []
    tourist_bottom_lower = []
    
    for i, (x, y_base, thickness) in enumerate(zip(x_positions, y_lower_with_elevation, lower_half_thickness)):
        tourist_ratio = lower_tourist[i] / lower_total[i] if lower_total[i] > 0 else 0
        tourist_thickness = thickness * tourist_ratio
        
        tourist_top_lower.append([x, y_base + thickness])
        tourist_bottom_lower.insert(0, [x, y_base + thickness - tourist_thickness])
    
    tourist_polygon_lower = Polygon(
        tourist_top_lower + tourist_bottom_lower,
        facecolor=COLOR_RI_TO_MAN_TOURIST,  # CHANGED: Light orange for RI→Manhattan tourists
        edgecolor=None,
        alpha=0.95,
        zorder=11
    )
    ax_flow.add_patch(tourist_polygon_lower)
    
    
    
    # ========================================================================
    # Labels and Annotations
    # ========================================================================
    

    
    # ========================================================================
    # X-Axis: Year labels with alternating months
    # ========================================================================
    
    # Year labels - centered over their 12 months
    # 2019: months 1-12 (center at 6.5)
    # 2020: months 13-24 (center at 18.5)
    ax_flow.text(6.5, -0.3, '2019', ha='center', va='top',
                fontsize=12, fontweight='bold', color='#2c3e50')
    ax_flow.text(18.5, -0.3, '2020', ha='center', va='top',
                fontsize=12, fontweight='bold', color='#2c3e50')
    
    # Subtle horizontal separators under year labels
    ax_flow.plot([1, 12], [-0.6, -0.6], color='#2c3e50', linewidth=1, alpha=0.3)
    ax_flow.plot([13, 24], [-0.6, -0.6], color='#2c3e50', linewidth=1, alpha=0.3)
    
    # Alternating month labels (Jan, Mar, May, Jul, Sep, Nov)
    month_names_short = ['Jan', 'Mar', 'May', 'Jul', 'Sep', 'Nov']
    
    # 2019 months (positions 1, 3, 5, 7, 9, 11)
    for i, month_name in enumerate(month_names_short):
        month_pos = 1 + i * 2  # 1, 3, 5, 7, 9, 11
        ax_flow.text(month_pos, -0.9, month_name, ha='center', va='top',
                    fontsize=10, fontweight='normal', color='#2c3e50')
    
    # 2020 months (positions 13, 15, 17, 19, 21, 23)
    for i, month_name in enumerate(month_names_short):
        month_pos = 13 + i * 2  # 13, 15, 17, 19, 21, 23
        ax_flow.text(month_pos, -0.9, month_name, ha='center', va='top',
                    fontsize=10, fontweight='normal', color='#2c3e50')
    
    # Add key ridership annotations
    key_months = [2, 6, 10, 14, 15, 18, 22]  # Mar 2019, Mar 2020, Apr 2020, Dec 2020
    
    for idx in key_months:
        x = x_positions[idx]
        
        # Upper flow annotation
        val_upper = upper_total[idx]
        y_upper = y_upper_with_elevation[idx] + upper_half_thickness[idx]
        
        if val_upper > 0:
            ax_flow.text(x, y_upper + 0.5, f'{val_upper:,.0f}',
                        ha='center', va='bottom', fontsize=12,
                        fontweight='bold', color=COLOR_MAN_TO_RI_RESIDENT)
        
        # Lower flow annotation
        val_lower = lower_total[idx]
        y_lower = y_lower_with_elevation[idx] - lower_half_thickness[idx]
        
        if val_lower > 0:
            ax_flow.text(x, y_lower - 0.5, f'{val_lower:,.0f}',
                        ha='center', va='top', fontsize=12,
                        fontweight='bold', color=COLOR_RI_TO_MAN_RESIDENT)
    
    # ========================================================================
    # Styling
    # ========================================================================
    
    ax_flow.set_xlim(0, 25)
    ax_flow.set_ylim(-1.5, 12.5)  # Extended bottom margin for new x-axis layout
    ax_flow.set_aspect('auto')
    ax_flow.axis('off')
    
    # ========================================================================
    # Title
    # ========================================================================
    
    fig.suptitle('Roosevelt Island Tramway\nThe COVID-19 Impact on Ridership  2019-2020',
                fontsize=22, fontweight='bold', color='#2c3e50', y=0.96)
    
    subtitle = 'Watch ridership collapse in March 2020  |  Line thickness = monthly ridership  |  Light tones = tourists'
    ax_flow.text(12.5, 12.2, subtitle, ha='center', fontsize=10,
                color='#7f8c8d', style='italic')
    
  
    
    # ========================================================================
    # COVID-19 TIMELINE (Bottom)
    # ========================================================================
    
    ax_covid.set_facecolor('#f8f8f0')
    
    timeline = get_covid_timeline()
    
    # Draw timeline bars
    for month_idx in range(1, 25):
        if month_idx in timeline:
            label, event, color = timeline[month_idx]
        else:
            color = '#E8E8E8'  # Default gray
            event = ""
        
        # Draw colored bar for this month
        bar = Rectangle((month_idx - 0.4, 0), 0.8, 1,
                       facecolor=color, edgecolor='white', linewidth=1)
        ax_covid.add_patch(bar)
    
    # Add key event labels
    key_events = [15, 16, 17, 24]  # Mar 2020, Apr 2020, May 2020, Dec 2020
    
    for month_idx in key_events:
        if month_idx in timeline:
            label, event, color = timeline[month_idx]
            ax_covid.text(month_idx, 1.3, event, ha='center', va='bottom',
                         fontsize=9, fontweight='bold', rotation=0,
                         color='#2c3e50')
    
    # Timeline labels
    ax_covid.text(6, -0.5, '2019: Normal Operations', ha='center', fontsize=13,
                 fontweight='bold', color='#9BA17B')
    ax_covid.text(18, -0.5, '2020: COVID-19 Impact & Recovery', ha='center',
                 fontsize=13, fontweight='bold', color='#A0522D')
    
    # Styling
    ax_covid.set_xlim(0, 25)
    ax_covid.set_ylim(-1, 2)
    ax_covid.set_aspect('auto')
    ax_covid.axis('off')
    
    ax_covid.set_title('NYC COVID-19 Timeline & Interventions',
                      fontsize=13, fontweight='bold', color='#2c3e50', pad=15)
    
    # ========================================================================
    # Credit
    # ========================================================================
    
    credit = '#30DayMapChallenge 2025 | Flow Lines\nData: MTA NYCT MetroCard History | Inspired by Charles Minard, 1869'
    fig.text(0.5, 0.01, credit, ha='center', fontsize=8,
            color='#7f8c8d', style='italic')
    
    # ========================================================================
    # Save
    # ========================================================================
    
    plt.tight_layout(rect=[0, 0.02, 1, 0.94])
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='#f8f8f0')
    print(f"\n✅ COVID Impact Map saved as {output_file}")
    
    return fig

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("Roosevelt Island Tramway - COVID-19 Impact Visualization")
    print("="*70)
    
    print("\n📊 Loading 2019-2020 data...")
    
    try:
        m_to_i, i_to_m = load_covid_period_data('edited.csv')
    except FileNotFoundError:
        print("ERROR: 'edited.csv' not found. Please ensure the data file is available.")
        exit()
    
    print(f"✅ Data loaded: {len(i_to_m)} months of ridership data")
    print(f"   Period: 2019-2020")
    print(f"   Stations: R468 (Manhattan→Island), R469 (Island→Manhattan)")
    
    print("\n🎨 Creating COVID-19 impact visualization...")
    print("   Watch for the DRAMATIC crash in March 2020!")
    
    fig = create_covid_impact_map(m_to_i, i_to_m)
    
    print("\n" + "="*70)
    print("✅ DONE! Your COVID impact map is ready!")
    print("   The visualization shows:")
    print("   • Thick flows in 2019 (normal operations)")
    print("   • DRAMATIC crash in March 2020 (lockdown)")
    print("   • Thin flows through rest of 2020 (reduced ridership)")
    print("="*70 + "\n")
    
    plt.show()