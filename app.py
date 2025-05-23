import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import dash
from dash import dcc, html, Input, Output, callback, State
import dash_bootstrap_components as dbc
import base64
import io

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
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            
            # Validate required columns
            required_columns = ['Event', 'Time', 'Toggled']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return None, f"Missing required columns: {', '.join(missing_columns)}"
            
            # Convert Time to numeric (nanoseconds)
            df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
            
            # Convert Toggled to boolean
            df['Toggled'] = df['Toggled'].astype(bool)
            
            return df, None
        else:
            return None, "Please upload a CSV file"
            
    except Exception as e:
        return None, f"Error processing file: {str(e)}"

def analyze_execution_timing(df):
    """Analyze execution timing from hardware data"""
    if df is None or df.empty:
        return {}
    
    # Calculate execution times for each event
    execution_stats = {}
    
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
                executions.append(execution_time)
                start_time = None
        
        if executions:
            execution_stats[event] = {
                'count': len(executions),
                'mean_ns': np.mean(executions),
                'std_ns': np.std(executions),
                'min_ns': np.min(executions),
                'max_ns': np.max(executions),
                'executions': executions
            }
    
    return execution_stats

def generate_sample_data():
    """Generate sample hardware timing data for demonstration"""
    np.random.seed(42)
    
    events = ['GPIO_Init', 'ADC_Read', 'UART_Send', 'Timer_ISR', 'SPI_Transfer']
    data = []
    
    current_time = 0
    
    for _ in range(1000):
        event = np.random.choice(events)
        # Event starts
        data.append({
            'Event': event,
            'Time': current_time,
            'Toggled': True
        })
        
        # Random execution time based on event type
        if event == 'GPIO_Init':
            exec_time = np.random.normal(500, 100)  # 500ns avg
        elif event == 'ADC_Read':
            exec_time = np.random.normal(2000, 300)  # 2μs avg
        elif event == 'UART_Send':
            exec_time = np.random.normal(8000, 1000)  # 8μs avg
        elif event == 'Timer_ISR':
            exec_time = np.random.normal(1200, 200)  # 1.2μs avg
        else:  # SPI_Transfer
            exec_time = np.random.normal(3000, 500)  # 3μs avg
        
        exec_time = max(100, exec_time)  # Minimum 100ns
        current_time += exec_time
        
        # Event ends
        data.append({
            'Event': event,
            'Time': current_time,
            'Toggled': False
        })
        
        # Add some idle time
        current_time += np.random.exponential(1000)
    
    return pd.DataFrame(data)

# Load sample data
sample_df = generate_sample_data()
timing_data = sample_df  # Initialize with sample data

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
                    html.P("Expected CSV format: Event, Time (nanoseconds), Toggled (True/False)", 
                           className="text-muted small")
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

# Callbacks for file upload and data processing
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
        
        if error:
            return (
                dbc.Alert(f"Error: {error}", color="danger"),
                "N/A", "N/A", "N/A", "N/A"
            )
        
        timing_data = df
        status_msg = dbc.Alert(f"Successfully loaded {filename} with {len(df)} records", color="success")
    else:
        status_msg = dbc.Alert("Using sample data", color="info")
    
    # Calculate stats
    if timing_data is not None and not timing_data.empty:
        stats = analyze_execution_timing(timing_data)
        
        if stats:
            total_events = sum(stat['count'] for stat in stats.values())
            avg_times = [stat['mean_ns'] for stat in stats.values()]
            avg_exec_time = f"{np.mean(avg_times)/1000:.1f} μs"
            
            # Find fastest and slowest events
            fastest_event = min(stats.keys(), key=lambda x: stats[x]['mean_ns'])
            slowest_event = max(stats.keys(), key=lambda x: stats[x]['mean_ns'])
            
            fastest_time = f"{stats[fastest_event]['mean_ns']/1000:.1f} μs"
            slowest_time = f"{stats[slowest_event]['mean_ns']/1000:.1f} μs"
            
            return (
                status_msg,
                f"{total_events:,}",
                avg_exec_time,
                f"{fastest_event}: {fastest_time}",
                f"{slowest_event}: {slowest_time}"
            )
    
    return status_msg, "0", "N/A", "N/A", "N/A"

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
    
    # Create comparison chart
    events = list(stats.keys())
    mean_times = [stats[event]['mean_ns']/1000 for event in events]  # Convert to microseconds
    std_times = [stats[event]['std_ns']/1000 for event in events]
    
    fig = go.Figure()
    
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
        yaxis_title='Execution Time (μs)',
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
    
    fig = go.Figure()
    
    for event, data in stats.items():
        executions = data['executions']
        x_values = list(range(len(executions)))
        y_values = [exec_time/1000 for exec_time in executions]  # Convert to microseconds
        
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
        yaxis_title='Execution Time (μs)',
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
    
    # Combine all execution times
    all_times = []
    all_events = []
    
    for event, data in stats.items():
        times_us = [t/1000 for t in data['executions']]  # Convert to microseconds
        all_times.extend(times_us)
        all_events.extend([event] * len(times_us))
    
    df_dist = pd.DataFrame({
        'Execution_Time_us': all_times,
        'Event': all_events
    })
    
    fig = px.histogram(
        df_dist,
        x='Execution_Time_us',
        color='Event',
        title='Execution Time Distribution',
        labels={'Execution_Time_us': 'Execution Time (μs)', 'count': 'Frequency'},
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
    
    # Create box plot data
    all_times = []
    all_events = []
    
    for event, data in stats.items():
        times_us = [t/1000 for t in data['executions']]  # Convert to microseconds
        all_times.extend(times_us)
        all_events.extend([event] * len(times_us))
    
    df_box = pd.DataFrame({
        'Execution_Time_us': all_times,
        'Event': all_events
    })
    
    fig = px.box(
        df_box,
        x='Event',
        y='Execution_Time_us',
        title='Detailed Execution Time Analysis (Box Plot)',
        labels={'Execution_Time_us': 'Execution Time (μs)'}
    )
    
    fig.update_layout(
        height=400,
        template='plotly_white',
        xaxis_tickangle=-45
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
