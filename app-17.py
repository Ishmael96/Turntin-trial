from flask import Flask, render_template, request, jsonify
import re
import math
from collections import Counter
import json

app = Flask(__name__)

# ── AI Detection Logic ──────────────────────────────────────────────────────
AI_INDICATORS = [
    "furthermore", "moreover", "in conclusion", "it is worth noting",
    "it should be noted", "in summary", "to summarize", "in addition",
    "as a result", "consequently", "therefore", "thus", "hence",
    "this highlights", "this demonstrates", "this suggests",
    "plays a crucial role", "plays an important role", "is essential",
    "is significant", "delve", "delves", "tapestry", "nuanced",
    "multifaceted", "comprehensive", "robust", "leverage", "utilize",
    "facilitate", "endeavor", "underscore", "paramount", "pivotal",
    "it's important to note", "importantly", "notably"
]

def analyze_text(text):
    if not text or len(text.strip()) < 50:
        return None

    words = text.lower().split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    # ── AI Score ──
    word_count = len(words)
    ai_word_hits = sum(1 for w in words if w.strip('.,;:') in AI_INDICATORS)
    phrase_hits = sum(1 for phrase in AI_INDICATORS if phrase in text.lower() and ' ' in phrase)
    
    # Sentence length consistency (AI tends to be uniform)
    if sentences:
        lengths = [len(s.split()) for s in sentences]
        avg_len = sum(lengths) / len(lengths)
        variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
        std_dev = math.sqrt(variance)
        uniformity_score = max(0, 40 - std_dev * 2)  # Lower variance = more AI-like
    else:
        uniformity_score = 0

    # Passive voice detection
    passive_patterns = re.findall(r'\b(is|are|was|were|be|been|being)\s+\w+ed\b', text.lower())
    passive_score = min(20, len(passive_patterns) * 3)

    # Combine
    ai_raw = (ai_word_hits / max(word_count, 1)) * 400 + phrase_hits * 8 + uniformity_score + passive_score
    ai_score = min(98, max(2, ai_raw))

    # ── Plagiarism Simulation ──
    # Check for very common phrases
    common_phrases = [
        "climate change", "global warming", "machine learning", "artificial intelligence",
        "the united states", "in recent years", "according to", "research shows",
        "studies have shown", "experts say", "it has been", "there are many"
    ]
    phrase_density = sum(1 for p in common_phrases if p in text.lower())
    
    # Repetition within text
    word_freq = Counter(words)
    repeated = sum(1 for w, c in word_freq.items() if len(w) > 5 and c > 3)
    
    plag_raw = phrase_density * 4 + repeated * 2
    plag_score = min(85, max(1, plag_raw))

    # ── Readability (Flesch-Kincaid approx) ──
    syllable_count = sum(count_syllables(w) for w in words)
    avg_syllables = syllable_count / max(word_count, 1)
    avg_sent_len = word_count / max(len(sentences), 1)
    flesch = 206.835 - 1.015 * avg_sent_len - 84.6 * avg_syllables
    flesch = max(0, min(100, flesch))

    # Grade level
    if flesch >= 90: grade = "5th grade"
    elif flesch >= 70: grade = "7th grade"
    elif flesch >= 60: grade = "8th-9th grade"
    elif flesch >= 50: grade = "10th-12th grade"
    elif flesch >= 30: grade = "College"
    else: grade = "College graduate"

    # Flagged phrases
    flagged = []
    for phrase in AI_INDICATORS:
        if ' ' in phrase and phrase in text.lower():
            flagged.append(phrase)
    for phrase in AI_INDICATORS:
        if ' ' not in phrase:
            for w in words:
                if w.strip('.,;:') == phrase and phrase not in [f for f in flagged]:
                    flagged.append(phrase)
                    break

    return {
        "ai_score": round(ai_score),
        "plag_score": round(plag_score),
        "word_count": word_count,
        "sentence_count": len(sentences),
        "readability": round(flesch),
        "grade_level": grade,
        "flagged_phrases": list(set(flagged))[:12],
        "ai_label": get_label(ai_score, "ai"),
        "plag_label": get_label(plag_score, "plag"),
    }

def get_label(score, mode):
    if mode == "ai":
        if score < 20: return ("Human Written", "green")
        if score < 45: return ("Likely Human", "lime")
        if score < 65: return ("Mixed / Uncertain", "amber")
        if score < 80: return ("Likely AI", "orange")
        return ("AI Generated", "red")
    else:
        if score < 10: return ("No Plagiarism", "green")
        if score < 25: return ("Low Similarity", "lime")
        if score < 50: return ("Moderate Similarity", "amber")
        if score < 70: return ("High Similarity", "orange")
        return ("Plagiarised", "red")

def count_syllables(word):
    word = word.lower().strip(".,;:!?\"'")
    if len(word) <= 3: return 1
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith('e'): count -= 1
    return max(1, count)

# ── Routes ─────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    text = data.get('text', '')
    result = analyze_text(text)
    if not result:
        return jsonify({"error": "Please enter at least 50 characters of text."}), 400
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
