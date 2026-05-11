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

    return df