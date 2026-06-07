import streamlit as st
import plotly.express as px
from preprocessing import preprocess_data

# =====================================================
# LOAD DATA
# =====================================================
df = preprocess_data('cleaned_cases.csv')

# Handle missing values
df = preprocess_data('cleaned_cases.csv')

df['priority_score'] = df['priority_score'].fillna(0)

max_val = df['priority_score'].max()

if max_val == 0:
    df['priority_score'] = 0
else:
    df['priority_score'] = (df['priority_score'] / max_val) * 88
# =====================================================
# PAGE TITLE
# =====================================================
st.title('⚠ Delay Analysis')

st.markdown('### High-Risk Case Monitoring & Delay Analytics')

# =====================================================
# HIGH RISK CASES (UNCHANGED AS REQUESTED)
# =====================================================
high_risk = df[df['calculated_risk'] == 'High']

# =====================================================
# HANDLE EMPTY DATA
# =====================================================
if len(high_risk) == 0:
    st.warning('No high-risk cases found.')

else:

    # =================================================
    # KPI SECTION
    # =================================================
    st.subheader('📊 High-Risk Overview')

    valid_gaps = high_risk[high_risk['hearing_gap_days'] > 0]

    avg_gap = round(valid_gaps['hearing_gap_days'].mean()) if len(valid_gaps) > 0 else 30

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric('High Risk Cases', len(high_risk))

    with col2:
        st.metric('Average Delay', f"{round(high_risk['case_age_days'].mean())} Days")

    with col3:
        st.metric('Average Hearing Gap', f"{avg_gap} Days")

    # =================================================
    # 🔥 FIXED: UNIFIED DISTRICT LOGIC (IMPORTANT FIX)
    # =================================================

    district_score = high_risk.groupby('district_name').agg(
        total_cases=('district_name', 'count'),
        avg_age=('case_age_days', 'mean'),
        avg_gap=('hearing_gap_days', 'mean'),
        avg_priority=('priority_score', 'mean')
    ).reset_index()

    # unified score (balances BOTH graph + bottleneck)
    district_score['final_score'] = district_score['total_cases']

    # =================================================
    # DISTRICT RISK ANALYSIS (NOW MATCHES BOTTLENECK)
    # =================================================
    st.subheader('🚨 High Risk Cases by District')

    risk_district = district_score[['district_name', 'total_cases']].sort_values(
        'total_cases', ascending=False
    ).rename(columns={'district_name': 'District', 'total_cases': 'Cases'})

    fig = px.bar(
        risk_district,
        x='District',
        y='Cases',
        color='Cases',
        text='Cases'
    )

    st.plotly_chart(fig, use_container_width=True)

    # =================================================
    # HIGH-RISK STAGES
    # =================================================
    st.subheader('⚠ High Risk Stage Analysis')

    risk_stage = high_risk.groupby('stage_of_case').size().reset_index(name='Cases')

    fig2 = px.bar(
        risk_stage,
        x='stage_of_case',
        y='Cases',
        color='Cases',
        text='Cases'
    )

    st.plotly_chart(fig2, use_container_width=True)

    # =================================================
    # HEARING GAP DISTRIBUTION
    # =================================================
    st.subheader('📅 Hearing Gap Distribution')

    gap_df = high_risk.copy()

    valid_gaps = gap_df[gap_df['hearing_gap_days'] > 0]

    median_gap = valid_gaps['hearing_gap_days'].median() if len(valid_gaps) > 0 else 30

    gap_df['hearing_gap_days'] = gap_df['hearing_gap_days'].replace(0, median_gap)

    fig3 = px.box(
        gap_df,
        x='district_name',
        y='hearing_gap_days',
        color='district_name'
    )

    st.plotly_chart(fig3, use_container_width=True)

    # =================================================
    # BOTTLENECK DISTRICTS (NOW SAME LOGIC AS GRAPH)
    # =================================================
    st.subheader('🚧 Bottleneck Districts')

    bottleneck = district_score.sort_values(
        'final_score',
        ascending=False
    )

    st.dataframe(bottleneck)

    # =================================================
    # DISTRICT INSIGHTS
    # =================================================
    st.subheader('📌 Critical District Insights')

    top_district = bottleneck.iloc[0]

    st.error(f"""
{top_district['district_name']}
has the highest HIGH-RISK case concentration.

Total High-Risk Cases:
{int(top_district['total_cases'])}


Average Delay:
{round(top_district['avg_age'])} days

Average Hearing Gap:
{round(top_district['avg_gap'])} days
""")

# =====================================================
# HIGH PRIORITY CASES (UNCHANGED)
# =====================================================
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

high_risk['stage_of_case'] = high_risk['stage_of_case'].astype(str).str.strip().str.upper()

active_high_risk = high_risk[~high_risk['stage_of_case'].isin(inactive_stages)]

top_cases = active_high_risk.sort_values(
    by='priority_score',
    ascending=False
)

top_cases = top_cases.groupby('district_name').head(2)
valid_gaps = top_cases[top_cases['hearing_gap_days'] > 0]

median_gap = valid_gaps['hearing_gap_days'].median() if len(valid_gaps) > 0 else 30

top_cases['hearing_gap_days'] = top_cases['hearing_gap_days'].replace(0, median_gap)

display_columns = [
    'district_name',
    'court_name',
    'stage_of_case',
    'case_age_days',
    'hearing_gap_days',
    'priority_score'
]

available_columns = [col for col in display_columns if col in top_cases.columns]

st.dataframe(top_cases[available_columns])
