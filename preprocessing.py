import pandas as pd

def preprocess_data(file_path):

    # ============================================
    # LOAD FILE
    # ============================================

    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    # ============================================
    # COLUMN CLEANING
    # ============================================

    df.columns = [
        col.strip().lower()
        for col in df.columns
    ]

    # ============================================
    # REQUIRED COLUMNS
    # ============================================

    required_columns = [

        'district_name',
        'court_name',
        'stage_of_case',
        'case_age_days',
        'hearing_gap_days'

    ]

    for col in required_columns:

        if col not in df.columns:
            df[col] = 'Unknown'

    # ============================================
    # NUMERIC CONVERSION
    # ============================================

    df['case_age_days'] = pd.to_numeric(
        df['case_age_days'],
        errors='coerce'
    ).fillna(0)

df['hearing_gap_days'] = pd.to_numeric(
    df['hearing_gap_days'],
    errors='coerce'
).fillna(0)

# ============================================
# STAGE STANDARDIZATION
# ============================================

df['stage_of_case'] = (
    df['stage_of_case']
    .astype(str)
    .str.strip()
    .str.upper()
)

df['stage_of_case'] = df['stage_of_case'].replace({

    'EVIDENCES': 'EVIDENCE',
    'ARGUMENTS': 'ARGUMENT',
    'HEARINGS': 'HEARING',
    'RE-ISSUE SUMMONS': 'SUMMONS',
    'REISSUE SUMMONS': 'SUMMONS'

})

# ============================================
# RISK CALCULATION
# ============================================

def calculate_risk(age):

        if age > 1200:
            return 'High'

        elif age > 600:
            return 'Medium'

        else:
            return 'Low'

    df['calculated_risk'] = df[
        'case_age_days'
    ].apply(calculate_risk)

    # ============================================
    # PRIORITY SCORE
    # ============================================

    df['priority_score'] = (

        df['case_age_days'] * 0.6 +

        df['hearing_gap_days'] * 0.4

    )

    # ============================================
    # LONG PENDING
    # ============================================

    df['long_pending'] = (
        df['case_age_days'] > 365
    )

    # ============================================
    # DELAY EXPLANATION
    # ============================================

    def get_delay_explanation(row):

        if row['case_age_days'] > 1200:

            return 'Very old pending case'

        elif row['hearing_gap_days'] > 60:

            return 'Large hearing gap'

        elif str(row['stage_of_case']).upper() == 'EVIDENCE':

            return 'Delay in evidence stage'

        elif str(row['stage_of_case']).upper() == 'ARGUMENTS':

            return 'Pending arguments stage'

        else:

            return 'Routine case progression'

    df['delay_explanation'] = df.apply(
        get_delay_explanation,
        axis=1
    )

    return df
