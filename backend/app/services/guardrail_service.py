"""
Guardrail service for Smart Grid Energy Intelligence Assistant.
Validates input queries to ensure domain relevance, reject out-of-scope questions,
prevent prompt injections, and guide users toward valid energy analytics workflows.
"""

import re
import unicodedata
from typing import Tuple, List, Optional


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if not (unicodedata.category(c) == "Mn" and 0x0300 <= ord(c) <= 0x036F)
    )


# Restricted/security patterns
SECURITY_PATTERNS = [
    r"api[_\s-]?key",
    r"system[_\s-]?prompt",
    r"system[_\s-]?instructions?",
    r"execute\s+(?:arbitrary\s+)?(?:python|code|bash|sh|cmd)",
    r"run\s+python",
    r"delete\s+all",
    r"drop\s+(?:database|table|collection)",
    r"direct\s+access\s+to\s+the\s+database",
    r"query\s+mongodb\s+directly",
    r"ignore\s+(?:all\s+)?previous\s+instructions?",
    r"disregard\s+(?:all\s+)?prior",
    r"reveal\s+(?:all\s+)?credentials?",
    r"leak\s+(?:the\s+)?secret",
]

# Explicitly off-topic topic keywords and domains
OFF_TOPIC_PATTERNS = [
    # General trivia / geography / capitals
    r"\bcapital\s+of\b",
    r"\bwho\s+is\s+(?:the\s+)?(?:president|prime\s+minister|king|queen|governor|actor|actress|singer)\b",
    r"\bwho\s+was\s+(?:napoleon|einstein|newton|shakespeare|caesar|hitler|lincoln)\b",
    r"\bwho\s+won\s+(?:the\s+)?(?:world\s+cup|super\s+bowl|oscars?|champions\s+league|election|game)\b",
    r"\bpopulation\s+of\b",
    r"\bmount\s+everest\b",
    r"\bcontinents?\s+(?:in|on)\s+earth\b",

    # Cooking / Food
    r"\b(?:recipe|cook|bake|baking|cake|pizza|cookie|chocolate|ingredients?|delicious|pasta|burger)\b",

    # Creative writing / jokes / entertainment
    r"\b(?:write\s+(?:a\s+)?poem|tell\s+(?:me\s+)?(?:a\s+)?joke|write\s+(?:a\s+)?story|lyrics|movie\s+recommendation)\b",

    # Coding / programming non-energy
    r"\b(?:write\s+(?:a\s+)?(?:python|java|c\+\+|javascript|rust|golang|sql)\s+(?:script|code|program|function))\b",
    r"\b(?:bubble\s+sort|quick\s+sort|binary\s+tree|linked\s+list|leetcode|fibonacci)\b",

    # Sports
    r"\b(?:football|soccer|basketball|cricket|tennis|nba|nfl|fifa|messi|ronaldo)\b",

    # Medical / Health
    r"\b(?:symptoms?\s+of|cure\s+for|diagnose|headache|medicine|fever|pill)\b",
]

# Domain relevance keywords across multiple languages (English, Spanish, French, German, Chinese, Hindi)
ENERGY_DOMAIN_TERMS = {
    # English
    "energy", "electricity", "power", "demand", "consumption", "kw", "kwh", "watt",
    "voltage", "current", "submetering", "meter", "grid", "peak", "off-peak", "spike",
    "load", "anomaly", "anomalies", "unusual", "pattern", "forecast", "prediction",
    "hourly", "daily", "weekly", "monthly", "weekend", "weekday", "evening", "morning",
    "reading", "readings", "historical", "baseline", "variance", "deviation", "insight",
    "insights", "operational", "efficiency", "generation", "baseload", "storage",

    # Spanish
    "energia", "electricidad", "potencia", "demanda", "consumo", "voltaje", "corriente",
    "medidor", "red", "pico", "maxima", "anomalia", "anomalias", "inusual", "patron",
    "pronostico", "horario", "diario", "semanal", "mensual", "fin de semana", "laboral",
    "tarde", "aumento",

    # French
    "energie", "electricite", "puissance", "consommation", "tension", "reseau",
    "pointe", "creme", "anomalie", "inhabituel", "prevision", "prochain", "semaine",
    "soir", "hausse",

    # German
    "strom", "stromverbrauch", "spitzenbedarf", "spitze", "leistung", "verbrauch",
    "spannung", "netz", "anomalie", "ungewohnlich", "prognose", "vorhersage",
    "stunde", "werktag", "wochenende", "abend", "anstieg",

    # Chinese
    "用电", "电力", "用电量", "能耗", "能源", "需求", "负荷", "峰值", "最高",
    "异常", "预测", "时段", "工作日", "周末", "晚间", "傍晚", "历史", "电网",

    # Hindi
    "ऊर्जा", "बिजली", "मांग", "खपत", "चरम", "असामान्य", "पूर्वानुमान",
    "घंटे", "सप्ताहांत", "शाम", "बढ़ोतरी", "ग्रिड",
}

GREETING_PATTERNS = [
    r"^(?:hi|hello|hey|good\s+morning|good\s+afternoon|good\s+evening|greetings|howdy)(?:\s+there)?[\s!.]*$",
    r"^(?:hola|buenos\s+dias|buenas\s+tardes|buenas\s+noches)[\s!.]*$",
    r"^(?:bonjour|bon\s+apres-midi|bonsoir|salut)[\s!.]*$",
    r"^(?:hallo|guten\s+morgen|guten\s+tag|guten\s+abend)[\s!.]*$",
    r"^(?:你好|早上好|下午好|晚上好|您好)[\s!.]*$",
    r"^(?:नमस्ते|नमस्कार|सुप्रभात|शुभ\s+दोपहर|शुभ\s+संध्या)[\s!.]*$",
]

LOCALIZED_SUGGESTIONS = {
    "en": [
        "What was the electricity demand during the peak hours?",
        "Which periods show unusual energy consumption?",
        "What is the expected demand for the next 6 hours?",
        "Compare weekday and weekend consumption patterns."
    ],
    "es": [
        "¿Cuál fue la demanda de electricidad durante las horas pico?",
        "¿Qué períodos muestran un consumo de energía inusual?",
        "¿Cuál es la demanda prevista para las próximas 6 horas?",
        "Compara el consumo entre días laborales y fines de semana."
    ],
    "fr": [
        "Quelle était la demande d'électricité pendant les heures de pointe?",
        "Quelles périodes affichent une consommation d'énergie inhabituelle?",
        "Quelle est la demande prévue pour les 6 prochaines heures?",
        "Comparez la consommation en semaine et le week-end."
    ],
    "de": [
        "Was war der Stromverbrauch während der Spitzenzeiten?",
        "Welche Zeiträume weisen einen ungewöhnlichen Energieverbrauch auf?",
        "Wie hoch ist der prognostizierte Bedarf für die nächsten 6 Stunden?",
        "Vergleichen Sie den Verbrauch an Werktagen und Wochenenden."
    ],
    "zh": [
        "高峰时段的用电需求是多少？",
        "哪些时段表现出异常的用电量？",
        "未来 6 小时的预期电力需求是多少？",
        "对比工作日与周末的用电模式。"
    ],
    "hi": [
        "पीक आवर्स के दौरान बिजली की मांग क्या थी?",
        "कौन सी अवधियां असामान्य ऊर्जा खपत दिखाती हैं?",
        "अगले 6 घंटों के लिए अनुमानित मांग क्या है?",
        "सप्ताह के दिनों और सप्ताहांत की खपत पैटर्न की तुलना करें।"
    ]
}

LOCALIZED_WARNINGS = {
    "en": (
        "⚠️ Notice: Off-Topic Query Detected.\n\n"
        "I am the AI-Powered Smart Grid Energy Intelligence Assistant, designed strictly to analyze "
        "smart grid electricity consumption, demand forecasting, anomaly detection, and operational grid patterns.\n\n"
        "Your question appears unrelated to smart grid energy data. Please select or ask a question regarding energy metrics, peak loads, or forecasts."
    ),
    "es": (
        "⚠️ Aviso: Consulta fuera de tema detectada.\n\n"
        "Soy el Asistente de Inteligencia Energética de Smart Grid, diseñado específicamente para analizar "
        "el consumo de electricidad, pronósticos de demanda, detección de anomalías y patrones de red.\n\n"
        "Su consulta no está relacionada con la red eléctrica. Por favor, realice preguntas sobre demanda energética, horas pico o pronósticos."
    ),
    "fr": (
        "⚠️ Avis: Question hors sujet détectée.\n\n"
        "Je suis l'Assistant d'Intelligence Énergétique Smart Grid, conçu pour analyser "
        "la consommation d'électricité, les prévisions de charge, la détection d'anomalies et les profils de réseau.\n\n"
        "Votre question ne concerne pas les données énergétiques. Veuillez poser une question relative à la consommation ou aux prévisions."
    ),
    "de": (
        "⚠️ Hinweis: Themenfremde Abfrage erkannt.\n\n"
        "Ich bin der KI-Assistent für Smart-Grid-Energieintelligenz, spezialisiert auf die Analyse von "
        "Stromverbrauch, Spitzenlasten, Anomalieerkennung und Lastprognosen.\n\n"
        "Ihre Frage bezieht sich nicht auf Energiedaten. Bitte stellen Sie Fragen zu Strombedarf, Spitzenzeiten oder Prognosen."
    ),
    "zh": (
        "⚠️ 提示：检测到非智能电网相关问题。\n\n"
        "我是智能电网能源智能助手，专门用于分析电力消费、负荷预测、用电异常检测和电网运行模式。\n\n"
        "您的问题不在智能电网数据分析范围内。请提出与用电需求、峰值负荷或预测相关的问题。"
    ),
    "hi": (
        "⚠️ सूचना: विषय से बाहर का प्रश्न पहचाना गया।\n\n"
        "मैं एआई-संचालित स्मार्ट ग्रिड ऊर्जा सहायक हूँ, जो केवल बिजली की खपत, चरम मांग, विसंगति का पता लगाने और ग्रिड लोड पूर्वानुमान का विश्लेषण करता है।\n\n"
        "कृपया ऊर्जा डेटा, पीक लोड या पूर्वानुमान से संबंधित प्रश्न पूछें।"
    )
}

LOCALIZED_GREETINGS = {
    "en": (
        "👋 Hello! I am your Smart Grid Energy Intelligence Assistant.\n\n"
        "I can help you analyze electricity demand, detect consumption anomalies, forecast future loads, "
        "and extract actionable operational insights from your smart grid readings.\n\n"
        "Here are some questions you can ask me:"
    ),
    "es": (
        "👋 ¡Hola! Soy su Asistente de Inteligencia Energética para Redes Inteligentes.\n\n"
        "Puedo ayudarle a analizar la demanda de electricidad, detectar anomalías, pronosticar el consumo futuro "
        "y extraer información operativa clave de sus datos de red.\n\n"
        "Aquí tiene algunas preguntas que puede hacerme:"
    ),
    "fr": (
        "👋 Bonjour! Je suis votre Assistant d'Intelligence Énergétique Smart Grid.\n\n"
        "Je peux vous aider à analyser la demande d'électricité, détecter les anomalies, prévoir les charges futures "
        "et extraire des enseignements opérationnels.\n\n"
        "Voici quelques questions que vous pouvez poser:"
    ),
    "de": (
        "👋 Hallo! Ich bin Ihr Assistent für Smart-Grid-Energieintelligenz.\n\n"
        "Ich kann Ihnen helfen, den Strombedarf zu analysieren, Verbrauchsanomalien zu erkennen, künftige Lasten vorherzusagen "
        "und betriebliche Erkenntnisse zu gewinnen.\n\n"
        "Hier sind einige Beispielfragen:"
    ),
    "zh": (
        "👋 您好！我是您的智能电网能源智能助手。\n\n"
        "我可以帮助您分析用电需求、检测异常消费、预测未来负荷，并从智能电网读数中提取运行洞察。\n\n"
        "您可以尝试询问以下问题："
    ),
    "hi": (
        "👋 नमस्ते! मैं आपका स्मार्ट ग्रिड ऊर्जा सहायक हूँ।\n\n"
        "मैं बिजली की मांग का विश्लेषण करने, खपत विसंगतियों का पता लगाने और भविष्य के लोड का पूर्वानुमान लगाने में आपकी सहायता कर सकता हूँ।\n\n"
        "आप मुझसे ये प्रश्न पूछ सकते हैं:"
    )
}


def check_guardrails(question: str, language: str = "en") -> Tuple[bool, Optional[str], Optional[str], List[str]]:
    """
    Evaluates whether the user's query satisfies security and domain guardrails.

    Returns:
        (is_allowed, intent_override, response_text, suggested_queries)
        - is_allowed: True if query is relevant and safe, False if blocked by guardrails or off-topic.
        - intent_override: 'security_violation', 'greeting', 'out_of_scope', or None if relevant.
        - response_text: Explanatory warning/greeting message or None if query should proceed.
        - suggested_queries: Curated relevant suggestions to guide the user.
    """
    clean_q = strip_accents(question.strip().lower())
    suggestions = LOCALIZED_SUGGESTIONS.get(language, LOCALIZED_SUGGESTIONS["en"])

    # 1. Security / Prompt Injection Guardrail
    for pat in SECURITY_PATTERNS:
        if re.search(pat, clean_q, re.IGNORECASE):
            return False, "security_violation", (
                "⚠️ Security Policy Alert: This request violates assistant guardrails and cannot be executed."
            ), suggestions

    # 2. Greeting / Conversational Greeting Guardrail
    for pat in GREETING_PATTERNS:
        if re.search(pat, clean_q, re.IGNORECASE) or clean_q in {"hi", "hello", "hey", "hola", "bonjour", "hallo", "你好", "नमस्ते"}:
            greeting = LOCALIZED_GREETINGS.get(language, LOCALIZED_GREETINGS["en"])
            return False, "greeting", greeting, suggestions

    # 3. Explicit Off-Topic Detection (politics, trivia, cooking, programming, etc.)
    for pat in OFF_TOPIC_PATTERNS:
        if re.search(pat, clean_q, re.IGNORECASE):
            warning = LOCALIZED_WARNINGS.get(language, LOCALIZED_WARNINGS["en"])
            return False, "out_of_scope", warning, suggestions

    # 4. Domain Relevance Analysis
    # Tokenize words to check for energy domain alignment
    words = set(re.findall(r"\w+", clean_q))
    has_domain_term = any(term in clean_q for term in ENERGY_DOMAIN_TERMS) or bool(words.intersection(ENERGY_DOMAIN_TERMS))

    # Also check typical energy analytical question stems
    has_analytics_stem = any(stem in clean_q for stem in [
        "peak", "demand", "consumption", "forecast", "unusual", "anomal",
        "hourly", "weekday", "weekend", "evening", "kw", "kwh", "power", "grid",
        "demanda", "consumo", "pronost", "inusual", "pointe", "previs",
        "strom", "spitze", "prognose", "用电", "负荷", "峰值", "预测", "मांग", "खपत"
    ])

    if not (has_domain_term or has_analytics_stem):
        # Query does not contain any energy/grid domain concept
        warning = LOCALIZED_WARNINGS.get(language, LOCALIZED_WARNINGS["en"])
        return False, "out_of_scope", warning, suggestions

    # Query passed all guardrails and is relevant to the smart grid domain
    return True, None, None, []
