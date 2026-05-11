import streamlit as st
import pandas as pd
import re
from datetime import datetime
from preprocessing import preprocess_data

# OCR IMPORTS
import pytesseract
from pdf2image import convert_from_bytes

# =====================================================
# TESSERACT PATH
# =====================================================

pytesseract.pytesseract.tesseract_cmd = (
    r'C:\Program Files\Tesseract-OCR\tesseract.exe'
)

# =====================================================
# POPPLER PATH
# =====================================================

POPPLER_PATH = (
    r'C:\poppler\poppler-24.08.0\Library\bin'
)

# =====================================================
# LOAD DATA
# =====================================================

df = preprocess_data('cleaned_cases.csv')

# =====================================================
# PAGE TITLE
# =====================================================

st.title('📥 Dynamic Case Input & OCR Extraction')

st.markdown(
    '### Upload eCourts PDFs or Manually Add Cases'
)

# =====================================================
# INPUT METHOD
# =====================================================

input_method = st.radio(

    'Choose Input Method',

    ['Manual Entry', 'PDF Upload']

)

# =====================================================
# MANUAL ENTRY
# =====================================================

if input_method == 'Manual Entry':

    st.subheader('✍ Manual Case Entry')

    district = st.selectbox(

        'District',

        sorted(df['district_name'].unique())

    )

    court_name = st.text_input(
        'Court Name'
    )

    stage = st.selectbox(

        'Stage of Case',

        sorted(df['stage_of_case'].unique())

    )

    case_status = st.selectbox(

        'Case Status',

        ['Pending', 'Disposed']

    )

    case_age = st.number_input(

        'Case Age (Days)',

        min_value=0,

        value=100

    )

    hearing_gap = st.number_input(

        'Hearing Gap (Days)',

        min_value=0,

        value=30

    )

    # =================================================
    # ADD MANUAL CASE
    # =================================================

    if st.button('Add Case'):

        # Risk
        if case_age > 1200:

            risk = 'High'

        elif case_age > 600:

            risk = 'Medium'

        else:

            risk = 'Low'

        # Priority
        priority_score = (

            case_age * 0.6 +

            hearing_gap * 0.4

        )

        # Explanation
        explanations = []

        if case_age > 900:

            explanations.append(
                'Extremely long pending case'
            )

        elif case_age > 500:

            explanations.append(
                'Long pending case'
            )

        if hearing_gap > 120:

            explanations.append(
                'Excessive hearing gaps'
            )

        elif hearing_gap > 60:

            explanations.append(
                'Large hearing intervals'
            )

        delay_explanation = (
            ', '.join(explanations)
        )

        # Recommendations
        recommendations = []

        if case_age > 1200:

            recommendations.append(
                'Create special disposal bench'
            )

        elif case_age > 700:

            recommendations.append(
                'Schedule continuous hearings'
            )

        elif case_age > 500:

            recommendations.append(
                'Monitor under long-pending category'
            )

        if hearing_gap > 120:

            recommendations.append(
                'Reduce excessive adjournments'
            )

        elif hearing_gap > 60:

            recommendations.append(
                'Increase hearing frequency'
            )

        if stage.lower() == 'evidence':

            recommendations.append(
                'Accelerate evidence recording'
            )

        elif stage.lower() == 'hearing':

            recommendations.append(
                'Prioritize hearing-stage clearance'
            )

        elif 'summons' in stage.lower():

            recommendations.append(
                'Investigate summons execution delays'
            )

        recommendation_text = (

            ' | '.join(set(recommendations))

        )

        # Create row
        new_case = pd.DataFrame({

            'district_name': [district],

            'court_name': [court_name],

            'stage_of_case': [stage],

            'case_age_days': [case_age],

            'hearing_gap_days': [hearing_gap],

            'calculated_risk': [risk],

            'priority_score': [priority_score],

            'delay_explanation': [delay_explanation],

            'recommendation': [recommendation_text],

            'case_status': [case_status]

        })

        # =================================================
        # RELOAD LATEST CSV
        # =================================================

        latest_df = preprocess_data(
            'cleaned_cases.csv'
        )

        updated_df = pd.concat(

            [latest_df, new_case],

            ignore_index=True

        )

        updated_df.to_csv(

            'cleaned_cases.csv',

            index=False

        )

        st.success(
            'Case added successfully.'
        )

# =====================================================
# PDF UPLOAD
# =====================================================

elif input_method == 'PDF Upload':

    st.subheader('📄 Upload eCourts PDF')

    uploaded_pdf = st.file_uploader(

        'Upload PDF',

        type='pdf'

    )

    if uploaded_pdf:

        text = ''

        # =================================================
        # OCR EXTRACTION
        # =================================================

        try:

            images = convert_from_bytes(

                uploaded_pdf.read(),

                poppler_path=POPPLER_PATH

            )

            for img in images:

                extracted = pytesseract.image_to_string(img)

                text += extracted + '\n'

        except Exception as e:

            st.error(f'OCR Error: {e}')

        # =================================================
        # SHOW OCR TEXT
        # =================================================

        st.subheader('📑 Extracted OCR Text')

        st.text_area(

            'OCR Output',

            text,

            height=300

        )

        # =================================================
        # DISTRICT DETECTION
        # =================================================

        district = 'Unknown'

        district_map = {

            'mysuru': 'Mysuru',

            'bengaluru': 'Bengaluru Urban',

            'tumakuru': 'Tumakuru',

            'belagavi': 'Belagavi',

            'kalaburagi': 'Kalaburagi'

        }

        for key, value in district_map.items():

            if key in text.lower():

                district = value

        # =================================================
        # COURT NAME
        # =================================================

        court_name = ''

        court_patterns = [

            r'PRL.*?NANJANGUD',

            r'COURT.*?MYSURU',

            r'JUDGE.*?MYSURU'

        ]

        for pattern in court_patterns:

            match = re.search(

                pattern,

                text,

                re.IGNORECASE

            )

            if match:

                court_name = match.group(0)

                break

        # =================================================
        # STAGE DETECTION
        # =================================================

        stage = 'Unknown'

        stage_keywords = [

            'EVIDENCE',

            'HEARING',

            'ARGUMENT',

            'JUDGMENT',

            'SUMMONS',

            'RE ISSUE SUMMONS',

            'STEPS',

            'NBW'

        ]

        for keyword in stage_keywords:

            if keyword.lower() in text.lower():

                stage = keyword.title()

                break

        # =================================================
        # CASE STATUS
        # =================================================

        case_status = 'Pending'

        if 'disposed' in text.lower():

            case_status = 'Disposed'

        # =================================================
        # REGISTRATION NUMBER
        # =================================================

        registration_number = ''

        reg_patterns = [

            r'\d{1,6}/\d{4}',

            r'C\.C\.\s*No\.\s*\d+/\d+'

        ]

        for pattern in reg_patterns:

            match = re.search(pattern, text)

            if match:

                registration_number = match.group(0)

                break

        # =================================================
        # FILING DATE
        # =================================================

        filing_date = ''

        filing_match = re.search(

            r'\d{2}-\d{2}-\d{4}',

            text

        )

        if filing_match:

            filing_date = filing_match.group(0)

        # =================================================
        # CASE AGE
        # =================================================

        case_age = 0

        try:

            if filing_date:

                filing_dt = datetime.strptime(

                    filing_date,

                    '%d-%m-%Y'

                )

                case_age = (

                    datetime.today() - filing_dt

                ).days

        except:
            pass

        # =================================================
        # HEARING GAP
        # =================================================

        hearing_gap = 30

        all_dates = re.findall(

            r'\d{2}-\d{2}-\d{4}',

            text

        )

        try:

            if len(all_dates) >= 2:

                d1 = datetime.strptime(

                    all_dates[-2],

                    '%d-%m-%Y'

                )

                d2 = datetime.strptime(

                    all_dates[-1],

                    '%d-%m-%Y'

                )

                hearing_gap = abs(
                    (d2 - d1).days
                )

        except:
            pass

        # =================================================
        # VERIFY DATA
        # =================================================

        st.subheader('✅ Verify Extracted Information')

        district = st.text_input(
            'District',
            value=district
        )

        court_name = st.text_input(
            'Court Name',
            value=court_name
        )

        registration_number = st.text_input(
            'Registration Number',
            value=registration_number
        )

        stage = st.text_input(
            'Stage of Case',
            value=stage
        )

        case_status = st.text_input(
            'Case Status',
            value=case_status
        )

        filing_date = st.text_input(
            'Filing Date',
            value=filing_date
        )

        case_age = st.number_input(
            'Case Age (Days)',
            value=int(case_age)
        )

        hearing_gap = st.number_input(
            'Hearing Gap (Days)',
            value=int(hearing_gap)
        )

        # =================================================
        # ADD EXTRACTED CASE
        # =================================================

        if st.button('Add Extracted Case'):

            # Risk
            if case_age > 1200:

                risk = 'High'

            elif case_age > 600:

                risk = 'Medium'

            else:

                risk = 'Low'

            # Priority
            priority_score = (

                case_age * 0.6 +

                hearing_gap * 0.4

            )

            # Explanation
            explanations = []

            if case_age > 900:

                explanations.append(
                    'Extremely long pending case'
                )

            elif case_age > 500:

                explanations.append(
                    'Long pending case'
                )

            if hearing_gap > 120:

                explanations.append(
                    'Excessive hearing gaps'
                )

            elif hearing_gap > 60:

                explanations.append(
                    'Large hearing intervals'
                )

            delay_explanation = (
                ', '.join(explanations)
            )

            # Recommendations
            recommendations = []

            if case_age > 1200:

                recommendations.append(
                    'Create special disposal bench'
                )

            elif case_age > 700:

                recommendations.append(
                    'Schedule continuous hearings'
                )

            elif case_age > 500:

                recommendations.append(
                    'Monitor under long-pending category'
                )

            if hearing_gap > 120:

                recommendations.append(
                    'Reduce excessive adjournments'
                )

            elif hearing_gap > 60:

                recommendations.append(
                    'Increase hearing frequency'
                )

            if stage.lower() == 'evidence':

                recommendations.append(
                    'Accelerate evidence recording'
                )

            elif stage.lower() == 'hearing':

                recommendations.append(
                    'Prioritize hearing-stage clearance'
                )

            elif 'summons' in stage.lower():

                recommendations.append(
                    'Investigate summons execution delays'
                )

            recommendation_text = (

                ' | '.join(set(recommendations))

            )

            # Create row
            new_case = pd.DataFrame({

                'district_name': [district],

                'court_name': [court_name],

                'stage_of_case': [stage],

                'case_age_days': [case_age],

                'hearing_gap_days': [hearing_gap],

                'calculated_risk': [risk],

                'priority_score': [priority_score],

                'delay_explanation': [delay_explanation],

                'recommendation': [recommendation_text],

                'case_status': [case_status]

            })

            # =================================================
            # RELOAD LATEST CSV
            # =================================================

            latest_df = preprocess_data(
                'cleaned_cases.csv'
            )

            updated_df = pd.concat(

                [latest_df, new_case],

                ignore_index=True

            )

            updated_df.to_csv(

                'cleaned_cases.csv',

                index=False

            )

            st.success(
                'PDF case extracted successfully.'
            )

            st.info(
                f'Recommendation: {recommendation_text}'
            )

# =====================================================
# DELETE CASES
# =====================================================

st.subheader('🗑 Delete Cases')

delete_stage = st.selectbox(

    'Delete Cases By Stage',

    sorted(df['stage_of_case'].unique())

)

if st.button('Delete Cases'):

    latest_df = preprocess_data(
        'cleaned_cases.csv'
    )

    updated_df = latest_df[
        latest_df['stage_of_case'] != delete_stage
    ]

    updated_df.to_csv(
        'cleaned_cases.csv',
        index=False
    )

    st.success(
        'Cases deleted successfully.'
    )