import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

def get_usd_to_gbp_rate():
    try:
        # Using ExchangeRate-API (free tier)
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
        data = response.json()
        return data['rates']['GBP']
    except:
        # Return a default rate if API call fails
        return 0.79

st.title("GPU Earning Calculator")

st.divider()
st.write("## Cost of a GPU System")
col1, col2, col3 = st.columns(3)
with col1:
    unit_price = st.number_input("Unit Price in GBP per system", value=25000, step=100)
with col2:
    tax_rate = st.number_input("Tax Rate %", value=24, step=1)
with col3:
    gpu_per_system = st.number_input("GPU cards per system", value=5)
num_systems = st.slider("Number of systems (6 to a rack)", 1, 24, 6)

effective_cost = unit_price - (unit_price * (tax_rate / 100))
st.write(f"Effective Cost in GBP per system: £{effective_cost:,.0f}")
st.write(f"Total cost of systems is: £{effective_cost * num_systems:,.0f} which includes {num_systems * gpu_per_system} GPU cards")

st.divider()

st.write("## Income")

col1, col2 = st.columns(2)
with col1:
    currency = "USD" if st.toggle("USD", value=True) is True else "GBP"
    conversion_rate = get_usd_to_gbp_rate() if currency == "USD" else 1.0
    charge_rate = st.slider(f"Hourly Rate Per GPU in {currency}", 0.00, 1.00, 0.45, step=0.01)
    charge_rate_gbp = charge_rate * conversion_rate if currency == "USD" else charge_rate
    utilization = st.slider("GPU Utilisation %", 0, 100, 80)

with col2:
    #s = f"rate in GBP: {charge_rate_gbp:,.2f}" if currency == "USD" else ""
    st.write(f"rate in GBP: {charge_rate_gbp:,.2f}") 
    charge_rate_dep = st.slider("Expected fall of charge rate per year %", 0.00, 50.00, 10.00, step=0.5)
    platform_fees = st.slider("Platform fees %", 0, 50, 25, step=1)

net_charge_rate = (charge_rate_gbp - (charge_rate_gbp * (platform_fees / 100)))
y5_charge_rate = net_charge_rate * ((1 - (charge_rate_dep/100))**4)

st.write(f"You are charging £{net_charge_rate:,.2f} per GPU hour (after charges) falling to £{y5_charge_rate:,.2f} after 5 years")

st.divider()

st.write("## Costs")
col1, col2 = st.columns(2)
with col1:
    electricity_cost = st.slider("Electricity unit price in GBP", 0.00, 0.50, 0.25, step=0.01)
    power_consumption = st.slider("Power Consumption in kWh per card per month at 100% utilisation", 0, 500, 244, step=1)
with col2:
    internet_cost = st.slider("Monthly internet cost in GBP", 0.00, 1000.00, 292.00, step=1.00)
    misc_cost = st.slider("Monthly other costs in GBP", 0.00, 1000.00, 50.00, step=1.00)

st.divider()

st.write("## Results")

# Calculate base revenue per GPU per month
hours_per_month = 24 * 30  # 24 hours * 30 days
total_gpus = num_systems * gpu_per_system

# Initialize lists for the DataFrame
years = []
revenues = []
electricity_costs = []
other_costs = []
net_profits = []

for year in range(5):
    # Calculate degraded charge rate for this year
    current_charge_rate = net_charge_rate * ((1 - (charge_rate_dep/100))**year)
    
    # Calculate annual revenue
    monthly_revenue = (
        current_charge_rate *  # Rate per hour
        hours_per_month *      # Hours per month
        total_gpus *          # Number of GPUs
        (utilization/100) *   # Utilization rate
        12                    # Months per year
    )
    
    # Calculate annual electricity cost
    monthly_electricity = (
        power_consumption *    # kWh per card per month
        electricity_cost *     # Cost per kWh
        total_gpus *          # Number of GPUs
        (utilization/100) *   # Utilization rate
        12                    # Months per year
    )
    
    # Calculate annual other costs
    annual_other_costs = (internet_cost + misc_cost) * 12
    
    # Calculate net profit
    net_profit = monthly_revenue - monthly_electricity - annual_other_costs
    
    # Append to lists
    years.append(f"Year {year + 1}")
    revenues.append(monthly_revenue)
    electricity_costs.append(monthly_electricity)
    other_costs.append(annual_other_costs)
    net_profits.append(net_profit)

# Create DataFrame
df = pd.DataFrame({
    'Year': years,
    'Revenue': revenues,
    'Electricity Costs': electricity_costs,
    'Other Costs': other_costs,
    'Net Profit': net_profits
})

# Calculate ROI
total_investment = effective_cost * num_systems
# roi_years = total_investment / (df['Net Profit'].mean())

# Display results
st.write("### Annual Profit Breakdown")
st.dataframe(df.style.format({
    'Revenue': '£{:,.0f}',
    'Electricity Costs': '£{:,.0f}',
    'Other Costs': '£{:,.0f}',
    'Net Profit': '£{:,.0f}'
}))

st.write(f"### Return on Investment")

# After the ROI calculations, replace the chart section with:
st.write("### Profit Visualization")

# Calculate cumulative profits
df['Cumulative Profit'] = df['Net Profit'].cumsum()

# Create the bar chart
chart_data = pd.DataFrame({
    'Year': years,
    'Annual Profit': net_profits,
    'Cumulative Profit': df['Cumulative Profit']
})

# Create figure
fig = go.Figure()

# Add bars for annual profit
fig.add_trace(
    go.Bar(
        x=chart_data['Year'],
        y=chart_data['Annual Profit'],
        name="Annual Profit",
        marker_color='lightblue'
    )
)

# Add line for cumulative profit
fig.add_trace(
    go.Scatter(
        x=chart_data['Year'],
        y=chart_data['Cumulative Profit'],
        name="Cumulative Profit",
        line=dict(color='darkblue')
    )
)

# Add line for investment
fig.add_trace(
    go.Scatter(
        x=chart_data['Year'],
        y=[total_investment] * 5,
        name="Initial Investment",
        line=dict(color='red', dash='dash')
    )
)

# Update layout
fig.update_layout(
    title="Profit Analysis Over Time",
    barmode='group',
    hovermode='x unified',
    yaxis=dict(title="Amount (£)"),
)

# Display the chart
st.plotly_chart(fig, use_container_width=True)

st.write(f"Total Investment: £{total_investment:,.0f}")

# Add a note about break-even
if df['Cumulative Profit'].max() > total_investment:
    break_even_year = np.interp(
        total_investment, 
        df['Cumulative Profit'], 
        range(1, 6)
    )
    st.write(f"📊 Break-even occurs after approximately {break_even_year:.1f} years")
else:
    st.write("⚠️ Investment does not break even within the 5-year period")