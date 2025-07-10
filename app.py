from flask import Flask, render_template, request, jsonify
import json
import os
import difflib

app = Flask(__name__)

# Load knowledge base
KB_PATH = os.path.join(os.path.dirname(__file__), 'knowledge_base.json')
if os.path.exists(KB_PATH):
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        KNOWLEDGE_BASE = json.load(f)
else:
    KNOWLEDGE_BASE = []

# Conversation state (for demo, use session or db for production)
user_states = {}

# Utility: check positive/negative
POSITIVE = [
    "haan", "yes", "tell me more", "batao", "kya hai", "kya hai?", "ok", "sure", "ji", "haanji", "y", "h", "please", "go ahead", "continue", "chalo", "zarur", "bilkul", "proceed", "aage badho", "hmm", "haan na", "why not", "of course"
]
NEGATIVE = [
    "nahi", "no", "nahin", "n", "nope", "not interested", "leave", "stop", "don’t want", "donot want", "na", "never", "no thanks", "no thank you"
]
import string

def normalize_message(msg):
    # Remove punctuation and extra spaces, lowercase
    return msg.translate(str.maketrans('', '', string.punctuation)).strip().lower()

def is_positive(msg):
    norm = normalize_message(msg)
    # Phrase match
    if any(phrase in norm for phrase in POSITIVE if ' ' in phrase):
        return True
    # Word match
    words = norm.split()
    return any(word in POSITIVE for word in words)

def is_negative(msg):
    norm = normalize_message(msg)
    # Phrase match
    if any(phrase in norm for phrase in NEGATIVE if ' ' in phrase):
        return True
    # Word match
    words = norm.split()
    return any(word in NEGATIVE for word in words)


def get_reply(user_id, msg):
    state = user_states.get(user_id, {"step": 0, "biology": None})
    step = state["step"]
    msg_norm = msg.strip().lower()

    # --- Knowledge Base Search ---
    def kb_search(query):
        # Normalize
        query = query.lower().strip()
        # 1. Exact match
        for entry in KNOWLEDGE_BASE:
            if entry["question"] == query:
                return entry["answer"]
        # 2. Fuzzy match (difflib)
        questions = [entry["question"] for entry in KNOWLEDGE_BASE]
        close = difflib.get_close_matches(query, questions, n=1, cutoff=0.6)
        if close:
            for entry in KNOWLEDGE_BASE:
                if entry["question"] == close[0]:
                    return entry["answer"]
        # 3. Partial/keyword overlap
        query_words = set(query.split())
        best_score = 0
        best_ans = None
        for entry in KNOWLEDGE_BASE:
            kb_words = set(entry["question"].split())
            overlap = len(query_words & kb_words)
            if overlap > best_score:
                best_score = overlap
                best_ans = entry["answer"]
        if best_score > 0:
            return best_ans
        return None

    # Handle 'tell me more' or 'details' requests
    if "tell me more" in msg_norm or "details" in msg_norm or "aur jaankari" in msg_norm:
        last_ans = state.get("last_kb_ans")
        if last_ans:
            return last_ans + "\nYadi aap kisi vishesh topic par aur jaankari chahte hain, jaise 'fee structure', 'hostel', ya 'scholarship', toh please poochhein!", False
        return "Main aapki madad ke liye yahan hoon! Kripya nursing admission se judi koi bhi query poochhein (jaise 'eligibility', 'fee', 'hostel', etc.)", False

    # Try knowledge base first
    kb_ans = kb_search(msg_norm)
    if kb_ans:
        user_states[user_id] = {**state, "last_kb_ans": kb_ans}
        return kb_ans, False

    # Universal negative handler
    if is_negative(msg):
        user_states[user_id] = {"step": 0, "biology": None}
        return ("Koi baat nahi! Aapne mana kiya, isliye hum yahin rukte hain. Agar aapko future mein madad chahiye ho toh zaroor batayen. Dhanyavaad!"), True

    # Stepwise conversation (fallback)
    if step == 0:
        user_states[user_id] = {"step": 1, "biology": None}
        return "Namaste! Kya aap Nursing College mein admission lene mein ruchi rakhte hain?", False

    if step == 1:
        if is_positive(msg):
            user_states[user_id]["step"] = 2
            return "Kya aapne 12vi mein Biology padha hai?", False
        else:
            user_states[user_id] = {"step": 0, "biology": None}
            return "Theek hai, agar aapko future mein madad chahiye ho toh zaroor batayen. Dhanyavaad!", True

    if step == 2:
        if "biology" in msg_norm or is_positive(msg):
            user_states[user_id]["step"] = 3
            user_states[user_id]["biology"] = True
            return ("Bahut accha! Main aapko B.Sc Nursing program ke baare mein kuch jankari deta hoon. "
                    "Kya aap aur jaankari chahenge?"), False
        else:
            user_states[user_id] = {"step": 0, "biology": None}
            return "B.Sc Nursing mein admission ke liye Biology avashyak hai.", True

    if step == 3:
        if is_positive(msg):
            user_states[user_id]["step"] = 4
            return ("B.Sc Nursing ek full-time program hai jo aapko nursing field mein career ke liye tayyar karta hai. "
                    "Kya aapko program ke fee structure ke baare mein jaankari chahiye?"), False
        else:
            user_states[user_id] = {"step": 0, "biology": None}
            return "Theek hai, agar aapko future mein madad chahiye ho toh zaroor batayen. Dhanyavaad!", True

    if step == 4:
        if is_positive(msg):
            user_states[user_id]["step"] = 5
            return ("Annual fee structure yeh hai:\n- Tuition Fee: ₹60,000\n- Bus Fee: ₹10,000\n- Total Annual Fees: ₹70,000\n"
                    "Yeh fees 3 installments mein baanti jaati hai:\n1. Pehla Installment: ₹30,000 (admission ke samay)\n"
                    "2. Dusra Installment: ₹20,000 (first semester ke baad)\n3. Teesra Installment: ₹20,000 (second semester ke baad)\n"
                    "Kya aap hostel ya training facilities ke baare mein jaanna chahenge?"), False
        else:
            user_states[user_id] = {"step": 0, "biology": None}
            return "Theek hai, agar aapko future mein madad chahiye ho toh zaroor batayen. Dhanyavaad!", True

    if step == 5:
        if is_positive(msg):
            user_states[user_id]["step"] = 6
            return ("Hostel mein 24x7 paani aur bijli uplabdh hai, CCTV surveillance aur ek warden bhi hamesha available rahte hain. "
                    "Hospital training bhi program ka hissa hai, jismein students ko real patients ke saath kaam karne ka mauka milta hai. "
                    "Kya aap college ki location ke baare mein jaanna chahenge?"), False
        else:
            user_states[user_id] = {"step": 0, "biology": None}
            return "Theek hai, agar aapko future mein madad chahiye ho toh zaroor batayen. Dhanyavaad!", True

    if step == 6:
        if is_positive(msg):
            user_states[user_id]["step"] = 7
            return ("Hamara college Delhi mein sthit hai. Kya aap location ya aaspaas ke area ke baare mein aur jaankari chahenge?"), False
        else:
            user_states[user_id] = {"step": 0, "biology": None}
            return "Theek hai, agar aapko future mein madad chahiye ho toh zaroor batayen. Dhanyavaad!", True

    if step == 7:
        if is_positive(msg):
            user_states[user_id]["step"] = 8
            return ("College Indian Nursing Council (INC), Delhi se manayata prapt hai. Kya aap accreditation ke baare mein aur jaankari chahenge?"), False
        else:
            user_states[user_id] = {"step": 0, "biology": None}
            return "Theek hai, agar aapko future mein madad chahiye ho toh zaroor batayen. Dhanyavaad!", True

    if step == 8:
        if is_positive(msg):
            user_states[user_id]["step"] = 9
            return ("Clinical training ke liye students ko yeh locations par bheja jaata hai:\n- District Hospital (Backundpur)\n- Community Health Centers\n- Regional Hospital (Chartha)\n- Ranchi Neurosurgery and Allied Science Hospital (Ranchi, Jharkhand)\nKya aap scholarship options ke baare mein jaanna chahenge?"), False
        else:
            user_states[user_id] = {"step": 0, "biology": None}
            return "Theek hai, agar aapko future mein madad chahiye ho toh zaroor batayen. Dhanyavaad!", True

    if step == 9:
        if is_positive(msg):
            user_states[user_id]["step"] = 10
            return ("Scholarship options uplabdh hain:\n- Government Post-Matric Scholarship (₹18,000 - ₹23,000)\n- Labour Ministry Scholarships (₹40,000 - ₹48,000), jo Labour Registration walon ke liye hain.\nKya aap seats availability ke baare mein jaanna chahenge?"), False
        else:
            user_states[user_id] = {"step": 0, "biology": None}
            return "Theek hai, agar aapko future mein madad chahiye ho toh zaroor batayen. Dhanyavaad!", True

    if step == 10:
        if is_positive(msg):
            user_states[user_id]["step"] = 11
            return ("B.Sc Nursing program mein kul 60 seats uplabdh hain. Kya aap admission eligibility criteria ke baare mein jaanna chahenge?"), False
        else:
            user_states[user_id] = {"step": 0, "biology": None}
            return "Theek hai, agar aapko future mein madad chahiye ho toh zaroor batayen. Dhanyavaad!", True

    if step == 11:
        if is_positive(msg):
            user_states[user_id]["step"] = 12
            return ("Admission ke liye yeh criteria hain:\n- 12vi mein Biology hona chahiye\n- PNT Exam pass karna anivarya hai\n- Umar 17 se 35 saal ke beech honi chahiye\nKya aapko aur kuch puchna hai ya admission process shuru karna hai?"), False
        else:
            user_states[user_id] = {"step": 0, "biology": None}
            return "Theek hai, agar aapko future mein madad chahiye ho toh zaroor batayen. Dhanyavaad!", True

    if step == 12:
        if is_positive(msg):
            user_states[user_id]["step"] = 0
            return "Aap apne prashn puch sakte hain ya admission ke liye apply kar sakte hain. Dhanyavaad!", True
        else:
            user_states[user_id] = {"step": 0, "biology": None}
            return "Dhanyavaad! Agar aapko future mein madad chahiye ho toh zaroor batayen.", True

    # Default fallback
    user_states[user_id] = {"step": 0, "biology": None}
    return "Maaf kijiye, main samajh nahi paaya. Kya aap Nursing College mein admission mein ruchi rakhte hain?", False

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_id = request.remote_addr  # Use IP as session key (for demo)
    msg = request.json.get("message", "")
    reply, end = get_reply(user_id, msg)
    return jsonify({"reply": reply, "end": end})

if __name__ == "__main__":
    app.run(debug=True)
