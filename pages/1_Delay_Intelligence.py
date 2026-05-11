import streamlit as st
import plotly.express as px

from preprocessing import preprocess_data

# =====================================================
# LOAD DATA
# =====================================================

df = preprocess_data('cleaned_cases.csv')

# =====================================================
# PAGE TITLE
# =====================================================

st.title('⚠ Delay Intelligence')

st.markdown(
    '### High-Risk Case Monitoring & Delay Analytics'
)

# =====================================================
# HIGH RISK CASES
# =====================================================

high_risk = df[

    df['calculated_risk'] == 'High'

]

# =====================================================
# HANDLE EMPTY DATA
# =====================================================

if len(high_risk) == 0:

    st.warning(
        'No high-risk cases found.'
    )

else:

    # =================================================
    # KPI SECTION
    # =================================================

    st.subheader('📊 High-Risk Overview')

    valid_gaps = high_risk[
        high_risk['hearing_gap_days'] > 0
    ]

    if len(valid_gaps) > 0:

        avg_gap = round(
            valid_gaps['hearing_gap_days'].mean()
        )

    else:

        avg_gap = 30

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            'High Risk Cases',
            len(high_risk)
        )

    with col2:

        st.metric(
            'Average Delay',
            f"{round(high_risk['case_age_days'].mean())} Days"
        )

    with col3:

        st.metric(
            'Average Hearing Gap',
            f"{avg_gap} Days"
        )

    # =================================================
    # DISTRICT RISK ANALYSIS
    # =================================================

    st.subheader('🚨 High Risk Cases by District')

    risk_district = (

        high_risk['district_name']
        .value_counts()
        .reset_index()

    )

    risk_district.columns = [

        'District',

        'Cases'

    ]

    fig = px.bar(

        risk_district,

        x='District',

        y='Cases',

        color='Cases',

        text='Cases'

    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =================================================
    # HIGH-RISK STAGES
    # =================================================

    st.subheader('⚠ High Risk Stage Analysis')

    risk_stage = (

        high_risk.groupby('stage_of_case')
        .size()
        .reset_index(name='Cases')

    )

    fig2 = px.bar(

        risk_stage,

        x='stage_of_case',

        y='Cases',

        color='Cases',

        text='Cases'

    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    # =================================================
    # HEARING GAP DISTRIBUTION
    # =================================================

    st.subheader('📅 Hearing Gap Distribution')

    gap_df = high_risk.copy()

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

    fig3 = px.box(

        gap_df,

        x='district_name',

        y='hearing_gap_days',

        color='district_name'

    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    # =================================================
    # BOTTLENECK DISTRICTS
    # =================================================

    st.subheader('🚧 Bottleneck Districts')

    bottleneck = (

        high_risk.groupby('district_name')
        .agg({

            'case_age_days': 'mean',

            'hearing_gap_days': 'mean',

            'priority_score': 'mean'

        })
        .reset_index()

    )

    bottleneck['Bottleneck Score'] = (

        bottleneck['case_age_days'] * 0.5 +

        bottleneck['hearing_gap_days'] * 0.3 +

        bottleneck['priority_score'] * 0.2

    )

    bottleneck = bottleneck.sort_values(

        by='Bottleneck Score',

        ascending=False

    )

    st.dataframe(bottleneck)

    # =================================================
    # DISTRICT INSIGHTS
    # =================================================

    st.subheader('📌 Critical District Insights')

    top_district = bottleneck.iloc[0]

    st.error(

        f"""
        {top_district['district_name']}
        currently shows the highest concentration
        of high-risk judicial delays.

        Average Delay:
        {round(top_district['case_age_days'])} days

        Average Hearing Gap:
        {round(top_district['hearing_gap_days'])} days
        """

    )
# =================================================
# HIGH PRIORITY CASES
# =================================================

st.subheader('🚨 Highest Priority Cases')

inactive_stages = [

    'DISPOSED',
    'DISPOSED OTHERWISE',
    'DISMISSED',
    'DISMISSED FOR DEFAULT',
    'CONVICTED',
    'CLOSED',
    'JUDGMENT'

]

# Normalize stage names
high_risk['stage_of_case'] = high_risk[
    'stage_of_case'
].astype(str).str.strip().str.upper()

# Keep only active stages
active_high_risk = high_risk[
    ~high_risk['stage_of_case']
    .isin(inactive_stages)
]

# Highest priority ACTIVE cases
top_cases = active_high_risk.sort_values(

    by='priority_score',

    ascending=False

).head(10)

# Replace zero hearing gaps
valid_gaps = top_cases[
    top_cases['hearing_gap_days'] > 0
]

if len(valid_gaps) > 0:

    median_gap = valid_gaps[
        'hearing_gap_days'
    ].median()

else:

    median_gap = 30

top_cases['hearing_gap_days'] = top_cases[
    'hearing_gap_days'
].replace(0, median_gap)

display_columns = [

    'district_name',

    'court_name',

    'stage_of_case',

    'case_age_days',

    'hearing_gap_days',

    'priority_score'

]

available_columns = [

    col for col in display_columns
    if col in top_cases.columns

]

st.dataframe(
    top_cases[available_columns]
)