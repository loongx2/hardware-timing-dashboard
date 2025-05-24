#!/usr/bin/env python3
"""
Data verification script to check if timing calculations and axis orientations are correct
"""
import pandas as pd
import numpy as np

def load_and_verify_data():
    """Load and verify the sample data"""
    print("🔍 Loading and verifying data...")
    
    # Load the data
    df = pd.read_csv('data/sample_data.csv')
    print(f"📊 Loaded {len(df)} rows of data")
    print(f"📋 Columns: {list(df.columns)}")
    print()
    
    # Show first few rows
    print("📋 First 10 rows:")
    print(df.head(10))
    print()
    
    # Verify data structure
    print("🔍 Data verification:")
    print(f"   Events: {df['Event'].unique()}")
    print(f"   Devices: {df['Device_ID'].unique()}")
    print(f"   Time range: {df['Time'].min()} - {df['Time'].max()}")
    print(f"   Toggled values: {df['Toggled'].unique()}")
    print()
    
    return df

def manually_calculate_execution_times(df):
    """Manually calculate execution times to verify the algorithm"""
    print("⚡ Manual execution time calculation:")
    
    # Check GPIO_Init for Device_1 as example
    device_1_gpio = df[(df['Device_ID'] == 'Device_1') & (df['Event'] == 'GPIO_Init')].copy()
    device_1_gpio = device_1_gpio.sort_values('Time')
    
    print("📋 GPIO_Init events for Device_1:")
    print(device_1_gpio)
    print()
    
    # Calculate execution time
    start_time = None
    for _, row in device_1_gpio.iterrows():
        if row['Toggled'] and start_time is None:
            start_time = row['Time']
            print(f"   Start: {start_time}")
        elif not row['Toggled'] and start_time is not None:
            end_time = row['Time']
            execution_time = end_time - start_time
            print(f"   End: {end_time}")
            print(f"   ⏱️ Execution time: {execution_time} ns = {execution_time/1000} μs")
            start_time = None
    print()

def check_data_consistency(df):
    """Check for data consistency issues"""
    print("🔍 Data consistency checks:")
    
    # Check for unpaired events
    for device in df['Device_ID'].unique():
        for event in df['Event'].unique():
            event_data = df[(df['Device_ID'] == device) & (df['Event'] == event)].copy()
            if len(event_data) == 0:
                continue
                
            event_data = event_data.sort_values('Time')
            
            true_count = len(event_data[event_data['Toggled'] == True])
            false_count = len(event_data[event_data['Toggled'] == False])
            
            if true_count != false_count:
                print(f"   ⚠️ Unpaired events for {device} {event}: {true_count} starts, {false_count} ends")
            
    print("   ✅ Data consistency check complete")
    print()

def verify_axis_orientation():
    """Verify that axis orientation makes sense"""
    print("📊 Axis orientation verification:")
    print("   Expected:")
    print("   - X-axis: Event names (GPIO_Init, ADC_Read, etc.)")
    print("   - Y-axis: Execution time in microseconds (μs)")
    print("   - Higher Y values = longer execution times")
    print("   - Box plots should show distribution of execution times")
    print()
    
    # Calculate some example values
    df = pd.read_csv('data/sample_data.csv')
    
    # GPIO_Init Device_1: start=1000, end=1500, execution=500ns = 0.5μs
    # ADC_Read Device_1: start=4000, end=6000, execution=2000ns = 2.0μs
    # UART_Send Device_1: start=15000, end=23000, execution=8000ns = 8.0μs
    
    print("   Example calculated values:")
    print("   - GPIO_Init (Device_1): 1500-1000 = 500ns = 0.5μs")
    print("   - ADC_Read (Device_1): 6000-4000 = 2000ns = 2.0μs") 
    print("   - UART_Send (Device_1): 23000-15000 = 8000ns = 8.0μs")
    print()
    print("   ✅ This means UART_Send should appear highest on Y-axis")
    print("   ✅ GPIO_Init should appear lowest on Y-axis")
    print("   ✅ If this is reversed in the chart, there's an axis issue")
    print()

if __name__ == "__main__":
    print("🔍 Data Verification Script")
    print("=" * 50)
    
    df = load_and_verify_data()
    manually_calculate_execution_times(df)
    check_data_consistency(df)
    verify_axis_orientation()
    
    print("✅ Verification complete!")
    print("👀 Check the dashboard at http://localhost:8050 to compare with these values")
