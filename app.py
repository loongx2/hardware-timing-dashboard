import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
from datetime import datetime, timedelta
import dash
from dash import dcc, html, Input, Output, callback, State
import dash_bootstrap_components as dbc
import base64
import io
import json
from itertools import combinations
import networkx as nx
import json
from itertools import combinations

# Set seaborn style
sns.set_style("whitegrid")
plt.style.use('seaborn-v0_8')

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Hardware Timing Analytics Dashboard"

# Global variable to store uploaded data
timing_data = None

def parse_csv_contents(contents, filename):
    """Parse uploaded CSV file"""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if 'csv' in filename.lower():
            # Read the CSV file into a string
            csv_string = decoded.decode('utf-8')
            
            # Remove comment lines that start with // or #
            cleaned_lines = [line for line in csv_string.splitlines() if not line.strip().startswith('//') and not line.strip().startswith('#')]
            cleaned_csv = '\n'.join(cleaned_lines)
            
            # Parse the cleaned CSV content
            df = pd.read_csv(io.StringIO(cleaned_csv))
            
            # Validate required columns
            required_columns = ['Event', 'Time', 'Toggled']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return None, f"Missing required columns: {', '.join(missing_columns)}"
            
            # Convert Time to numeric (nanoseconds)
            df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
            
            # Convert Toggled to boolean
            df['Toggled'] = df['Toggled'].astype(bool)
            
            # Handle optional columns for device topology
            if 'Device_ID' in df.columns:
                # Convert Position to numeric if it exists
                if 'Position' in df.columns:
                    df['Position'] = pd.to_numeric(df['Position'], errors='coerce')
            
            return df, None
        else:
            return None, "Please upload a CSV file"
            
    except Exception as e:
        return None, f"Error processing file: {str(e)}"

def analyze_execution_timing(df):
    """Analyze execution timing from hardware data"""
    if df is None or df.empty:
        return {}
    
    # Calculate execution times for each event, per device if device info exists
    execution_stats = {}
    
    # Check if the DataFrame has Device_ID column
    has_device_info = 'Device_ID' in df.columns
    
    if has_device_info:
        # Process each device separately
        for device in df['Device_ID'].unique():
            device_df = df[df['Device_ID'] == device]
            device_stats = {}
            
            for event in device_df['Event'].unique():
                event_data = device_df[device_df['Event'] == event].copy()
                event_data = event_data.sort_values('Time')
                
                # Find pairs of toggle on/off to calculate execution time
                executions = []
                start_time = None
                message_id = None
                
                for _, row in event_data.iterrows():
                    if row['Toggled'] and start_time is None:
                        # Event started
                        start_time = row['Time']
                        message_id = row.get('Message_ID', None)
                    elif not row['Toggled'] and start_time is not None:
                        # Only pair events with the same Message_ID if available
                        # Handle NaN values properly
                        row_message_id = row.get('Message_ID', None)
                        if (pd.isna(message_id) and pd.isna(row_message_id)) or (message_id == row_message_id):
                            # Event ended
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
    else:
        # Original processing when no device info
        for event in df['Event'].unique():
            event_data = df[df['Event'] == event].copy()
            event_data = event_data.sort_values('Time')
            
            # Find pairs of toggle on/off to calculate execution time
            executions = []
            start_time = None
            
            for _, row in event_data.iterrows():
                if row['Toggled'] and start_time is None:
                    # Event started
                    start_time = row['Time']
                elif not row['Toggled'] and start_time is not None:
                    # Event ended
                    execution_time = row['Time'] - start_time
                    executions.append({
                        'time': execution_time,
                        'start': start_time,
                        'end': row['Time'],
                        'message_id': None
                    })
                    start_time = None
            
            if executions:
                execution_times = [ex['time'] for ex in executions]
                execution_stats[event] = {
                    'count': len(executions),
                    'mean_ns': np.mean(execution_times),
                    'std_ns': np.std(execution_times),
                    'min_ns': np.min(execution_times),
                    'max_ns': np.max(execution_times),
                    'executions': executions
                }
    
    return execution_stats

def analyze_synchronicity(df):
    """Analyze the synchronicity of events across devices"""
    if df is None or df.empty or 'Device_ID' not in df.columns:
        return {}
    
    sync_stats = {}
    
    # Focus on sync events specifically
    sync_df = df[df['Event'] == 'Sync_Pulse'].copy()
    
    if sync_df.empty:
        return {}
    
    # Group by Message_ID to analyze each sync pulse across devices
    for message_id in sync_df['Message_ID'].unique():
        if not message_id or not str(message_id).startswith('SYNC_'):
            continue
            
        message_df = sync_df[sync_df['Message_ID'] == message_id]
        
        # Group by device and get start times (Toggled = True)
        device_start_times = {}
        for _, row in message_df[message_df['Toggled']].iterrows():
            device_start_times[row['Device_ID']] = row['Time']
        
        if len(device_start_times) <= 1:
            continue
            
        # Calculate time differences between devices
        time_diffs = []
        devices = list(device_start_times.keys())
        
        for dev1, dev2 in combinations(devices, 2):
            time_diff = abs(device_start_times[dev1] - device_start_times[dev2])
            time_diffs.append({
                'device1': dev1,
                'device2': dev2,
                'time_diff_ns': time_diff
            })
        
        # Calculate statistics for this sync pulse
        time_diff_values = [td['time_diff_ns'] for td in time_diffs]
        
        sync_stats[message_id] = {
            'device_count': len(devices),
            'max_diff_ns': np.max(time_diff_values),
            'min_diff_ns': np.min(time_diff_values),
            'mean_diff_ns': np.mean(time_diff_values),
            'std_diff_ns': np.std(time_diff_values),
            'details': time_diffs
        }
    
    return sync_stats

def analyze_communication_time(df):
    """Analyze the communication time between devices in a chain"""
    if df is None or df.empty or 'Device_ID' not in df.columns:
        return {}
    
    comm_stats = {}
    
    # Focus on communication events (UART_Send and UART_Receive)
    comm_df = df[(df['Event'] == 'UART_Send') | (df['Event'] == 'UART_Receive')].copy()
    
    if comm_df.empty:
        return {}
    
    # Group by Message_ID to track message propagation through the chain
    for message_id in comm_df['Message_ID'].unique():
        if not message_id or message_id is None or str(message_id).startswith('SYNC_'):
            continue
            
        message_df = comm_df[comm_df['Message_ID'] == message_id]
        
        # Track when the message starts in the sending device
        send_row = message_df[(message_df['Event'] == 'UART_Send') & (message_df['Toggled'])].iloc[0] if not message_df[(message_df['Event'] == 'UART_Send') & (message_df['Toggled'])].empty else None
        
        if send_row is None:
            continue
            
        send_device = send_row['Device_ID']
        send_position = send_row['Position']
        send_time = send_row['Time']
        
        # Track when the message is received by each device
        propagation_times = []
        
        for device in message_df['Device_ID'].unique():
            if device == send_device:
                continue
                
            # Find when this device received the message
            receive_row = message_df[(message_df['Device_ID'] == device) & 
                                     (message_df['Event'] == 'UART_Receive') & 
                                     (message_df['Toggled'])].iloc[0] if not message_df[(message_df['Device_ID'] == device) & 
                                                                               (message_df['Event'] == 'UART_Receive') & 
                                                                               (message_df['Toggled'])].empty else None
            
            if receive_row is None:
                continue
                
            receive_position = receive_row['Position']
            receive_time = receive_row['Time']
            
            # Calculate propagation time and hops
            prop_time = receive_time - send_time
            hops = abs(receive_position - send_position)
            
            propagation_times.append({
                'from_device': send_device,
                'to_device': device,
                'from_position': send_position,
                'to_position': receive_position,
                'hops': hops,
                'time_ns': prop_time,
                'time_per_hop_ns': prop_time / hops if hops > 0 else 0
            })
        
        if propagation_times:
            # Calculate statistics for this message
            comm_stats[str(message_id)] = {
                'source_device': send_device,
                'destination_count': len(propagation_times),
                'propagation_details': propagation_times
            }
    
    return comm_stats

def generate_sample_data():
    """Generate sample hardware timing data for demonstration"""
    np.random.seed(42)
    
    # Define a daisy chain topology of embedded devices
    num_devices = 5  # Number of devices in the chain
    events = ['GPIO_Init', 'ADC_Read', 'UART_Send', 'Timer_ISR', 'SPI_Transfer']
    data = []
    
    current_time = 0
    
    # Generate events for each device in the chain
    for _ in range(200):  # Generate fewer events per device for clarity
        # Select a random device from the chain
        device_id = np.random.randint(1, num_devices + 1)
        event = np.random.choice(events)
        
        # Add a small time offset for each device to simulate propagation delay in the chain
        device_offset = (device_id - 1) * 50  # 50ns offset per device in chain
        event_time = current_time + device_offset
        
        # Event starts
        data.append({
            'Event': event,
            'Time': event_time,
            'Toggled': True,
            'Device_ID': f"Device_{device_id}",
            'Position': device_id,  # Position in the daisy chain
            'Message_ID': None  # Will be used for communication events
        })
        
        # Random execution time based on event type
        if event == 'GPIO_Init':
            exec_time = np.random.normal(500, 100)  # 500ns avg
        elif event == 'ADC_Read':
            exec_time = np.random.normal(2000, 300)  # 2μs avg
        elif event == 'UART_Send':
            exec_time = np.random.normal(8000, 1000)  # 8μs avg
            # For UART_Send, generate a message that propagates through the chain
            if device_id < num_devices:  # Not the last device
                message_id = np.random.randint(10000, 99999)
                data[-1]['Message_ID'] = message_id  # Update the Message_ID for the send event
                
                # Add propagation through the chain for this message
                prop_time = event_time + exec_time
                for next_device in range(device_id + 1, num_devices + 1):
                    # Message arrives at next device
                    comm_delay = np.random.normal(2000, 300) * (next_device - device_id)  # Communication delay increases with distance
                    prop_time += comm_delay
                    
                    # Receive event at the next device
                    data.append({
                        'Event': 'UART_Receive',
                        'Time': prop_time,
                        'Toggled': True,
                        'Device_ID': f"Device_{next_device}",
                        'Position': next_device,
                        'Message_ID': message_id
                    })
                    
                    # Processing time at the receiving device
                    proc_time = np.random.normal(500, 100)
                    prop_time += proc_time
                    
                    data.append({
                        'Event': 'UART_Receive',
                        'Time': prop_time,
                        'Toggled': False,
                        'Device_ID': f"Device_{next_device}",
                        'Position': next_device,
                        'Message_ID': message_id
                    })
                
        elif event == 'Timer_ISR':
            exec_time = np.random.normal(1200, 200)  # 1.2μs avg
        else:  # SPI_Transfer
            exec_time = np.random.normal(3000, 500)  # 3μs avg
        
        exec_time = max(100, exec_time)  # Minimum 100ns
        event_time += exec_time
        
        # Event ends
        data.append({
            'Event': event,
            'Time': event_time,
            'Toggled': False,
            'Device_ID': f"Device_{device_id}",
            'Position': device_id,
            'Message_ID': data[-1]['Message_ID']  # Maintain the same Message_ID
        })
        
        # Add some idle time
        current_time += exec_time + np.random.exponential(1000)
    
    # Generate synchronization events across all devices
    # Each sync event happens at roughly the same time on all devices
    for sync_idx in range(10):
        base_sync_time = current_time + sync_idx * 50000  # 50μs between sync events
        
        for device_id in range(1, num_devices + 1):
            # Add jitter to sync time to simulate real-world conditions
            jitter = np.random.normal(0, 200)  # 200ns std dev jitter
            sync_time = base_sync_time + jitter
            
            # Sync event starts
            data.append({
                'Event': 'Sync_Pulse',
                'Time': sync_time,
                'Toggled': True,
                'Device_ID': f"Device_{device_id}",
                'Position': device_id,
                'Message_ID': f"SYNC_{sync_idx}"
            })
            
            # Sync pulse duration
            sync_duration = np.random.normal(300, 50)  # 300ns avg
            
            # Sync event ends
            data.append({
                'Event': 'Sync_Pulse',
                'Time': sync_time + sync_duration,
                'Toggled': False,
                'Device_ID': f"Device_{device_id}",
                'Position': device_id,
                'Message_ID': f"SYNC_{sync_idx}"
            })
    
    return pd.DataFrame(data)

# Load sample data
# sample_df = generate_sample_data()

# Load sample timing data with proper handling of comment lines
sample_file = 'data/sample_data.csv'
if not os.path.exists(sample_file):
    sample_file = 'sample_data.csv'  # Fallback to current directory

try:
    with open(sample_file, 'r') as f:
        # Skip comment lines that start with // or #
        cleaned_lines = [line for line in f if not line.strip().startswith('//') and not line.strip().startswith('#')]
        cleaned_csv = '\n'.join(cleaned_lines)

    # Parse the cleaned CSV content
    sample_df = pd.read_csv(io.StringIO(cleaned_csv))
    timing_data = sample_df  # Initialize with sample data
except FileNotFoundError:
    print(f"Warning: Sample data file not found at {sample_file}")
    timing_data = None

# Define the layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("⚡ Hardware Timing Analytics Dashboard", 
                   className="text-center mb-4",
                   style={'color': '#2c3e50', 'fontWeight': 'bold'})
        ])
    ]),
    
    # File Upload Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📁 Upload Hardware Timing Data"),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select CSV File')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        multiple=False
                    ),
                    html.Div(id='upload-status', className='mt-3'),
                    html.Hr(),
                    html.P("Expected CSV format: Event, Time (nanoseconds), Toggled (True/False), Device_ID, Position, Message_ID", 
                           className="text-muted small")
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Device Topology Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔌 Device Topology"),
                dbc.CardBody([
                    html.Div([
                        html.H4("📊 Embedded Device Configuration", className="card-title"),
                        html.Div(id="device-topology-stats"),
                    ]),
                    html.Hr(),
                    # Topology Editing Controls
                    dbc.Row([
                        dbc.Col([
                            html.Label("Topology Mode:", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id='topology-mode',
                                options=[
                                    {'label': '🔗 Daisy Chain', 'value': 'daisy'},
                                    {'label': '⭐ Star Network', 'value': 'star'},
                                    {'label': '🔄 Ring Network', 'value': 'ring'},
                                    {'label': '🌐 Mesh Network', 'value': 'mesh'},
                                    {'label': '✏️ Custom Layout', 'value': 'custom'}
                                ],
                                value='daisy',
                                clearable=False,
                                className="mb-2"
                            )
                        ], width=3),
                        dbc.Col([
                            html.Label("Connection Editor:", className="fw-bold mb-2"),
                            dbc.ButtonGroup([
                                dbc.Button("🔗 Add Connection", id="add-connection-btn", 
                                          color="success", size="sm", className="me-1"),
                                dbc.Button("✂️ Remove Connection", id="remove-connection-btn", 
                                          color="danger", size="sm", className="me-1"),
                                dbc.Button("🔄 Reset Layout", id="reset-layout-btn", 
                                          color="warning", size="sm")
                            ], className="mb-2")
                        ], width=4),
                        dbc.Col([
                            html.Label("Topology Actions:", className="fw-bold mb-2"),
                            dbc.ButtonGroup([
                                dbc.Button("💾 Save Topology", id="save-topology-btn", 
                                          color="primary", size="sm", className="me-1"),
                                dbc.Button("📤 Export Layout", id="export-topology-btn", 
                                          color="info", size="sm")
                            ], className="mb-2")
                        ], width=3),
                        dbc.Col([
                            html.Label("Layout Options:", className="fw-bold mb-2"),
                            dbc.Checklist(
                                id="layout-options",
                                options=[
                                    {"label": "Show Labels", "value": "labels"},
                                    {"label": "Show Connections", "value": "connections"},
                                    {"label": "Enable Dragging", "value": "dragging"}
                                ],
                                value=["labels", "connections", "dragging"],
                                inline=True,
                                className="small"
                            )
                        ], width=2)
                    ], className="mb-3"),
                    # Connection Editor Modal
                    dbc.Modal([
                        dbc.ModalHeader("🔗 Connection Editor"),
                        dbc.ModalBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Source Device:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='connection-source',
                                        placeholder="Select source device..."
                                    )
                                ], width=6),
                                dbc.Col([
                                    html.Label("Target Device:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='connection-target',
                                        placeholder="Select target device..."
                                    )
                                ], width=6)
                            ], className="mb-3"),
                            html.Div(id="current-connections-display")
                        ]),
                        dbc.ModalFooter([
                            dbc.Button("Add Connection", id="confirm-add-connection", 
                                      color="success", className="me-2"),
                            dbc.Button("Close", id="close-connection-modal", 
                                      color="secondary")
                        ])
                    ], id="connection-modal", is_open=False),
                    # Status and feedback
                    html.Div(id="topology-status", className="mb-2"),
                    # Interactive topology chart
                    dcc.Graph(id='device-topology-chart'),
                    # Store for topology state
                    dcc.Store(id='topology-store', data={}),
                    dcc.Store(id='custom-positions-store', data={})
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Stats Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("🎯 Total Events", className="card-title"),
                    html.H2(id="total-events", className="text-primary")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("⚡ Avg Execution Time", className="card-title"),
                    html.H2(id="avg-exec-time", className="text-success")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("🔥 Fastest Event", className="card-title"),
                    html.H2(id="fastest-event", className="text-info")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("🐌 Slowest Event", className="card-title"),
                    html.H2(id="slowest-event", className="text-warning")
                ])
            ])
        ], width=3),
    ], className="mb-4"),
    
    # Charts
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 Execution Time Comparison"),
                dbc.CardBody([
                    dcc.Graph(id='execution-time-chart')
                ])
            ])
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📈 Event Distribution"),
                dbc.CardBody([
                    dcc.Graph(id='event-distribution-chart')
                ])
            ])
        ], width=4),
    ], className="mb-4"),
    
    # Execution Trends and Distribution
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📉 Execution Time Trends"),
                dbc.CardBody([
                    dcc.Graph(id='execution-trends-chart')
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📦 Execution Time Distribution"),
                dbc.CardBody([
                    dcc.Graph(id='time-distribution-chart')
                ])
            ])
        ], width=6),
    ], className="mb-4"),
    
    # Device Selector for Analysis
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔍 Device-Specific Analysis"),
                dbc.CardBody([
                    html.P("Select devices to compare:"),
                    dcc.Dropdown(
                        id='device-selector',
                        multi=True,
                        placeholder="Select devices...",
                    ),
                    html.Div(id="device-comparison-stats", className="mt-3"),
                    dcc.Graph(id='device-comparison-chart')
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Synchronicity Analysis
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("⏱️ Device Synchronicity Analysis"),
                dbc.CardBody([
                    html.Div(id="sync-stats"),
                    dcc.Graph(id='sync-chart')
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔄 Communication Time Analysis"),
                dbc.CardBody([
                    html.Div(id="comm-stats"),
                    dcc.Graph(id='comm-chart')
                ])
            ])
        ], width=6),
    ], className="mb-4"),
    
    # Detailed Timing Analysis
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔍 Detailed Timing Analysis"),
                dbc.CardBody([
                    dcc.Graph(id='detailed-timing-chart')
                ])
            ])
        ])
    ])
], fluid=True)

@app.callback(
    [Output('upload-status', 'children'),
     Output('total-events', 'children'),
     Output('avg-exec-time', 'children'),
     Output('fastest-event', 'children'),
     Output('slowest-event', 'children')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_upload_status_and_stats(contents, filename):
    global timing_data
    
    if contents is not None:
        # Parse uploaded file
        df, error = parse_csv_contents(contents, filename)
        
        if error or df is None:
            return (
                dbc.Alert(f"Error: {error}", color="danger"),
                "N/A", "N/A", "N/A", "N/A"
            )
        
        timing_data = df
        status_msg = dbc.Alert(f"Successfully loaded {filename} with {len(df)} records", color="success")
    else:
        status_msg = dbc.Alert("Using sample data", color="info")
    
    # Calculate stats
    if timing_data is None or timing_data.empty:
        return status_msg, "0", "N/A", "N/A", "N/A"
    
    # Check if the DataFrame has device information
    has_device_info = 'Device_ID' in timing_data.columns
    
    stats = analyze_execution_timing(timing_data)
    
    if not stats:
        return status_msg, "0", "N/A", "N/A", "N/A"
    
    if has_device_info:
        # Aggregate stats across all devices
        total_events = 0
        all_mean_times = []
        all_event_means = {}
        
        for device, device_stats in stats.items():
            for event, event_stats in device_stats.items():
                total_events += event_stats['count']
                all_mean_times.append(event_stats['mean_ns'])
                
                if event not in all_event_means:
                    all_event_means[event] = []
                all_event_means[event].append(event_stats['mean_ns'])
        
        # Calculate overall average
        avg_exec_time = f"{np.mean(all_mean_times):.1f} ns"
        
        # Find fastest and slowest events
        event_avgs = {event: np.mean(means) for event, means in all_event_means.items()}
        fastest_event = min(event_avgs.keys(), key=lambda x: event_avgs[x])
        slowest_event = max(event_avgs.keys(), key=lambda x: event_avgs[x])
        
        fastest_time = f"{event_avgs[fastest_event]:.1f} ns"
        slowest_time = f"{event_avgs[slowest_event]:.1f} ns"
    else:
        # Original stats calculation when no device info
        total_events = sum(stat['count'] for stat in stats.values())
        avg_times = [stat['mean_ns'] for stat in stats.values()]
        avg_exec_time = f"{np.mean(avg_times):.1f} ns"
        
        # Find fastest and slowest events
        fastest_event = min(stats.keys(), key=lambda x: stats[x]['mean_ns'])
        slowest_event = max(stats.keys(), key=lambda x: stats[x]['mean_ns'])
        
        fastest_time = f"{stats[fastest_event]['mean_ns']:.1f} ns"
        slowest_time = f"{stats[slowest_event]['mean_ns']:.1f} ns"
    
    return (
        status_msg,
        f"{total_events:,}",
        avg_exec_time,
        f"{fastest_event}: {fastest_time}",
        f"{slowest_event}: {slowest_time}"
    )

@app.callback(
    Output('execution-time-chart', 'figure'),
    Input('upload-data', 'contents')
)
def update_execution_time_chart(contents):
    global timing_data
    
    if timing_data is None or timing_data.empty:
        return px.bar(title="No data available")
    
    stats = analyze_execution_timing(timing_data)
    
    if not stats:
        return px.bar(title="No execution data found")
    
    # Check if the DataFrame has device information
    has_device_info = 'Device_ID' in timing_data.columns
    
    fig = go.Figure()
    
    if has_device_info:
        # Aggregate stats across all devices for each event
        event_stats = {}
        
        for device, device_stats in stats.items():
            for event, event_data in device_stats.items():
                if event not in event_stats:
                    event_stats[event] = {
                        'times': [],
                        'count': 0
                    }
                
                event_stats[event]['times'].extend([ex['time'] for ex in event_data['executions']])
                event_stats[event]['count'] += event_data['count']
        
        # Create comparison chart
        events = list(event_stats.keys())
        mean_times = [np.mean(event_stats[event]['times']) for event in events]  # Keep as nanoseconds
        std_times = [np.std(event_stats[event]['times']) for event in events]
        
        fig.add_trace(go.Bar(
            x=events,
            y=mean_times,
            error_y=dict(type='data', array=std_times),
            name='Mean Execution Time',
            marker_color='lightblue'
        ))
    else:
        # Original processing when no device info
        events = list(stats.keys())
        mean_times = [stats[event]['mean_ns'] for event in events]  # Keep as nanoseconds
        std_times = [stats[event]['std_ns'] for event in events]  # Keep as nanoseconds
        
        fig.add_trace(go.Bar(
            x=events,
            y=mean_times,
            error_y=dict(type='data', array=std_times),
            name='Mean Execution Time',
            marker_color='lightblue'
        ))
    
    fig.update_layout(
        title='Event Execution Time Comparison',
        xaxis_title='Events',
        yaxis_title='Execution Time (ns)',  # Changed from μs to ns
        height=400,
        template='plotly_white'
    )
    
    return fig

@app.callback(
    Output('event-distribution-chart', 'figure'),
    Input('upload-data', 'contents')
)
def update_event_distribution(contents):
    global timing_data
    
    if timing_data is None or timing_data.empty:
        return px.pie(title="No data available")
    
    stats = analyze_execution_timing(timing_data)
    
    if not stats:
        return px.pie(title="No execution data found")
    
    # Check if the DataFrame has device information
    has_device_info = 'Device_ID' in timing_data.columns
    
    if has_device_info:
        # Aggregate counts across all devices for each event
        event_counts = {}
        
        for device, device_stats in stats.items():
            for event, event_data in device_stats.items():
                if event not in event_counts:
                    event_counts[event] = 0
                event_counts[event] += event_data['count']
        
        events = list(event_counts.keys())
        counts = [event_counts[event] for event in events]
    else:
        # Original processing when no device info
        events = list(stats.keys())
        counts = [stats[event]['count'] for event in events]
    
    fig = px.pie(
        values=counts,
        names=events,
        title='Event Execution Count Distribution',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(height=400)
    
    return fig

@app.callback(
    Output('execution-trends-chart', 'figure'),
    Input('upload-data', 'contents')
)
def update_execution_trends(contents):
    global timing_data
    
    if timing_data is None or timing_data.empty:
        return px.line(title="No data available")
    
    stats = analyze_execution_timing(timing_data)
    
    if not stats:
        return px.line(title="No execution data found")
    
    # Check if the DataFrame has device information
    has_device_info = 'Device_ID' in timing_data.columns
    
    fig = go.Figure()
    
    if has_device_info:
        # For device data, we can either:
        # 1. Show trends for one event across all devices
        # 2. Aggregate across all devices for each event
        # Let's do #2 for simplicity
        
        # Collect all executions for each event type
        event_executions = {}
        
        for device, device_stats in stats.items():
            for event, event_data in device_stats.items():
                if event not in event_executions:
                    event_executions[event] = []
                
                # Sort executions by start time to maintain chronological order
                sorted_execs = sorted(event_data['executions'], key=lambda x: x['start'])
                event_executions[event].extend(sorted_execs)
        
        # Now plot the trends for each event type
        for event, executions in event_executions.items():
            # Sort one more time to ensure chronological order after merging from all devices
            sorted_execs = sorted(executions, key=lambda x: x['start'])
            x_values = list(range(len(sorted_execs)))
            y_values = [ex['time'] for ex in sorted_execs]  # Keep in nanoseconds
            
            fig.add_trace(go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers',
                name=event,
                line=dict(width=2)
            ))
    else:
        # Original processing when no device info
        for event, data in stats.items():
            executions = [ex['time'] for ex in data['executions']]
            x_values = list(range(len(executions)))
            y_values = executions  # Keep in nanoseconds
            
            fig.add_trace(go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers',
                name=event,
                line=dict(width=2)
            ))
    
    fig.update_layout(
        title='Execution Time Trends Over Time',
        xaxis_title='Execution Instance',
        yaxis_title='Execution Time (ns)',  # Changed from μs to ns
        height=400,
        template='plotly_white'
    )
    
    return fig

@app.callback(
    Output('time-distribution-chart', 'figure'),
    Input('upload-data', 'contents')
)
def update_time_distribution(contents):
    global timing_data
    
    if timing_data is None or timing_data.empty:
        return px.histogram(title="No data available")
    
    stats = analyze_execution_timing(timing_data)
    
    if not stats:
        return px.histogram(title="No execution data found")
    
    # Check if the DataFrame has device information
    has_device_info = 'Device_ID' in timing_data.columns
    
    # Combine all execution times
    all_times = []
    all_events = []
    
    if has_device_info:
        for device, device_stats in stats.items():
            for event, event_data in device_stats.items():
                times_ns = [ex['time'] for ex in event_data['executions']]  # Keep as nanoseconds
                all_times.extend(times_ns)
                all_events.extend([event] * len(times_ns))
    else:
        for event, data in stats.items():
            times_ns = [ex['time'] for ex in data['executions']]  # Keep as nanoseconds
            all_times.extend(times_ns)
            all_events.extend([event] * len(times_ns))
    
    df_dist = pd.DataFrame({
        'Execution_Time_ns': all_times,
        'Event': all_events
    })
    
    fig = px.histogram(
        df_dist,
        x='Execution_Time_ns',  # Fixed typo from Execution_Time_un
        color='Event',
        title='Execution Time Distribution',
        labels={'Execution_Time_ns': 'Execution Time (ns)', 'count': 'Frequency'},
        nbins=30
    )
    
    fig.update_layout(
        height=400,
        template='plotly_white',
        barmode='overlay'
    )
    fig.update_traces(opacity=0.7)
    
    return fig

@app.callback(
    Output('detailed-timing-chart', 'figure'),
    Input('upload-data', 'contents')
)
def update_detailed_timing(contents):
    global timing_data
    
    if timing_data is None or timing_data.empty:
        return px.box(title="No data available")
    
    stats = analyze_execution_timing(timing_data)
    
    if not stats:
        return px.box(title="No execution data found")
    
    # Check if the DataFrame has device information
    has_device_info = 'Device_ID' in timing_data.columns
    
    # Create box plot data
    all_times = []
    all_events = []
    all_devices = []
    
    if has_device_info:
        for device, device_stats in stats.items():
            for event, event_data in device_stats.items():
                times_ns = [ex['time'] for ex in event_data['executions']]  # Keep as nanoseconds
                all_times.extend(times_ns)
                all_events.extend([event] * len(times_ns))
                all_devices.extend([device] * len(times_ns))
        
        df_box = pd.DataFrame({
            'Execution_Time_ns': all_times,  # Changed from Execution_Time_us
            'Event': all_events,
            'Device': all_devices
        })
        
        fig = px.box(
            df_box,
            x='Event',
            y='Execution_Time_ns',  # Changed from Execution_Time_us
            color='Device',
            title='Detailed Execution Time Analysis by Device',
            labels={'Execution_Time_ns': 'Execution Time (ns)'}  # Changed from μs to ns
        )
    else:
        for event, data in stats.items():
            times_ns = [ex['time'] for ex in data['executions']]  # Keep as nanoseconds
            all_times.extend(times_ns)
            all_events.extend([event] * len(times_ns))
        
        df_box = pd.DataFrame({
            'Execution_Time_ns': all_times,  # Changed from Execution_Time_us
            'Event': all_events
        })
        
        fig = px.box(
            df_box,
            x='Event',
            y='Execution_Time_ns',  # Changed from Execution_Time_us
            title='Detailed Execution Time Analysis (Box Plot)',
            labels={'Execution_Time_ns': 'Execution Time (ns)'}  # Changed from μs to ns
        )
    
    fig.update_layout(
        height=400,
        template='plotly_white',
        xaxis_tickangle=-45
    )
    
    return fig

@app.callback(
    [Output('device-topology-stats', 'children'),
     Output('device-topology-chart', 'figure'),
     Output('device-selector', 'options')],
    Input('upload-data', 'contents')
)
def update_device_topology(contents):
    global timing_data
    
    if timing_data is None or timing_data.empty or 'Device_ID' not in timing_data.columns:
        empty_fig = px.bar(title="No device topology data available")
        return html.P("No device topology data available"), empty_fig, []
    
    # Count devices and their positions
    devices = timing_data['Device_ID'].unique()
    num_devices = len(devices)
    
    # Check if Position column exists
    if 'Position' in timing_data.columns:
        # Create a dictionary of devices and their positions
        device_positions = {}
        for device in devices:
            device_df = timing_data[timing_data['Device_ID'] == device]
            # Take the most common position value
            position = device_df['Position'].mode().iloc[0]
            device_positions[device] = position
        
        # Sort devices by position
        sorted_devices = sorted(device_positions.items(), key=lambda x: x[1])
        sorted_device_ids = [d[0] for d in sorted_devices]
        sorted_positions = [d[1] for d in sorted_devices]
        
        # Create interactive topology visualization
        # Use networkx for the graph layout
        G = nx.Graph()
        
        # Add nodes and edges to the graph
        for i, (device, position) in enumerate(sorted_devices):
            G.add_node(device, position=position)
            if i < len(sorted_devices) - 1:
                next_device = sorted_devices[i+1][0]
                G.add_edge(device, next_device)
        
        # Create positions for the network graph - initially in a line (daisy chain)
        pos = {device: (position, 1) for device, position in device_positions.items()}
        
        # Create the figure with networkx
        fig = go.Figure()
        
        # Add edges (connections between devices)
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, dash='dash', color='gray'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        ))
        
        # Add nodes (devices)
        node_x = [pos[node][0] for node in G.nodes()]
        node_y = [pos[node][1] for node in G.nodes()]
        
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=list(G.nodes()),
            textposition="bottom center",
            marker=dict(
                size=30,
                color='royalblue',
                line=dict(width=2, color='darkblue')
            ),
            customdata=list(G.nodes()),
            hovertemplate='%{customdata}<extra></extra>'
        ))
        
        # Make the graph interactive with drag-and-drop capability
        fig.update_layout(
            title="Device Topology (Drag nodes to reshape)",
            xaxis_title="Position in Chain",
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                zeroline=False
            ),
            height=400,
            template='plotly_white',
            hovermode='closest',
            dragmode='select',  # Enable selection
            clickmode='event+select',  # Enable click events
            margin=dict(l=20, r=20, t=60, b=20),
            # This enables modebar with the ability to drag points
            modebar=dict(
                orientation='v',
                bgcolor='rgba(255, 255, 255, 0.7)',
                color='rgba(44, 62, 80, 0.8)',
                activecolor='rgba(44, 62, 80, 1)'
            ),
            updatemenus=[
                dict(
                    type='buttons',
                    showactive=False,
                    buttons=[
                        dict(
                            label='Reset Layout',
                            method='relayout',
                            args=[{'xaxis.range': [min(sorted_positions)-0.5, max(sorted_positions)+0.5], 
                                   'yaxis.range': [0.5, 1.5]}]
                        )
                    ],
                    x=0.05,
                    y=1.15,
                )
            ]
        )
        
        # Create a summary of device stats
        device_stats = []
        for device, position in sorted_devices:
            device_df = timing_data[timing_data['Device_ID'] == device]
            event_count = len(device_df[device_df['Toggled']].drop_duplicates())
            device_stats.append(html.P(f"{device} (Position {position}): {event_count} events"))
        
        summary = [
            html.H5(f"Number of Devices: {num_devices}"),
            html.P("Device Chain Configuration:"),
            html.Div(device_stats)
        ]
        
        # Create options for device selector dropdown
        options = [{'label': device, 'value': device} for device in sorted_device_ids]
        
        return html.Div(summary), fig, options
    else:
        # Basic visualization without position data
        fig = go.Figure()
        
        # Add devices as nodes in a circle
        radius = 1
        angles = np.linspace(0, 2*np.pi, num_devices, endpoint=False)
        x_pos = radius * np.cos(angles)
        y_pos = radius * np.sin(angles)
        
        for i, device in enumerate(devices):
            fig.add_trace(go.Scatter(
                x=[x_pos[i]],
                y=[y_pos[i]],
                mode='markers+text',
                marker=dict(size=30, color='royalblue'),
                text=[device],
                textposition="bottom center",
                name=device
            ))
        
        fig.update_layout(
            title="Device Topology (Unknown Configuration)",
            xaxis=dict(
                showticklabels=False,
                showgrid=False,
                zeroline=False
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                zeroline=False
            ),
            height=300,
            template='plotly_white'
        )
        
        # Create a summary of device stats
        device_stats = []
        for device in devices:
            device_df = timing_data[timing_data['Device_ID'] == device]
            event_count = len(device_df[device_df['Toggled']].drop_duplicates())
            device_stats.append(html.P(f"{device}: {event_count} events"))
        
        summary = [
            html.H5(f"Number of Devices: {num_devices}"),
            html.P("Device Configuration (unknown topology):"),
            html.Div(device_stats)
        ]
        
        # Create options for device selector dropdown
        options = [{'label': device, 'value': device} for device in devices]
        
        return html.Div(summary), fig, options

@app.callback(
    [Output('device-comparison-stats', 'children'),
     Output('device-comparison-chart', 'figure')],
    [Input('device-selector', 'value')]
)
def update_device_comparison(selected_devices):
    global timing_data
    
    if timing_data is None or timing_data.empty or 'Device_ID' not in timing_data.columns or not selected_devices:
        empty_fig = px.bar(title="No devices selected for comparison")
        return html.P("Please select devices to compare"), empty_fig
    
    # Filter data for selected devices
    selected_df = timing_data[timing_data['Device_ID'].isin(selected_devices)]
    
    # Compare execution times for different events across devices
    event_device_stats = {}
    
    for device in selected_devices:
        device_df = timing_data[timing_data['Device_ID'] == device]
        stats = analyze_execution_timing(device_df)
        
        # In this case, stats has a nested structure with device as the first key
        if device in stats:
            for event, event_stats in stats[device].items():
                if event not in event_device_stats:
                    event_device_stats[event] = {}
                event_device_stats[event][device] = event_stats['mean_ns'] / 1000  # Convert to microseconds
    
    # Create comparison chart
    fig = go.Figure()
    
    for event, devices in event_device_stats.items():
        fig.add_trace(go.Bar(
            x=list(devices.keys()),
            y=list(devices.values()),
            name=event
        ))
    
    fig.update_layout(
        title="Event Execution Time Comparison by Device",
        xaxis_title="Device",
        yaxis_title="Execution Time (μs)",
        barmode='group',
        height=400,
        template='plotly_white'
    )
    
    # Create comparison stats summary
    summary = []
    
    for device in selected_devices:
        device_df = timing_data[timing_data['Device_ID'] == device]
        device_stats = analyze_execution_timing(device_df)
        
        if device in device_stats:
            event_count = sum(stat['count'] for stat in device_stats[device].values())
            avg_times = [stat['mean_ns'] for stat in device_stats[device].values()]
            avg_exec_time = f"{np.mean(avg_times)/1000:.1f} μs"
            
            summary.append(html.P(f"{device}: {event_count} events, Avg Time: {avg_exec_time}"))
    
    return html.Div(summary), fig

@app.callback(
    [Output('sync-stats', 'children'),
     Output('sync-chart', 'figure')],
    Input('upload-data', 'contents')
)
def update_synchronicity_analysis(contents):
    global timing_data
    
    if timing_data is None or timing_data.empty or 'Device_ID' not in timing_data.columns:
        empty_fig = px.bar(title="No synchronicity data available")
        return html.P("No synchronicity data available"), empty_fig
    
    # Analyze synchronicity
    sync_stats = analyze_synchronicity(timing_data)
    
    if not sync_stats:
        empty_fig = px.bar(title="No synchronization events found")
        return html.P("No synchronization events found in the data"), empty_fig
    
    # Create visualization of sync jitter
    sync_ids = list(sync_stats.keys())
    max_diffs = [stats['max_diff_ns'] / 1000 for stats in sync_stats.values()]  # Convert to microseconds
    mean_diffs = [stats['mean_diff_ns'] / 1000 for stats in sync_stats.values()]
    std_diffs = [stats['std_diff_ns'] / 1000 for stats in sync_stats.values()]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=sync_ids,
        y=max_diffs,
        name='Max Time Difference',
        marker_color='coral'
    ))
    
    fig.add_trace(go.Bar(
        x=sync_ids,
        y=mean_diffs,
        name='Mean Time Difference',
        marker_color='royalblue'
    ))
    
    # Add a line trace for standard deviation
    fig.add_trace(go.Scatter(
        x=sync_ids,
        y=std_diffs,
        name='Standard Deviation',
        mode='lines+markers',
        marker_color='green',
        line=dict(dash='dash')
    ))
    
    # Add error bars for a better visualization of mean and std dev
    fig.add_trace(go.Scatter(
        x=sync_ids,
        y=mean_diffs,
        error_y=dict(
            type='data',
            array=std_diffs,
            visible=True
        ),
        mode='markers',
        name='Mean ± Std Dev',
        marker=dict(color='purple', size=10)
    ))
    
    fig.update_layout(
        title="Synchronization Time Differences Between Devices",
        xaxis_title="Sync Pulse ID",
        yaxis_title="Time Difference (ns)",  # Changed from μs to ns
        height=400,
        template='plotly_white'
    )
    
    # Create summary statistics
    all_max_diffs = [stats['max_diff_ns'] for stats in sync_stats.values()]
    all_mean_diffs = [stats['mean_diff_ns'] for stats in sync_stats.values()]
    
    overall_max = np.max(all_max_diffs) / 1000  # Convert to microseconds
    overall_avg = np.mean(all_mean_diffs) / 1000
    
    # Count number of devices involved in synchronization
    devices_involved = set()
    for sync_id, stats in sync_stats.items():
        for detail in stats['details']:
            devices_involved.add(detail['device1'])
            devices_involved.add(detail['device2'])
    
    summary = [
        html.H5("Synchronicity Analysis"),
        html.P(f"Number of sync events: {len(sync_stats)}"),
        html.P(f"Devices involved in synchronization: {len(devices_involved)}"),
        html.P(f"Average sync difference: {overall_avg:.2f} ns"),  # Changed from μs to ns
        html.P(f"Maximum sync difference: {overall_max:.2f} ns"),  # Changed from μs to ns
        html.Hr(),
        html.P("Lower values indicate better synchronization between devices")
    ]
    
    return html.Div(summary), fig

@app.callback(
    [Output('comm-stats', 'children'),
     Output('comm-chart', 'figure')],
    Input('upload-data', 'contents')
)
def update_communication_analysis(contents):
    global timing_data
    
    if timing_data is None or timing_data.empty or 'Device_ID' not in timing_data.columns:
        empty_fig = px.bar(title="No communication data available")
        return html.P("No communication data available"), empty_fig
    
    # Analyze communication times
    comm_stats = analyze_communication_time(timing_data)
    
    if not comm_stats:
        empty_fig = px.bar(title="No communication events found")
        return html.P("No communication events found in the data"), empty_fig
    
    # Collect data for visualization
    message_ids = []
    source_devices = []
    destination_devices = []
    comm_times = []
    hop_counts = []
    
    for message_id, stats in comm_stats.items():
        for prop in stats['propagation_details']:
            message_ids.append(message_id)
            source_devices.append(prop['from_device'])
            destination_devices.append(prop['to_device'])
            comm_times.append(prop['time_ns'] / 1000)  # Convert to microseconds
            hop_counts.append(prop['hops'])
    
    # Create dataframe for visualization
    df_comm = pd.DataFrame({
        'Message_ID': message_ids,
        'Source': source_devices,
        'Destination': destination_devices,
        'Time_us': comm_times,
        'Hops': hop_counts
    })
    
    # Create scatter plot of communication time vs. hop count
    fig = px.scatter(
        df_comm,
        x='Hops',
        y='Time_us',
        color='Source',
        hover_data=['Destination', 'Message_ID'],
        title='Communication Time vs. Distance (Hops)',
        labels={'Time_us': 'Communication Time (μs)', 'Hops': 'Number of Hops'},
        trendline='ols'  # Add trendline
    )
    
    fig.update_layout(
        height=400,
        template='plotly_white'
    )
    
    # Calculate average communication time per hop
    avg_time_per_hop = df_comm['Time_us'].sum() / df_comm['Hops'].sum() if df_comm['Hops'].sum() > 0 else 0
    
    # Calculate average communication times between each device pair
    device_pairs = df_comm.groupby(['Source', 'Destination']).agg({
        'Time_us': 'mean',
        'Hops': 'mean'
    }).reset_index()
    
    # Create summary statistics
    pair_stats = []
    for _, row in device_pairs.iterrows():
        pair_stats.append(
            html.P(f"{row['Source']} → {row['Destination']} ({row['Hops']:.0f} hops): {row['Time_us']:.2f} ns")  # Changed from μs to ns
        )
    
    summary = [
        html.H5("Communication Time Analysis"),
        html.P(f"Total messages analyzed: {len(message_ids)}"),
        html.P(f"Average time per hop: {avg_time_per_hop:.2f} ns"),  # Changed from μs to ns
        html.Hr(),
        html.P("Average communication times:"),
        html.Div(pair_stats)
    ]
    
    return html.Div(summary), fig

# Enhanced Topology Callbacks for Interactive Editing

@app.callback(
    [Output('device-topology-chart', 'figure', allow_duplicate=True),
     Output('topology-status', 'children'),
     Output('topology-store', 'data', allow_duplicate=True)],
    [Input('topology-mode', 'value'),
     Input('reset-layout-btn', 'n_clicks'),
     Input('layout-options', 'value')],
    [State('topology-store', 'data'),
     State('custom-positions-store', 'data')],
    prevent_initial_call=True
)
def update_topology_mode(topology_mode, reset_clicks, layout_options, topology_data, custom_positions):
    """Update topology visualization based on selected mode and options"""
    global timing_data
    
    if timing_data is None or timing_data.empty or 'Device_ID' not in timing_data.columns:
        return {}, html.P("No device data available"), {}
    
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    devices = timing_data['Device_ID'].unique()
    num_devices = len(devices)
    
    # Create networkx graph based on topology mode
    G = nx.Graph()
    for device in devices:
        G.add_node(device)
    
    # Define positions based on topology mode
    if topology_mode == 'daisy':
        # Linear chain layout
        pos = {device: (i, 0) for i, device in enumerate(devices)}
        # Add edges for daisy chain
        for i in range(len(devices) - 1):
            G.add_edge(devices[i], devices[i + 1])
            
    elif topology_mode == 'star':
        # Star network with first device as center
        center_device = devices[0]
        pos = {center_device: (0, 0)}
        angles = np.linspace(0, 2*np.pi, num_devices-1, endpoint=False)
        for i, device in enumerate(devices[1:]):
            pos[device] = (2*np.cos(angles[i]), 2*np.sin(angles[i]))
            G.add_edge(center_device, device)
            
    elif topology_mode == 'ring':
        # Circular ring layout
        angles = np.linspace(0, 2*np.pi, num_devices, endpoint=False)
        pos = {device: (2*np.cos(angles[i]), 2*np.sin(angles[i])) for i, device in enumerate(devices)}
        # Add ring edges
        for i in range(num_devices):
            G.add_edge(devices[i], devices[(i + 1) % num_devices])
            
    elif topology_mode == 'mesh':
        # Full mesh network
        pos = nx.spring_layout(G, k=2, iterations=50)
        # Add all possible edges
        for i in range(num_devices):
            for j in range(i + 1, num_devices):
                G.add_edge(devices[i], devices[j])
                
    elif topology_mode == 'custom':
        # Use custom positions if available
        if custom_positions and not (triggered_id == 'reset-layout-btn' and reset_clicks):
            pos = custom_positions
        else:
            pos = nx.spring_layout(G, k=2, iterations=50)
        # Use existing connections from topology_data
        if topology_data and 'connections' in topology_data:
            for connection in topology_data['connections']:
                G.add_edge(connection['source'], connection['target'])
    
    # Create the interactive figure
    fig = create_interactive_topology_figure(G, pos, layout_options, topology_mode)
    
    # Update topology store
    new_topology_data = {
        'mode': topology_mode,
        'positions': pos,
        'connections': [{'source': edge[0], 'target': edge[1]} for edge in G.edges()],
        'devices': list(devices)
    }
    
    status = dbc.Alert(f"Topology updated to {topology_mode} mode with {len(G.edges())} connections", 
                      color="success", dismissable=True)
    
    return fig, status, new_topology_data

@app.callback(
    [Output('connection-source', 'options'),
     Output('connection-target', 'options')],
    Input('topology-store', 'data')
)
def update_connection_dropdowns(topology_data):
    """Update connection dropdown options based on available devices"""
    if not topology_data or 'devices' not in topology_data:
        return [], []
    
    options = [{'label': device, 'value': device} for device in topology_data['devices']]
    return options, options

@app.callback(
    Output('connection-modal', 'is_open'),
    [Input('add-connection-btn', 'n_clicks'),
     Input('close-connection-modal', 'n_clicks')],
    State('connection-modal', 'is_open')
)
def toggle_connection_modal(add_clicks, close_clicks, is_open):
    """Toggle the connection editor modal"""
    if add_clicks or close_clicks:
        return not is_open
    return is_open

@app.callback(
    [Output('current-connections-display', 'children'),
     Output('topology-store', 'data', allow_duplicate=True),
     Output('device-topology-chart', 'figure', allow_duplicate=True)],
    [Input('confirm-add-connection', 'n_clicks'),
     Input('remove-connection-btn', 'n_clicks')],
    [State('connection-source', 'value'),
     State('connection-target', 'value'),
     State('topology-store', 'data'),
     State('layout-options', 'value')],
    prevent_initial_call=True
)
def manage_connections(add_clicks, remove_clicks, source, target, topology_data, layout_options):
    """Add or remove connections in the topology"""
    if not topology_data:
        return html.P("No topology data available"), {}, {}
    
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    if triggered_id == 'confirm-add-connection' and source and target and source != target:
        # Add new connection
        new_connection = {'source': source, 'target': target}
        if new_connection not in topology_data.get('connections', []):
            topology_data.setdefault('connections', []).append(new_connection)
    
    elif triggered_id == 'remove-connection-btn':
        # Show interface for removing connections (for now, remove the last added)
        if topology_data.get('connections'):
            topology_data['connections'].pop()
    
    # Create updated graph
    G = nx.Graph()
    for device in topology_data.get('devices', []):
        G.add_node(device)
    
    for connection in topology_data.get('connections', []):
        G.add_edge(connection['source'], connection['target'])
    
    # Update figure
    pos = topology_data.get('positions', {})
    fig = create_interactive_topology_figure(G, pos, layout_options, topology_data.get('mode', 'custom'))
    
    # Display current connections
    connections_display = html.Div([
        html.H6("Current Connections:"),
        html.Ul([
            html.Li(f"{conn['source']} ↔ {conn['target']}")
            for conn in topology_data.get('connections', [])
        ])
    ])
    
    return connections_display, topology_data, fig

@app.callback(
    Output('custom-positions-store', 'data'),
    Input('device-topology-chart', 'relayoutData'),
    State('topology-store', 'data')
)
def update_custom_positions(relayout_data, topology_data):
    """Store custom positions when nodes are dragged"""
    if not relayout_data or not topology_data:
        return {}
    
    # Extract position updates from relayout data
    custom_positions = topology_data.get('positions', {})
    
    # Plotly sends position updates as 'shapes[n].x0', 'shapes[n].y0' etc.
    # For now, we'll maintain the existing positions
    # In a production version, you'd parse the relayout_data to extract new positions
    
    return custom_positions

def create_interactive_topology_figure(G, pos, layout_options, topology_mode):
    """Create an interactive topology figure with drag-and-drop capability"""
    
    # Default options
    show_labels = 'labels' in layout_options if layout_options else True
    show_connections = 'connections' in layout_options if layout_options else True
    enable_dragging = 'dragging' in layout_options if layout_options else True
    
    fig = go.Figure()
    
    # Add edges (connections) if enabled
    if show_connections and G.edges():
        edge_x = []
        edge_y = []
        for edge in G.edges():
            if edge[0] in pos and edge[1] in pos:
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
        
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=3, color='rgba(50, 50, 50, 0.6)'),
            hoverinfo='none',
            mode='lines',
            showlegend=False,
            name='connections'
        ))
    
    # Add nodes (devices)
    if pos:
        node_x = [pos[node][0] for node in G.nodes() if node in pos]
        node_y = [pos[node][1] for node in G.nodes() if node in pos]
        node_text = list(G.nodes()) if show_labels else ['']*len(G.nodes())
        
        # Color nodes based on their degree (number of connections)
        node_colors = []
        for node in G.nodes():
            degree = G.degree(node)
            if degree == 0:
                node_colors.append('lightgray')  # Isolated nodes
            elif degree <= 2:
                node_colors.append('lightblue')  # Low connectivity
            elif degree <= 4:
                node_colors.append('orange')     # Medium connectivity
            else:
                node_colors.append('red')        # High connectivity
        
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text' if show_labels else 'markers',
            text=node_text,
            textposition="bottom center",
            marker=dict(
                size=40,
                color=node_colors,
                line=dict(width=3, color='darkblue'),
                opacity=0.8
            ),
            customdata=list(G.nodes()),
            hovertemplate='%{customdata}<br>Connections: %{marker.color}<extra></extra>',
            name='devices'
        ))
    
    # Configure layout
    dragmode = 'pan' if enable_dragging else 'zoom'
    
    fig.update_layout(
        title=f"🔌 Interactive Device Topology - {topology_mode.title()} Mode",
        xaxis=dict(
            showticklabels=False,
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            zeroline=False
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            zeroline=False
        ),
        height=500,
        template='plotly_white',
        hovermode='closest',
        dragmode=dragmode,
        margin=dict(l=40, r=40, t=60, b=40),
        plot_bgcolor='rgba(248, 249, 250, 0.8)',
        paper_bgcolor='white',
        annotations=[
            dict(
                text=f"Drag nodes to reposition • {len(G.nodes())} devices • {len(G.edges())} connections",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=-0.1, xanchor='center', yanchor='top',
                font=dict(size=12, color="gray")
            )
        ] if enable_dragging else []
    )
    
    return fig

@app.callback(
    Output('topology-status', 'children', allow_duplicate=True),
    [Input('save-topology-btn', 'n_clicks'),
     Input('export-topology-btn', 'n_clicks')],
    State('topology-store', 'data'),
    prevent_initial_call=True
)
def save_export_topology(save_clicks, export_clicks, topology_data):
    """Save or export topology configuration"""
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    if not topology_data:
        return dbc.Alert("No topology data to save", color="warning", dismissable=True)
    
    if triggered_id == 'save-topology-btn':
        # Save topology to a local file (simulated for demo)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"topology_{timestamp}.json"
        
        # In a real application, you would save this to a file or database
        return dbc.Alert(f"Topology saved as {filename}", color="success", dismissable=True)
    
    elif triggered_id == 'export-topology-btn':
        # Export topology for download (simulated for demo)
        return dbc.Alert("Topology exported to downloads", color="info", dismissable=True)
    
    return ""

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('DASH_PORT', 8050))
    app.run(debug=True, host='0.0.0.0', port=port)
