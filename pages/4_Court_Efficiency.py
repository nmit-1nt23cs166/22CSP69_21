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

st.title('🏛 Court Efficiency Analysis')

st.markdown(
    '### Active Court Performance & Delay Analytics'
)

# =====================================================
# REMOVE INACTIVE STAGES
# =====================================================

inactive_stages = [

    'Disposed',
    'Disposed Otherwise',
    'Dismissed',
    'Dismissed For Default',
    'Closed',
    'Judgment'

]

# =====================================================
# ACTIVE CASES ONLY
# =====================================================

active_df = df[
    ~df['stage_of_case']
    .isin(inactive_stages)
]

# =====================================================
# REMOVE INVALID DELAYS
# =====================================================

active_df = active_df[
    active_df['case_age_days'] > 0
]

# =====================================================
# HANDLE HEARING GAPS
# =====================================================

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

# =====================================================
# COURT ANALYTICS
# =====================================================

court_stats = (

    active_df.groupby('court_name')
    .agg({

        'case_age_days': 'mean',

        'hearing_gap_days': 'mean',

        'priority_score': 'mean'

    })
    .reset_index()

)

# =====================================================
# CASE COUNTS
# =====================================================

case_counts = (

    active_df['court_name']
    .value_counts()
    .reset_index()

)

case_counts.columns = [

    'court_name',

    'total_cases'

]

court_stats = court_stats.merge(

    case_counts,

    on='court_name'

)

# =====================================================
# KEEP COURTS WITH AT LEAST 1 CASE
# =====================================================

court_stats = court_stats[
    court_stats['total_cases'] >= 1
]

# =====================================================
# DELAY BURDEN SCORE
# =====================================================

court_stats['delay_burden_score'] = (

    court_stats['case_age_days'] * 0.5 +

    court_stats['hearing_gap_days'] * 0.3 +

    court_stats['priority_score'] * 0.2

)

# =====================================================
# SORTING
# =====================================================

worst_courts = court_stats.sort_values(

    by='delay_burden_score',

    ascending=False

)

best_courts = court_stats.sort_values(

    by='delay_burden_score',

    ascending=True

)

# =====================================================
# KPI SECTION
# =====================================================

st.subheader('📊 Court Analytics')

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        'Active Courts',
        len(court_stats)
    )

with col2:

    st.metric(
        'Average Court Delay',
        f"{round(court_stats['case_age_days'].mean())} Days"
    )

with col3:

    st.metric(
        'Average Hearing Gap',
        f"{round(court_stats['hearing_gap_days'].mean())} Days"
    )

# =====================================================
# HIGHEST DELAY COURTS
# =====================================================

st.subheader('⚠ Courts with Highest Delay Burden')

fig1 = px.bar(

    worst_courts.head(10),

    x='court_name',

    y='delay_burden_score',

    color='delay_burden_score',

    text='delay_burden_score'

)

st.plotly_chart(
    fig1,
    use_container_width=True
)

# =====================================================
# BEST COURTS
# =====================================================

st.subheader('✅ Courts with Lowest Delay Burden')

fig2 = px.bar(

    best_courts.head(10),

    x='court_name',

    y='delay_burden_score',

    color='delay_burden_score',

    text='delay_burden_score'

)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# =====================================================
# COURT PERFORMANCE TABLE
# =====================================================

st.subheader('📋 Court Performance Table')

display_table = court_stats[[

    'court_name',

    'total_cases',

    'case_age_days',

    'hearing_gap_days',

    'priority_score',

    'delay_burden_score'

]]

display_table.columns = [

    'Court',

    'Total Cases',

    'Average Delay',

    'Average Hearing Gap',

    'Priority Score',

    'Delay Burden Score'

]

st.dataframe(display_table)

# =====================================================
# BOTTLENECK COURTS
# =====================================================

st.subheader('🚧 Court Bottleneck Detection')

top_bottlenecks = worst_courts.head(5)

for index, row in top_bottlenecks.iterrows():

    st.error(

        f"""
        Court:
        {row['court_name']}

        Average Delay:
        {round(row['case_age_days'])} days

        Average Hearing Gap:
        {round(row['hearing_gap_days'])} days

        Delay Burden Score:
        {round(row['delay_burden_score'])}

        Cases:
        {row['total_cases']}
        """

    )

# =====================================================
# BEST COURTS
# =====================================================

st.subheader('🏆 Best Performing Courts')

top_best = best_courts.head(5)

for index, row in top_best.iterrows():

    st.success(

        f"""
        Court:
        {row['court_name']}

        Average Delay:
        {round(row['case_age_days'])} days

        Average Hearing Gap:
        {round(row['hearing_gap_days'])} days

        Delay Burden Score:
        {round(row['delay_burden_score'])}
        """

    )

# =====================================================
# KEY INSIGHTS
# =====================================================

st.subheader('📌 Key Insights')

worst = worst_courts.iloc[0]

best = best_courts.iloc[0]

st.error(

    f"""
    {worst['court_name']} currently shows
    the highest active judicial delay burden.

    Delay Burden Score:
    {round(worst['delay_burden_score'])}
    """

)

st.success(

    f"""
    {best['court_name']} currently appears
    to have the lowest judicial delay burden.

    Delay Burden Score:
    {round(best['delay_burden_score'])}
    """

)