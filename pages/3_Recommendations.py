import streamlit as st
import pandas as pd
from preprocessing import preprocess_data

# =====================================================
# LOAD DATA
# =====================================================

df = preprocess_data('cleaned_cases.csv')


# FIX: replace invalid hearing gaps
df['hearing_gap_days'] = df['hearing_gap_days'].fillna(0)

median_gap = df[df['hearing_gap_days'] > 0]['hearing_gap_days'].median()

if pd.isna(median_gap):
    median_gap = 30

df['hearing_gap_days'] = df['hearing_gap_days'].replace(0, median_gap)

# =====================================================
# PAGE TITLE
# =====================================================

st.title('📌 Recommendations')

st.markdown(
    '### Judicial Decision Support & Delay Recommendations'
)

# =====================================================
# SIDEBAR FILTERS
# =====================================================

st.sidebar.header('Filters')

selected_district = st.sidebar.selectbox(

    'Select District',

    ['All'] + sorted(df['district_name'].unique())

)

selected_risk = st.sidebar.selectbox(

    'Select Risk Level',

    ['All', 'High', 'Medium', 'Low']

)

# =====================================================
# FILTER DATA
# =====================================================

filtered_df = df.copy()

if selected_district != 'All':

    filtered_df = filtered_df[
        filtered_df['district_name']
        == selected_district
    ]

if selected_risk != 'All':

    filtered_df = filtered_df[
        filtered_df['calculated_risk']
        == selected_risk
    ]

# =====================================================
# NO DATA
# =====================================================

if len(filtered_df) == 0:

    st.warning(
        'No cases found for selected filters.'
    )

# =====================================================
# MAIN LOGIC
# =====================================================

else:

    # =================================================
    # DISTRICT SUMMARY
    # =================================================

    st.subheader('📊 District Summary')

    avg_delay = round(
        filtered_df['case_age_days'].mean()
    )

    # Replace zero gaps with median
    valid_gaps = filtered_df[
        filtered_df['hearing_gap_days'] > 0
    ]

    if len(valid_gaps) > 0:

        avg_gap = round(
            valid_gaps['hearing_gap_days'].mean()
        )

    else:

        avg_gap = 30

    total_cases = len(filtered_df)

    high_risk_cases = len(

        filtered_df[
            filtered_df['calculated_risk']
            == 'High'
        ]

    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            'Total Cases',
            total_cases
        )

    with col2:

        st.metric(
            'Average Delay',
            f'{avg_delay} Days'
        )

    with col3:

        st.metric(
            'Average Hearing Gap',
            f'{avg_gap} Days'
        )

    with col4:

        st.metric(
            'High Risk Cases',
            high_risk_cases
        )

    # =================================================
    # DISTRICT LEVEL RECOMMENDATIONS
    # =================================================

    st.subheader('🚨 District-Level Recommendations')

    recommendations = []

    # =================================================
    # DELAY ANALYSIS
    # =================================================

    if avg_delay > 1200:

        recommendations.append(
            f"""
            🔴 Critical:
            Extremely severe pendency detected in
            {selected_district if selected_district != 'All' else 'selected districts'}.

            Recommendation:
            Conduct special disposal drives and
            create temporary fast-track benches.
            """
        )

    elif avg_delay > 700:

        recommendations.append(
            """
            🟠 High:
            Long-pending case concentration is high.

            Recommendation:
            Prioritize continuous hearing schedules
            for old pending cases.
            """
        )

    elif avg_delay > 400:

        recommendations.append(
            """
            🟡 Medium:
            Moderate judicial delay detected.

            Recommendation:
            Increase monitoring frequency and
            optimize case scheduling.
            """
        )

    # =================================================
    # HEARING GAP ANALYSIS
    # =================================================

    if avg_gap > 120:

        recommendations.append(
            """
            🔴 Critical:
            Excessive hearing gaps detected.

            Recommendation:
            Reduce adjournments and increase
            hearing frequency immediately.
            """
        )

    elif avg_gap > 60:

        recommendations.append(
            """
            🟠 High:
            Hearing intervals are unusually high.

            Recommendation:
            Optimize hearing calendar allocation.
            """
        )

    # =================================================
    # HEARING STAGE ANALYSIS
    # =================================================

    hearing_cases = len(

        filtered_df[
            filtered_df['stage_of_case']
            .str.lower() == 'hearing'
        ]

    )

    if hearing_cases > total_cases * 0.30:

        recommendations.append(
            f"""
            🟠 High:
            Hearing-stage backlog detected.

            Recommendation:
            Allocate additional hearing benches.

            Cases in Hearing Stage:
            {hearing_cases}
            """
        )

    # =================================================
    # EVIDENCE STAGE ANALYSIS
    # =================================================

    evidence_cases = len(

        filtered_df[
            filtered_df['stage_of_case']
            .str.lower() == 'evidence'
        ]

    )

    if evidence_cases > total_cases * 0.20:

        recommendations.append(
            f"""
            🟡 Medium:
            Evidence-stage delays are increasing.

            Recommendation:
            Accelerate evidence recording and
            witness coordination.

            Evidence Cases:
            {evidence_cases}
            """
        )

    # =================================================
    # SUMMONS DELAYS
    # =================================================

    summons_cases = len(

        filtered_df[
            filtered_df['stage_of_case']
            .str.lower()
            .str.contains('summons')
        ]

    )

    if summons_cases > total_cases * 0.15:

        recommendations.append(
            f"""
            🟡 Medium:
            Summons-related procedural delays detected.

            Recommendation:
            Improve summons execution monitoring.

            Summons Cases:
            {summons_cases}
            """
        )

    # =================================================
    # HIGH RISK CONCENTRATION
    # =================================================

    if high_risk_cases > total_cases * 0.30:

        recommendations.append(
            f"""
            🔴 Critical:
            High concentration of high-risk cases detected.

            Recommendation:
            Weekly monitoring and administrative review
            required for high-risk cases.

            High-Risk Cases:
            {high_risk_cases}
            """
        )

    # =================================================
    # DISPLAY DISTRICT RECOMMENDATIONS
    # =================================================

    if len(recommendations) == 0:

        st.success(
            'No major judicial risk indicators detected.'
        )

    else:

        for rec in recommendations:

            st.warning(rec)

    # =================================================
    # CASE SPECIFIC RECOMMENDATIONS
    # =================================================

    st.subheader('⚠ Case-Specific Recommendations')

    top_cases = filtered_df.sort_values(

        by='priority_score',

        ascending=False

    ).head(10)

    for index, row in top_cases.iterrows():

        case_recommendations = []

        # =================================================
        # AGE ANALYSIS
        # =================================================

        if row['case_age_days'] > 1500:

            case_recommendations.append(
                'Create special disposal bench'
            )

        elif row['case_age_days'] > 900:

            case_recommendations.append(
                'Schedule continuous hearings'
            )

        elif row['case_age_days'] > 500:

            case_recommendations.append(
                'Monitor under long-pending category'
            )

        # =================================================
        # HEARING GAP ANALYSIS
        # =================================================

        if row['hearing_gap_days'] > 180:

            case_recommendations.append(
                'Reduce excessive adjournments'
            )

        elif row['hearing_gap_days'] > 90:

            case_recommendations.append(
                'Increase hearing frequency'
            )

        elif row['hearing_gap_days'] > 45:

            case_recommendations.append(
                'Optimize hearing scheduling'
            )

        # =================================================
        # STAGE ANALYSIS
        # =================================================

        stage = str(
            row['stage_of_case']
        ).lower()

        if stage == 'hearing':

            case_recommendations.append(
                'Prioritize hearing-stage clearance'
            )

        elif stage == 'evidence':

            case_recommendations.append(
                'Accelerate evidence recording'
            )

        elif stage == 'argument':

            case_recommendations.append(
                'Proceed to final arguments quickly'
            )

        elif 'summons' in stage:

            case_recommendations.append(
                'Investigate summons execution delays'
            )

        elif stage == 'steps':

            case_recommendations.append(
                'Improve procedural compliance tracking'
            )

        # =================================================
        # RISK ANALYSIS
        # =================================================

        if row['calculated_risk'] == 'High':

            case_recommendations.append(
                'Weekly judicial monitoring required'
            )

        elif row['calculated_risk'] == 'Medium':

            case_recommendations.append(
                'Periodic review recommended'
            )

        # =================================================
        # REMOVE DUPLICATES
        # =================================================

        case_recommendations = list(
            set(case_recommendations)
        )

        # =================================================
        # DISPLAY CASE RECOMMENDATION
        # =================================================

        st.info(

            f"""
            District:
            {row['district_name']}

            Court:
            {row['court_name']}

            Stage:
            {row['stage_of_case']}

            Delay:
            {round(row['case_age_days'])} days

            Hearing Gap:
            {round(row['hearing_gap_days'])} days

            Risk:
            {row['calculated_risk']}

            Recommendation:
            {' | '.join(case_recommendations)}
            """

        )
