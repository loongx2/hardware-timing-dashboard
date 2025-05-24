#!/usr/bin/env python3
"""
Test visualization to check axis orientation
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Create test data with known values
test_data = {
    'Event': ['GPIO_Init', 'ADC_Read', 'UART_Send'] * 5,
    'Execution_Time_us': [0.5, 2.0, 8.0] * 5,  # Known values from our calculation
    'Device': ['Device_1'] * 3 + ['Device_2'] * 3 + ['Device_3'] * 3 + ['Device_4'] * 3 + ['Device_5'] * 3
}

df_test = pd.DataFrame(test_data)

print("📊 Creating test visualization with known values:")
print("   GPIO_Init: 0.5 μs (should be lowest)")
print("   ADC_Read: 2.0 μs (should be middle)")  
print("   UART_Send: 8.0 μs (should be highest)")
print()

# Create the same type of box plot as the dashboard
fig = px.box(
    df_test,
    x='Event',
    y='Execution_Time_us',
    color='Device',
    title='Test: Expected Axis Orientation',
    labels={'Execution_Time_us': 'Execution Time (μs)'}
)

fig.update_layout(
    height=400,
    template='plotly_white',
    xaxis_tickangle=-45
)

# Save as HTML for inspection
fig.write_html('test_axis_orientation.html')
print("✅ Test visualization saved as 'test_axis_orientation.html'")
print("📋 Expected in chart:")
print("   - X-axis: Event names")
print("   - Y-axis: Execution Time (μs)")
print("   - UART_Send boxes should be at the TOP (highest Y values)")
print("   - GPIO_Init boxes should be at the BOTTOM (lowest Y values)")
