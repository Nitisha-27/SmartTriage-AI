
import re
import spacy

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# --------------------------------------------------
# 1. SPACY INITIALIZATION
# --------------------------------------------------

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = spacy.blank("en")


# --------------------------------------------------
# 2. SYNDROMIC ARCHETYPES
# --------------------------------------------------

SYNDROME_DESCRIPTIONS = {
    "Acute Coronary Syndrome": (
        "Chest pain pressure crushing sensation radiating to left arm "
        "jaw sweating nausea breathlessness palpitations"
    ),

    "Acute Respiratory Failure": (
        "Severe breathlessness respiratory distress low oxygen saturation "
        "rapid breathing cyanosis inability to breathe"
    ),

    "Systemic Sepsis": (
        "Fever infection chills elevated heart rate rapid breathing "
        "low blood pressure confusion weakness"
    ),

    "Acute Stroke": (
        "Facial droop arm weakness speech difficulty sudden numbness "
        "confusion loss of balance severe headache"
    ),

    "Acute Surgical Abdomen": (
        "Severe abdominal pain rigid abdomen vomiting tenderness "
        "abdominal distension gastrointestinal bleeding"
    )
}


# --------------------------------------------------
# 3. RED FLAG PHRASES
# --------------------------------------------------

RED_FLAG_PHRASES = {
    "radiating to left arm":
        "Possible cardiac warning symptom",

    "crushing chest":
        "Possible acute coronary syndrome warning symptom",

    "facial droop":
        "Possible stroke warning symptom",

    "arm weakness":
        "Possible focal neurological deficit",

    "confused":
        "Possible altered mental status",

    "vomiting blood":
        "Possible gastrointestinal bleeding",

    "stiff neck":
        "Possible meningeal irritation",

    "cannot breathe":
        "Possible severe respiratory distress",

    "unconscious":
        "Possible loss of consciousness",

    "severe headache":
        "Possible serious neurological warning symptom"
}


# --------------------------------------------------
# 4. NEGATION DETECTION
# --------------------------------------------------

NEGATION_WORDS = {
    "no", "not", "denies", "denied",
    "without", "never", "negative"
}



def is_negated(text, phrase):

    text = text.lower()

    matches = list(
        re.finditer(re.escape(phrase.lower()), text)
    )

    if not matches:
        return False

    for match in matches:

        preceding_text = text[:match.start()]

        # Restrict negation checking to the current clause
        preceding_text = re.split(
            r"[,;.!?]|\bbut\b|\bhowever\b",
            preceding_text
        )[-1]

        words = re.findall(
            r"\b\w+\b",
            preceding_text
        )

        if not any(
            word in NEGATION_WORDS
            for word in words[-5:]
        ):
            return False

    return True



# --------------------------------------------------
# 5. CLINICAL ENTITY EXTRACTION
# --------------------------------------------------

CLINICAL_TERMS = {
    "chest pain": "CHEST_PAIN",
    "crushing chest pain": "CHEST_PAIN",
    "shortness of breath": "BREATHLESSNESS",
    "breathlessness": "BREATHLESSNESS",
    "difficulty breathing": "BREATHLESSNESS",
    "left arm": "PAIN_LOCATION",
    "facial droop": "NEUROLOGICAL_DEFICIT",
    "arm weakness": "NEUROLOGICAL_DEFICIT",
    "speech difficulty": "SPEECH_DISTURBANCE",
    "abdominal pain": "ABDOMINAL_PAIN",
    "fever": "FEVER",
    "vomiting": "VOMITING",
    "hypertension": "MEDICAL_HISTORY",
    "diabetes": "MEDICAL_HISTORY",
    "aspirin": "MEDICATION",
}


def extract_clinical_entities(narrative):

    if not narrative or not narrative.strip():
        return [], {}

    text = narrative.lower()

    entities = {}

    for phrase, category in CLINICAL_TERMS.items():

        if phrase in text and not is_negated(text, phrase):
            entities[phrase] = category

    detected_red_flags = {}

    for phrase, reason in RED_FLAG_PHRASES.items():

        if phrase in text and not is_negated(text, phrase):
            detected_red_flags[phrase] = reason

    return entities, detected_red_flags


# --------------------------------------------------
# 6. MISSING CLINICAL INFORMATION
# --------------------------------------------------

MISSING_FIELD_PATTERNS = {

    "symptom_duration": [
        r"\b\d+\s*(minutes?|hours?|days?|weeks?|months?)\b",
        r"\bsince\s+\w+",
        r"\bfor\s+\d+\s*(minutes?|hours?|days?|weeks?)\b"
    ],

    "pain_scale": [
        r"\b\d+\s*/\s*10\b",
        r"\b\d+\s*out of\s*10\b",
        r"\bpain\s*(?:score|level)\s*(?:is|of)?\s*\d+\b"
    ],

    "prior_history": [
        r"\bmedical history\b",
        r"\bpast history\b",
        r"\bpreviously diagnosed\b",
        r"\bknown history\b"
    ],

    "allergies": [
        r"\ballerg(?:y|ies)\b"
    ],

    "current_medications": [
        r"\bmedications?\b",
        r"\bmedicines?\b",
        r"\btaking\s+\w+"
    ],

    "onset_type": [
        r"\bsudden onset\b",
        r"\bgradual onset\b",
        r"\bstarted suddenly\b",
        r"\bstarted gradually\b"
    ]
}


def detect_missing_fields(narrative):

    text = narrative.lower()

    missing_fields = []

    for field, patterns in MISSING_FIELD_PATTERNS.items():

        found = any(
            re.search(pattern, text)
            for pattern in patterns
        )

        if not found:
            missing_fields.append(field)

    return missing_fields


# --------------------------------------------------
# 7. TF-IDF SYNDROME MATCHING
# --------------------------------------------------

def compute_syndrome_match(narrative):

    if not narrative or not narrative.strip():
        return None, 0.0

    syndrome_names = list(SYNDROME_DESCRIPTIONS.keys())

    syndrome_texts = [
        SYNDROME_DESCRIPTIONS[name]
        for name in syndrome_names
    ]

    all_texts = syndrome_texts + [narrative]

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words="english"
    )

    tfidf_matrix = vectorizer.fit_transform(all_texts)

    syndrome_vectors = tfidf_matrix[:-1]
    patient_vector = tfidf_matrix[-1]

    similarities = cosine_similarity(
        patient_vector,
        syndrome_vectors
    )[0]

    best_index = similarities.argmax()

    return (
        syndrome_names[best_index],
        round(float(similarities[best_index]), 4)
    )


# --------------------------------------------------
# 8. FIVE-PARAMETER NEWS2 COMPONENT SCORING
# --------------------------------------------------

def calculate_news2(hr, rr, sbp, spo2, temp):

    values = [hr, rr, sbp, spo2, temp]

    if any(value is None for value in values):
        raise ValueError(
            "All five vital signs are required for scoring."
        )

    if hr <= 0 or rr <= 0 or sbp <= 0:
        raise ValueError("Heart rate, respiratory rate and SBP must be positive.")

    if not 0 <= spo2 <= 100:
        raise ValueError("SpO2 must be between 0 and 100.")

    if not 25 <= temp <= 45:
        raise ValueError("Temperature must be between 25 and 45 Celsius.")

    # Respiratory rate
    if rr <= 8:
        rr_score = 3
    elif rr <= 11:
        rr_score = 1
    elif rr <= 20:
        rr_score = 0
    elif rr <= 24:
        rr_score = 2
    else:
        rr_score = 3

    # Oxygen saturation - Scale 1
    if spo2 <= 91:
        spo2_score = 3
    elif spo2 <= 93:
        spo2_score = 2
    elif spo2 <= 95:
        spo2_score = 1
    else:
        spo2_score = 0

    # Systolic blood pressure
    if sbp <= 90:
        sbp_score = 3
    elif sbp <= 100:
        sbp_score = 2
    elif sbp <= 110:
        sbp_score = 1
    elif sbp <= 219:
        sbp_score = 0
    else:
        sbp_score = 3

    # Heart rate
    if hr <= 40:
        hr_score = 3
    elif hr <= 50:
        hr_score = 1
    elif hr <= 90:
        hr_score = 0
    elif hr <= 110:
        hr_score = 1
    elif hr <= 130:
        hr_score = 2
    else:
        hr_score = 3

    # Temperature
    if temp <= 35.0:
        temp_score = 3
    elif temp <= 36.0:
        temp_score = 1
    elif temp <= 38.0:
        temp_score = 0
    elif temp <= 39.0:
        temp_score = 1
    else:
        temp_score = 2

    return (
        rr_score
        + spo2_score
        + sbp_score
        + hr_score
        + temp_score
    )


# --------------------------------------------------
# 9. SOAP NOTE GENERATION
# --------------------------------------------------

def build_soap(
    narrative,
    entities,
    red_flags,
    syndrome,
    similarity,
    news2,
    tier,
    vitals
):

    # SUBJECTIVE
    subjective = (
        f"Patient complaint: {narrative}\n"
        f"Extracted clinical entities: {', '.join(entities)}"
    )

    # OBJECTIVE
    objective = (
        f"Heart Rate: {vitals.get('heart_rate')} bpm\n"
        f"Respiratory Rate: {vitals.get('resp_rate')} /min\n"
        f"Systolic BP: {vitals.get('systolic_bp')} mmHg\n"
        f"SpO2: {vitals.get('spo2')}%\n"
        f"Temperature: {vitals.get('temperature')} C\n"
        f"Five-parameter NEWS2 component score: {news2}"
    )

    # ASSESSMENT
    assessment = (
        f"Prototype AI triage suggestion: {tier}\n"
        f"Closest syndrome archetype: {syndrome}\n"
        f"Syndrome similarity: {similarity}\n"
        f"Detected red flags: {red_flags}"
    )

    return {
        "subjective": subjective,
        "objective": objective,
        "assessment": assessment
    }
