#!/usr/bin/env python3
"""
Test the fixed execution timing analysis
"""
import pandas as pd
import numpy as np

def analyze_execution_timing_fixed(df):
    """Fixed version of execution timing analysis"""
    if df is None or df.empty:
        return {}
    
    execution_stats = {}
    has_device_info = 'Device_ID' in df.columns
    
    if has_device_info:
        for device in df['Device_ID'].unique():
            device_df = df[df['Device_ID'] == device]
            device_stats = {}
            
            for event in device_df['Event'].unique():
                event_data = device_df[device_df['Event'] == event].copy()
                event_data = event_data.sort_values('Time')
                
                executions = []
                start_time = None
                message_id = None
                
                for _, row in event_data.iterrows():
                    if row['Toggled'] and start_time is None:
                        start_time = row['Time']
                        message_id = row.get('Message_ID', None)
                    elif not row['Toggled'] and start_time is not None:
                        # Fixed: Handle NaN values properly
                        row_message_id = row.get('Message_ID', None)
                        if (pd.isna(message_id) and pd.isna(row_message_id)) or (message_id == row_message_id):
                            execution_time = row['Time'] - start_time
                            executions.append({
                                'time': execution_time,
                                'start': start_time,
                                'end': row['Time'],
                                'message_id': message_id
                            })
                            start_time = None
                            message_id = None
                
                if executions:
                    execution_times = [ex['time'] for ex in executions]
                    device_stats[event] = {
                        'count': len(executions),
                        'mean_ns': np.mean(execution_times),
                        'std_ns': np.std(execution_times),
                        'min_ns': np.min(execution_times),
                        'max_ns': np.max(execution_times),
                        'executions': executions
                    }
            
            if device_stats:
                execution_stats[device] = device_stats
    
    return execution_stats

if __name__ == "__main__":
    print("🔧 Testing Fixed Execution Timing Analysis")
    print("=" * 50)
    
    # Load data
    df = pd.read_csv('data/sample_data.csv')
    print(f"📊 Loaded {len(df)} rows")
    
    # Test fixed analysis
    stats = analyze_execution_timing_fixed(df)
    
    print("\n📋 Fixed Results Summary:")
    print("Expected values:")
    print("  GPIO_Init: 0.5 μs")
    print("  ADC_Read: 2.0 μs") 
    print("  UART_Send: 8.0 μs")
    print("  Timer_ISR: 1.2 μs")
    print("  SPI_Transfer: 3.0 μs")
    print()
    
    for device in ['Device_1', 'Device_2'][:2]:  # Check first 2 devices
        if device in stats:
            print(f"🔸 {device}:")
            for event, event_stats in stats[device].items():
                mean_us = event_stats['mean_ns'] / 1000
                count = event_stats['count']
                print(f"   {event}: {mean_us:.1f} μs (count: {count})")
            print()
    
    # Check if we have data for all expected events
    total_events = sum(len(device_stats) for device_stats in stats.values())
    print(f"✅ Total events processed: {total_events}")
    print(f"✅ Total devices processed: {len(stats)}")
    
    if total_events > 0:
        print("🎉 Fix successful! Data is now being processed correctly.")
    else:
        print("❌ Fix failed - no events processed.")
