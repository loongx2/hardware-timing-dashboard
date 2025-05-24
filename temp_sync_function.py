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
        yaxis_title="Time Difference (μs)",
        height=400,
        template='plotly_white'
    )
    
    # Create summary statistics
    all_max_diffs = [stats['max_diff_ns'] for stats in sync_stats.values()]
    all_mean_diffs = [stats['mean_diff_ns'] for stats in sync_stats.values()]
    
    overall_max = np.max(all_max_diffs) / 1000  # Convert to microseconds
    overall_avg = np.mean(all_mean_diffs) / 1000
