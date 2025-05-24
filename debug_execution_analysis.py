#!/usr/bin/env python3
"""
Debug the execution timing analysis function to see what it actually returns
"""
import pandas as pd
import numpy as np

def analyze_execution_timing_debug(df):
    """Debug version of the execution timing analysis"""
    if df is None or df.empty:
        return {}
    
    print("🔍 Debug: Starting execution timing analysis")
    
    # Calculate execution times for each event, per device if device info exists
    execution_stats = {}
    
    # Check if the DataFrame has Device_ID column
    has_device_info = 'Device_ID' in df.columns
    print(f"   Has device info: {has_device_info}")
    
    if has_device_info:
        # Process each device separately
        for device in df['Device_ID'].unique():
            print(f"\n📱 Processing device: {device}")
            device_df = df[df['Device_ID'] == device]
            device_stats = {}
            
            for event in device_df['Event'].unique():
                print(f"   ⚡ Processing event: {event}")
                event_data = device_df[device_df['Event'] == event].copy()
                event_data = event_data.sort_values('Time')
                
                print(f"      Event data:")
                print(event_data[['Time', 'Toggled']].to_string())
                
                # Find pairs of toggle on/off to calculate execution time
                executions = []
                start_time = None
                message_id = None
                
                for _, row in event_data.iterrows():
                    if row['Toggled'] and start_time is None:
                        # Event started
                        start_time = row['Time']
                        message_id = row.get('Message_ID', None)
                        print(f"      Start: {start_time}")
                    elif not row['Toggled'] and start_time is not None:
                        # Only pair events with the same Message_ID if available
                        if pd.isna(message_id) and pd.isna(row.get('Message_ID', None)) or message_id == row.get('Message_ID', None):
                            # Event ended
                            execution_time = row['Time'] - start_time
                            print(f"      End: {row['Time']}")
                            print(f"      ⏱️ Execution time: {execution_time} ns = {execution_time/1000} μs")
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
                    print(f"      ✅ Calculated {len(executions)} executions")
                else:
                    print(f"      ❌ No valid executions found")
            
            if device_stats:
                execution_stats[device] = device_stats
    
    return execution_stats

if __name__ == "__main__":
    print("🔍 Debug Execution Timing Analysis")
    print("=" * 50)
    
    # Load data
    df = pd.read_csv('data/sample_data.csv')
    print(f"📊 Loaded {len(df)} rows")
    
    # Run debug analysis
    stats = analyze_execution_timing_debug(df)
    
    print("\n📋 Final Results Summary:")
    for device, device_stats in stats.items():
        print(f"\n🔸 {device}:")
        for event, event_stats in device_stats.items():
            mean_us = event_stats['mean_ns'] / 1000
            print(f"   {event}: {mean_us:.1f} μs (count: {event_stats['count']})")
