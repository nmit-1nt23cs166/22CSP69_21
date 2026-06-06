import streamlit as st
import plotly.express as px

from preprocessing import preprocess_data

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title='Judicial Delay Intelligence System',
    layout='wide'
)

# =====================================================
# CUSTOM UI
# =====================================================

st.markdown("""
<style>

.main {
    background-color: #0E1117;
    color: white;
}

[data-testid="stMetric"] {
    background-color: #1E1E1E;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #333;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# LOAD DATA
# =====================================================

df = preprocess_data('cleaned_cases.csv')
#st.write(df.columns)

# =====================================================
# HEADER
# =====================================================

st.title('⚖ Judicial Delay Intelligence System')

st.markdown(
    '### Karnataka Judiciary Pendency & Bottleneck Analytics'
)

# =====================================================
# SIDEBAR FILTERS
# =====================================================

st.sidebar.header('Dashboard Filters')

selected_districts = st.sidebar.multiselect(
    'Select District',
    sorted(df['district_name'].unique()),
    default=sorted(df['district_name'].unique())
)

selected_risk = st.sidebar.multiselect(
    'Select Risk',
    ['Low', 'Medium', 'High'],
    default=['Low', 'Medium', 'High']
)

filtered_df = df[
    (df['district_name'].isin(selected_districts)) &
    (df['calculated_risk'].isin(selected_risk))
]

# =====================================================
# KPI SECTION
# =====================================================

st.subheader('📌 Dashboard Overview')

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        'Total Cases',
        len(filtered_df)
    )

with col2:

    st.metric(
        'Average Delay',
        f"{round(filtered_df['case_age_days'].mean())} Days"
    )

with col3:

    st.metric(
        'High Risk Cases',
        len(
            filtered_df[
                filtered_df['calculated_risk'] == 'High'
            ]
        )
    )

with col4:

    st.metric(
        'Long Pending Cases',
        len(
            filtered_df[
                filtered_df['long_pending'] == True
            ]
        )
    )

# =====================================================
# DISTRICT PENDENCY
# =====================================================

st.subheader('📊 District-wise Pendency')

pendency = (

    filtered_df['district_name']
    .value_counts()
    .reset_index()

)

pendency.columns = [

    'District',

    'Cases'

]

fig1 = px.bar(

    pendency,

    x='District',

    y='Cases',

    color='Cases',

    text='Cases'

)

st.plotly_chart(
    fig1,
    use_container_width=True
)

# =====================================================
# ACTIVE WORKFLOW STAGE DELAY ANALYSIS
# =====================================================

st.subheader('⚠ Active Workflow Stage Delay Analysis')

chart_df = filtered_df.copy()

chart_df['stage_of_case'] = (
    chart_df['stage_of_case']
    .astype(str)
    .str.strip()
    .str.upper()
)

inactive_stages = [
    'DISPOSED',
    'DISPOSED OTHERWISE',
    'DISMISSED',
    'DISMISSED FOR DEFAULT',
    'CONVICTED',
    'ACQUITTED',
    'ABATED',
    'WITHDRAWN',
    'CLOSED',
    'JUDGMENT'
]

chart_df = chart_df[
    ~chart_df['stage_of_case'].isin(inactive_stages)
]

stage_delay = (
    chart_df.groupby('stage_of_case')['case_age_days']
    .mean()
    .reset_index()
)

stage_delay = stage_delay.sort_values(
    by='case_age_days',
    ascending=False
)

fig2 = px.bar(
    stage_delay,
    x='stage_of_case',
    y='case_age_days',
    color='case_age_days',
    text='case_age_days',
    title='Average Delay by Active Workflow Stage'
)

fig2.update_layout(
    xaxis_title='Active Stage',
    yaxis_title='Average Delay (Days)',
    xaxis_tickangle=-45
)

st.plotly_chart(
    fig2,
    use_container_width=True
)
# =====================================================
# ACTIVE STAGE HEATMAP
# =====================================================

st.subheader('🔥 District vs Active Stage Delay Heatmap')

heatmap_df = filtered_df.copy()

heatmap_df['stage_of_case'] = (
    heatmap_df['stage_of_case']
    .astype(str)
    .str.strip()
    .str.upper()
)

inactive_stages = [
    'DISPOSED',
    'DISPOSED OTHERWISE',
    'DISMISSED',
    'DISMISSED FOR DEFAULT',
    'CONVICTED',
    'ACQUITTED',
    'ABATED',
    'WITHDRAWN',
    'CLOSED',
    'JUDGMENT'
]

heatmap_df = heatmap_df[
    ~heatmap_df['stage_of_case'].isin(inactive_stages)
]

heatmap_data = heatmap_df.pivot_table(
    values='case_age_days',
    index='district_name',
    columns='stage_of_case',
    aggfunc='mean'
)

fig3 = px.imshow(
    heatmap_data,
    text_auto=True,
    aspect='auto',
    title='Average Delay by District and Active Workflow Stage'
)

st.plotly_chart(
    fig3,
    use_container_width=True
)
# =====================================================
# HEARING GAP ANALYSIS
# =====================================================

st.subheader('📅 Hearing Gap Analysis')

gap_df = filtered_df.copy()

# Replace zero gaps with median
valid_gaps = gap_df[
    gap_df['hearing_gap_days'] > 0
]

if len(valid_gaps) > 0:

    median_gap = valid_gaps[
        'hearing_gap_days'
    ].median()

else:

    median_gap = 30

gap_df['hearing_gap_days'] = gap_df[
    'hearing_gap_days'
].replace(0, median_gap)

fig4 = px.box(

    gap_df,

    x='district_name',

    y='hearing_gap_days',

    color='district_name'

)

st.plotly_chart(
    fig4,
    use_container_width=True
)

# =====================================================
# DISTRICT HEALTH SCORE
# =====================================================

st.subheader('🏥 District Health Score')

health = (

    filtered_df.groupby('district_name')
    .agg({

        'case_age_days': 'mean',
        'hearing_gap_days': 'mean',
        'priority_score': 'mean'

    })
    .reset_index()

)

# -----------------------------------------------------
# NORMALIZATION
# -----------------------------------------------------

health['age_norm'] = (

    (health['case_age_days'] - health['case_age_days'].min())

    /

    (health['case_age_days'].max() - health['case_age_days'].min())

)

health['gap_norm'] = (

    (health['hearing_gap_days'] - health['hearing_gap_days'].min())

    /

    (health['hearing_gap_days'].max() - health['hearing_gap_days'].min())

)

health['priority_norm'] = (

    (health['priority_score'] - health['priority_score'].min())

    /

    (health['priority_score'].max() - health['priority_score'].min())

)

# -----------------------------------------------------
# HEALTH SCORE
# -----------------------------------------------------

health['Health Score'] = (

    80

    -

    (

        health['age_norm'] * 25 +

        health['gap_norm'] * 15 +

        health['priority_norm'] * 20

    )

)

health['Health Score'] = (
    health['Health Score']
    .clip(lower=0, upper=100)
    .round(1)
)

# -----------------------------------------------------
# HEALTH STATUS
# -----------------------------------------------------

def health_status(score):

    if score >= 70:
        return 'Good'

    elif score >= 55:
        return 'Moderate'

    elif score >= 40:
        return 'Needs Improvement'

    else:
        return 'Critical'

health['Status'] = (
    health['Health Score']
    .apply(health_status)
)

# -----------------------------------------------------
# VISUALIZATION
# -----------------------------------------------------

fig5 = px.bar(

    health.sort_values(
        by='Health Score',
        ascending=False
    ),

    x='district_name',

    y='Health Score',

    color='Health Score',

    text='Health Score',

    title='District Health Score'

)

fig5.update_layout(

    xaxis_title='District',

    yaxis_title='Health Score',

    yaxis_range=[0,100]

)

st.plotly_chart(
    fig5,
    use_container_width=True
)

# -----------------------------------------------------
# TABLE
# -----------------------------------------------------

st.dataframe(

    health[
        [
            'district_name',
            'Health Score',
            'Status'
        ]
    ],

    use_container_width=True

)
# =====================================================
# PRIORITY CASES
# =====================================================

st.subheader('🚨 Priority Cases')

inactive_stages = [

    'DISPOSED',
    'DISPOSED OTHERWISE',
    'DISMISSED',
    'DISMISSED FOR DEFAULT',
    'CONVICTED',
    'CLOSED',
    'JUDGMENT'

]

priority_df = filtered_df.copy()

# Normalize stage names
priority_df['stage_of_case'] = priority_df[
    'stage_of_case'
].astype(str).str.strip().str.upper()

# Keep only active stages
priority_df = priority_df[
    ~priority_df['stage_of_case']
    .isin(inactive_stages)
]

# Remove invalid delays
priority_df = priority_df[
    priority_df['case_age_days'] > 0
]

# Replace zero hearing gaps
valid_gaps = priority_df[
    priority_df['hearing_gap_days'] > 0
]

if len(valid_gaps) > 0:

    median_gap = valid_gaps[
        'hearing_gap_days'
    ].median()

else:

    median_gap = 30

priority_df['hearing_gap_days'] = priority_df[
    'hearing_gap_days'
].replace(0, median_gap)

# =====================================================
# PRIORITY SCORE (0-100)
# =====================================================

age_range = (
    priority_df['case_age_days'].max()
    - priority_df['case_age_days'].min()
)

gap_range = (
    priority_df['hearing_gap_days'].max()
    - priority_df['hearing_gap_days'].min()
)

if age_range == 0:
    priority_df['age_score'] = 50
else:
    priority_df['age_score'] = (
        (
            priority_df['case_age_days']
            - priority_df['case_age_days'].min()
        )
        / age_range
    ) * 100

if gap_range == 0:
    priority_df['gap_score'] = 50
else:
    priority_df['gap_score'] = (
        (
            priority_df['hearing_gap_days']
            - priority_df['hearing_gap_days'].min()
        )
        / gap_range
    ) * 100

# Final Priority Score

priority_df['priority_score'] = (

    priority_df['age_score'] * 0.7 +

    priority_df['gap_score'] * 0.3

).round(1)

# =====================================================
# TOP 3 PRIORITY CASES FROM EACH DISTRICT
# =====================================================

priority_cases = (

    priority_df

    .sort_values(
        by='priority_score',
        ascending=False
    )

    .groupby('district_name')

    .head(3)

    .sort_values(
        by='priority_score',
        ascending=False
    )

    .reset_index(drop=True)

)

columns = [

    'district_name',

    'court_name',

    'stage_of_case',

    'case_age_days',

    'hearing_gap_days',

    'priority_score',

    'delay_explanation'

]

available_columns = [

    col for col in columns
    if col in priority_cases.columns

]

st.dataframe(

    priority_cases[available_columns],

    use_container_width=True

)

# =====================================================
# BOTTLENECK DETECTION
# =====================================================

st.subheader('🚧 Bottleneck Detection')

inactive_stages = [
    'DISPOSED',
    'DISPOSED OTHERWISE',
    'DISMISSED',
    'DISMISSED FOR DEFAULT',
    'CONVICTED',
    'ACQUITTED',
    'ABATED',
    'WITHDRAWN',
    'CLOSED',
    'JUDGMENT'
]

active_df = filtered_df.copy()

# Normalize text
active_df['stage_of_case'] = active_df[
    'stage_of_case'
].astype(str).str.strip().str.upper()

inactive_stages = [

    'DISPOSED',
    'DISPOSED OTHERWISE',
    'DISMISSED',
    'DISMISSED FOR DEFAULT',
    'CLOSED',
    'JUDGMENT'

]

# Remove inactive stages
active_df = active_df[
    ~active_df['stage_of_case']
    .isin(inactive_stages)
]

# Remove invalid delays only
active_df = active_df[
    active_df['case_age_days'] > 0
]

# Replace zero hearing gaps with median
valid_gaps = active_df[
    active_df['hearing_gap_days'] > 0
]

if len(valid_gaps) > 0:

    median_gap = valid_gaps[
        'hearing_gap_days'
    ].median()

else:

    median_gap = 30

active_df['hearing_gap_days'] = active_df[
    'hearing_gap_days'
].replace(0, median_gap)

if len(active_df) == 0:

    st.warning(
        'No valid active bottleneck stages found.'
    )

else:

    bottleneck = (

        active_df.groupby('stage_of_case')
        .agg({

            'case_age_days': 'mean',

            'hearing_gap_days': 'mean'

        })
        .reset_index()

    )

    pending_counts = (

        active_df['stage_of_case']
        .value_counts()
        .reset_index()

    )

    pending_counts.columns = [

        'stage_of_case',

        'pending_count'

    ]

    bottleneck = bottleneck.merge(

        pending_counts,

        on='stage_of_case'

    )

    bottleneck['Bottleneck Score'] = (

        bottleneck['case_age_days'] * 0.4 +

        bottleneck['hearing_gap_days'] * 0.4 +

        bottleneck['pending_count'] * 0.2

    )

    worst_stage = bottleneck.sort_values(

        by='Bottleneck Score',

        ascending=False

    ).iloc[0]

    st.error(

        f"""
        {worst_stage['stage_of_case']} stage acts as the primary active bottleneck.

        Average Delay:
        {round(worst_stage['case_age_days'])} days

        Average Hearing Gap:
        {round(worst_stage['hearing_gap_days'])} days

        
        """

    )

# =====================================================
# KEY INSIGHTS
# =====================================================

st.subheader('📌 Key Insights')

highest_district = pendency.iloc[0]['District']

st.success(
    f"{highest_district} has the highest pendency concentration."
)

if len(active_df) > 0:

    st.warning(
        f"""
        Most delays currently accumulate during
        {worst_stage['stage_of_case']} stage.
        """
    )

# =====================================================
# FOOTER
# =====================================================

st.markdown('---')

st.caption(
    'Judicial Delay Intelligence & Decision Support System'
)
