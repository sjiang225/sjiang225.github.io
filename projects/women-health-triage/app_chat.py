# -*- coding: utf-8 -*-
"""
app_chat.py
Streamlit frontend for AI OB/GYN Triage System with doctor selection.
"""

import os
import html
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# --------------------------- Page Config ---------------------------
PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")
SCHEDULE_PATH = Path(os.getenv("DOCTOR_SCHEDULE_PATH", PROJECT_DIR / "uploaded_schedule.xlsx"))


def configure_secrets() -> bool:
    if os.getenv("OPENAI_API_KEY"):
        return True
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        api_key = None
    if api_key:
        os.environ["OPENAI_API_KEY"] = str(api_key)
        return True
    return False


from appointment_db import book_appointment, get_booked_slots, init_db
from schedule_loader import load_schedule
from triage_agent import TriageAgent, SLOTS, get_available_doctors_list

init_db()


def load_internal_schedule(path: str):
    return load_schedule(path)


def get_internal_schedule():
    if not SCHEDULE_PATH.exists():
        raise FileNotFoundError(f"Doctor schedule not found: {SCHEDULE_PATH}")
    return load_internal_schedule(str(SCHEDULE_PATH))


st.set_page_config(
    page_title="Women's Health Care Intake",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --------------------------- CSS ---------------------------
st.markdown("""
<style>
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], header [data-testid="stToolbar"] {
    visibility: hidden;
    height: 0;
}
.stApp {
    background: #f6f8fb;
}
.block-container {
    max-width: 1120px;
    padding-top: 1.6rem;
    padding-bottom: 3rem;
}
[data-testid="stSidebar"] {
    background: #eef3f4;
    border-right: 1px solid #d7e1e4;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 2.35rem;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #24343a;
    letter-spacing: 0;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #65757c;
    line-height: 1.55;
}
[data-testid="stProgress"] > div > div > div {
    background: #0f8f83;
}
.care-steps {
    margin: 1.1rem 0 0.25rem 0;
    display: grid;
    gap: 0.52rem;
}
.care-step {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    color: #65757c;
    font-size: 0.9rem;
}
.care-dot {
    width: 0.68rem;
    height: 0.68rem;
    border-radius: 50%;
    border: 2px solid #b8c8cd;
    background: #ffffff;
}
.care-step.active {
    color: #24343a;
    font-weight: 700;
}
.care-step.active .care-dot {
    background: #0f8f83;
    border-color: #0f8f83;
}
.care-step.done .care-dot {
    background: #d9a441;
    border-color: #d9a441;
}
.patient-header {
    border: 1px solid #d8e4e7;
    background: #ffffff;
    border-radius: 8px;
    padding: 1.45rem 1.6rem 1.25rem 1.6rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 14px 34px rgba(36, 52, 58, 0.08);
    border-top: 4px solid #0f8f83;
}
.main-header {
    font-size: 2.18rem;
    line-height: 1.2;
    font-weight: 780;
    color: #202934;
    margin: 0 0 0.35rem 0;
    letter-spacing: 0;
}
.sub-header {
    color: #5c6972;
    font-size: 1rem;
    margin: 0;
}
.section-label {
    color: #0f8f83;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}
.header-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 1.25rem;
    align-items: center;
}
.status-rail {
    display: grid;
    grid-template-columns: repeat(3, minmax(92px, 1fr));
    gap: 0.55rem;
}
.status-chip {
    border: 1px solid #d8e4e7;
    border-radius: 7px;
    padding: 0.55rem 0.7rem;
    background: #f8fbfb;
    color: #3d4b53;
    font-size: 0.78rem;
    font-weight: 650;
    white-space: nowrap;
}
.status-chip strong {
    display: block;
    color: #202934;
    font-size: 0.95rem;
    margin-bottom: 0.05rem;
}
.clinic-strip {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.2rem;
}
.clinic-strip-item {
    background: #ffffff;
    border: 1px solid #d8e4e7;
    border-left: 4px solid #d9a441;
    border-radius: 8px;
    padding: 0.8rem 0.95rem;
    color: #5c6972;
    box-shadow: 0 8px 22px rgba(36, 52, 58, 0.05);
}
.clinic-strip-item strong {
    display: block;
    color: #202934;
    font-size: 0.96rem;
    margin-bottom: 0.16rem;
}
[data-testid="stChatMessage"] {
    background: #ffffff;
    border: 1px solid #d8e4e7;
    border-radius: 8px;
    padding: 0.35rem 0.65rem;
    box-shadow: 0 8px 20px rgba(36, 52, 58, 0.045);
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    color: #2a333a;
}
[data-testid="stAlert"] {
    border-radius: 8px;
    border: 1px solid #d8e4e7;
}
[data-testid="stChatInput"] {
    border-radius: 8px;
}
.doctor-card {
    background: #ffffff;
    border: 1px solid #d8e4e7;
    border-left: 4px solid #0f8f83;
    border-radius: 8px;
    padding: 1.05rem 1.2rem;
    margin: 1rem 0 0.65rem 0;
    box-shadow: 0 10px 26px rgba(36, 52, 58, 0.06);
}
.doctor-name {
    font-size: 1.16rem;
    font-weight: 720;
    color: #202934;
    margin-bottom: 0.5rem;
}
.doctor-meta {
    color: #5c6972;
    margin: 0.2rem 0;
}
.doctor-pill {
    display: inline-block;
    border-radius: 999px;
    padding: 0.18rem 0.55rem;
    margin-left: 0.4rem;
    color: #0f5f58;
    background: #e7f5f2;
    border: 1px solid #c8e6e1;
    font-size: 0.75rem;
    font-weight: 700;
}
.stButton > button {
    border-radius: 6px;
    font-weight: 650;
    border: 1px solid #0f8f83;
    background: #0f8f83;
    color: #ffffff;
}
.stButton > button:hover {
    border: 1px solid #0b7068;
    background: #0b7068;
    color: #ffffff;
}
.stSelectbox div[data-baseweb="select"] > div {
    border-radius: 6px;
    border-color: #cfdadf;
    background: #ffffff;
}
.system-footer {
    border-top: 1px solid #d8e4e7;
    margin-top: 2rem;
    padding-top: 1.1rem;
    color: #6b7780;
    font-size: 0.86rem;
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
}
.system-footer strong {
    color: #24343a;
}
hr {
    border-color: #d8e4e7;
}
@media (max-width: 900px) {
    .header-grid,
    .clinic-strip {
        grid-template-columns: 1fr;
    }
    .status-rail {
        grid-template-columns: 1fr;
    }
    .main-header {
        font-size: 1.7rem;
    }
}
</style>
""", unsafe_allow_html=True)

# --------------------------- Header ---------------------------
st.markdown(
    """
    <section class="patient-header">
        <div class="header-grid">
            <div>
                <p class="section-label">Women\'s Health Front Desk</p>
                <h1 class="main-header">Clinical Intake & Appointment Triage</h1>
                <p class="sub-header">Share what is going on, and we will route you to the right OB/GYN specialist.</p>
            </div>
            <div class="status-rail" aria-label="Visit status">
                <div class="status-chip"><strong>Intake</strong>Secure</div>
                <div class="status-chip"><strong>Routing</strong>Specialty match</div>
                <div class="status-chip"><strong>Booking</strong>Live slots</div>
            </div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="clinic-strip">
        <div class="clinic-strip-item"><strong>Private Visit Record</strong>Active session</div>
        <div class="clinic-strip-item"><strong>Urgency Screen</strong>Safety first</div>
        <div class="clinic-strip-item"><strong>Specialty Desk</strong>OB/GYN routing</div>
    </section>
    """,
    unsafe_allow_html=True,
)

# --------------------------- Sidebar ---------------------------
with st.sidebar:
    st.subheader("Front Desk Queue")
    current_slots = st.session_state.get("slots", dict(SLOTS))
    intake_fields = [k for k in SLOTS if k not in {"age"}]
    collected = sum(1 for k in intake_fields if current_slots.get(k))
    st.progress(min(collected / max(len(intake_fields), 1), 1.0))
    st.caption(f"{collected}/{len(intake_fields)} intake items complete")

    stage = st.session_state.get("stage", "collecting")
    step_classes = {
        "intake": "active" if stage in {"greeting", "collecting"} else "done",
        "triage": "active" if stage == "triaging" else ("done" if stage in {"selecting_doctor", "confirming", "confirmed"} else ""),
        "booking": "active" if stage in {"selecting_doctor", "confirming"} else ("done" if stage == "confirmed" else ""),
    }
    st.markdown(
        f"""
        <div class="care-steps">
            <div class="care-step {step_classes['intake']}"><span class="care-dot"></span><span>Intake</span></div>
            <div class="care-step {step_classes['triage']}"><span class="care-dot"></span><span>Clinical routing</span></div>
            <div class="care-step {step_classes['booking']}"><span class="care-dot"></span><span>Appointment desk</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.caption("If you are experiencing severe symptoms or feel unsafe, call 911 or go to the nearest emergency room.")

    if st.button("Start Over", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if not configure_secrets():
    st.error("Care intake is temporarily unavailable. Please contact the clinic directly.")
    st.stop()

# --------------------------- Session Init ---------------------------
if "agent" not in st.session_state:
    st.session_state.agent = TriageAgent()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "slots" not in st.session_state:
    st.session_state.slots = dict(SLOTS)
if "stage" not in st.session_state:
    st.session_state.stage = "greeting"
if "available_doctors" not in st.session_state:
    st.session_state.available_doctors = []
if "selected_doctor" not in st.session_state:
    st.session_state.selected_doctor = None
if "triage_result" not in st.session_state:
    st.session_state.triage_result = None
if "rag_answer" not in st.session_state:
    st.session_state.rag_answer = ""
if "rag_refs" not in st.session_state:
    st.session_state.rag_refs = []

agent = st.session_state.agent

# --------------------------- Helper Functions ---------------------------
def bot_say(text, message_type="normal"):
    st.session_state.messages.append({"role": "assistant", "content": text, "type": message_type})

def user_say(text):
    st.session_state.messages.append({"role": "user", "content": text})

def render_message(msg):
    with st.chat_message(msg["role"]):
        style = msg.get("type", "normal")
        content = msg["content"]
        if style == "info":
            st.info(content)
        elif style == "warning":
            st.warning(content)
        elif style == "success":
            st.success(content)
        else:
            st.markdown(content)

# --------------------------- Initial Greeting ---------------------------
if not st.session_state.messages:
    greeting = (
        "Welcome. We will ask a few questions to understand your concern and help find an appropriate appointment.\n\n"
        "**First question:** Is this an emergency situation? (Yes/No)"
    )
    bot_say(greeting, "info")
    st.session_state.stage = "collecting"

# --------------------------- Render Chat History ---------------------------
for m in st.session_state.messages:
    render_message(m)

# --------------------------- Doctor Selection UI ---------------------------
if st.session_state.stage == "selecting_doctor" and st.session_state.available_doctors:
    st.markdown("### Available Appointments")

    for idx, doctor in enumerate(st.session_state.available_doctors):
        with st.container():
            doctor_name = html.escape(str(doctor.get("name", "Unknown doctor")))
            specialty = html.escape(str(doctor.get("subspecialty", "OB/GYN")))
            earliest = doctor.get("earliest_slot", {})
            earliest_date = html.escape(str(earliest.get("date", "TBD")))
            earliest_day = html.escape(str(earliest.get("day", "")))
            earliest_time = html.escape(str(earliest.get("time", "")))
            st.markdown(f"""
            <div class="doctor-card">
                <div class="doctor-name">{doctor_name}</div>
                <p class="doctor-meta"><strong>Specialty:</strong> {specialty}</p>
                <p class="doctor-meta"><strong>Insurance:</strong> {'Accepted' if doctor['insurance_accepted'] else 'Not in network'}</p>
                <p class="doctor-meta"><strong>Earliest:</strong> {earliest_date} ({earliest_day}) at {earliest_time}</p>
                <p class="doctor-meta"><strong>Open slots shown:</strong> {len(doctor.get('available_slots', []))}</p>
            </div>
            """, unsafe_allow_html=True)

            slots = doctor.get("available_slots", [])
            slot_labels = [f"{slot['date']} ({slot['day']}) at {slot['time']}" for slot in slots]
            selected_label = st.selectbox(
                "Choose an appointment time",
                slot_labels,
                key=f"slot_select_{idx}",
                label_visibility="collapsed",
            )
            selected_idx = slot_labels.index(selected_label)
            slot = slots[selected_idx]

            if st.button("Reserve this appointment", key=f"reserve_{idx}", use_container_width=True):
                selected = {
                    "name": doctor['name'],
                    "specialty": doctor['subspecialty'],
                    "date": slot['date'],
                    "time": slot['time'],
                    "wait_days": doctor['wait_days']
                }
                booked = book_appointment(
                    doctor_name=selected["name"],
                    specialty=selected["specialty"],
                    appointment_date=selected["date"],
                    appointment_time=selected["time"],
                    patient_name=agent.slots.get("name") or "",
                    patient_contact=agent.slots.get("contact") or "",
                    symptom=agent.slots.get("symptom") or "",
                )
                if not booked:
                    st.warning("That appointment was just booked by another patient. Please choose another time.")
                    try:
                        availability = get_internal_schedule()
                        st.session_state.available_doctors = get_available_doctors_list(
                            availability=availability,
                            subspecialty_code=st.session_state.triage_result["subspecialty_code"],
                            urgency=st.session_state.triage_result["urgency"],
                            insurance=agent.slots.get("insurance"),
                            booked_slots=get_booked_slots(),
                            slots_per_doctor=16,
                        )
                    except Exception:
                        pass
                    st.rerun()
                st.session_state.selected_doctor = selected
                st.session_state.stage = "confirming"
                st.rerun()

            st.markdown("---")

# --------------------------- Input Handling ---------------------------
if st.session_state.stage not in ["selecting_doctor", "confirming", "confirmed"]:
    prompt = st.chat_input("Type your answer here...")

    if prompt:
        user_say(prompt)
        with st.chat_message("user"):
            st.markdown(prompt)

        # --- Update agent slots ---
        old_slots = agent.slots.copy()
        agent.update(prompt)
        st.session_state.slots = agent.slots.copy()

        updated_fields = [k for k in SLOTS if old_slots.get(k) != agent.slots.get(k) and agent.slots.get(k)]

        # --- Acknowledge updated fields ---
        if updated_fields and st.session_state.stage == "collecting":
            ack = f"✓ Recorded: {', '.join(updated_fields)}"
            bot_say(ack)
            with st.chat_message("assistant"):
                st.markdown(ack)

        # If the patient says this is an emergency, do not continue intake.
        if st.session_state.stage == "collecting" and str(agent.slots.get("emergency_check", "")).lower() == "yes":
            from triage_agent import confirmation

            triage_info = agent.triage()
            st.session_state.triage_result = triage_info
            red_flags = triage_info.get("red_flags", [])
            red_flags_list = "\n".join([f"- {flag}" for flag in red_flags])
            emergency_summary = f"""
### Emergency Alert

You indicated this may be an emergency.

**URGENT RECOMMENDATION:**
**Call 911 immediately** or go to your nearest Emergency Room.

**Warning signs noted:**
{red_flags_list if red_flags else '- Patient reported an emergency situation'}

---

{confirmation(agent.slots, triage_info, {"doctor_name": "Emergency Department"}, "")}
"""
            bot_say(emergency_summary, "warning")
            with st.chat_message("assistant"):
                st.warning(emergency_summary)
            st.session_state.stage = "confirmed"
            st.rerun()

        # --- Ask next question or finalize triage ---
        question = agent.next_question()

        if question and st.session_state.stage == "collecting":
            bot_say(question)
            with st.chat_message("assistant"):
                st.markdown(question)

        elif not question and st.session_state.stage == "collecting":
            st.session_state.stage = "triaging"
            with st.spinner("Analyzing your information and matching OB/GYN specialists..."):
                try:
                    availability = get_internal_schedule()
                except Exception as e:
                    print("Schedule load error:", e)
                    error_msg = "Scheduling is temporarily unavailable. Please contact the clinic directly."
                    bot_say(error_msg, "warning")
                    with st.chat_message("assistant"):
                        st.warning(error_msg)
                    st.session_state.stage = "collecting"
                    st.stop()

                # Perform triage
                triage_info = agent.triage()
                st.session_state.triage_result = triage_info
                urgency = triage_info.get('urgency', 'routine')

                # Handle emergency
                if urgency == 'emergency':
                    from triage_agent import confirmation
                    red_flags = triage_info.get('red_flags', [])
                    red_flags_list = "\n".join([f"- {flag}" for flag in red_flags])

                    emergency_summary = f"""
### Emergency Alert

**Patient:** {agent.slots.get('name', 'N/A')}
**Contact:** {agent.slots.get('contact', 'N/A')}
**Symptoms:** {agent.slots.get('symptom', 'N/A')}

**Critical warning signs detected:**
{red_flags_list if red_flags else 'Emergency condition identified'}

**URGENT RECOMMENDATION:**
**Call 911 immediately** or go to your nearest Emergency Room

**Clinical Assessment:** {triage_info.get('reasoning', 'Immediate medical attention required')}

---

{confirmation(agent.slots, triage_info, {"doctor_name": "Emergency Department"}, "")}
"""
                    bot_say(emergency_summary, "warning")
                    with st.chat_message("assistant"):
                        st.warning(emergency_summary)
                    st.session_state.stage = "confirmed"
                    st.rerun()

                rag_answer, rag_refs = agent.rag_consult()
                st.session_state.rag_answer = rag_answer
                st.session_state.rag_refs = rag_refs
                references_section = ""
                if rag_refs:
                    references = "\n".join(
                        [f"- Page {page}: {snippet}..." for page, snippet in rag_refs]
                    )
                    references_section = f"""

**Clinical References**
{references}
"""

                # Get available doctors
                available_doctors = get_available_doctors_list(
                    availability=availability,
                    subspecialty_code=triage_info["subspecialty_code"],
                    urgency=triage_info["urgency"],
                    insurance=agent.slots.get("insurance"),
                    booked_slots=get_booked_slots(),
                    slots_per_doctor=16,
                )

                st.session_state.available_doctors = available_doctors

                # Display triage summary
                s = agent.slots
                summary = f"""
### Triage Summary

**Patient Info**
- Name: `{s.get('name', 'N/A')}`
- Contact: `{s.get('contact', 'N/A')}`
- Age: `{s.get('age', 'N/A')}`
- Insurance: `{s.get('insurance', 'N/A')}`

**Reproductive Info**
- Menstrual Cycle: `{s.get('menstrual_cycle', 'N/A')}`
- Last Period: `{s.get('last_period', 'N/A')}`
- Pregnancy Week: `{s.get('pregnancy_week', 'N/A')}`

**Clinical Assessment**
- Complaint: `{s.get('symptom', 'N/A')}`
- Urgency: `{urgency}`
- Recommended Specialty: `{triage_info.get('subspecialty', 'N/A')}`
- Confidence: `{triage_info.get('confidence', 0):.0%}`

---

**Found {len(available_doctors)} available doctor(s) matching your needs.**

Please select your preferred doctor and appointment time from the options below.
{references_section}
"""

                bot_say(summary, "success")
                with st.chat_message("assistant"):
                    st.success(summary)

                if available_doctors:
                    st.session_state.stage = "selecting_doctor"
                else:
                    no_doctor_msg = "Unfortunately, no doctors are currently available for your selected criteria. Please contact our office directly at (XXX) XXX-XXXX to schedule an appointment."
                    bot_say(no_doctor_msg, "warning")
                    with st.chat_message("assistant"):
                        st.warning(no_doctor_msg)
                    st.session_state.stage = "confirmed"

                st.rerun()

# --------------------------- Confirmation Stage ---------------------------
if st.session_state.stage == "confirming" and st.session_state.selected_doctor:
    from triage_agent import confirmation

    doctor_info = {
        "doctor_name": st.session_state.selected_doctor["name"],
        "available_date": st.session_state.selected_doctor["date"],
        "available_time": st.session_state.selected_doctor["time"],
        "wait_days": st.session_state.selected_doctor["wait_days"]
    }

    confirm_msg = confirmation(agent.slots, st.session_state.triage_result, doctor_info, st.session_state.get("rag_answer", ""))

    final_summary = f"""
### Appointment Confirmed

**Your Appointment Details:**
- Doctor: **{st.session_state.selected_doctor['name']}**
- Specialty: {st.session_state.selected_doctor['specialty']}
- Date: **{st.session_state.selected_doctor['date']}**
- Time: **{st.session_state.selected_doctor['time']}**
- Wait time: {st.session_state.selected_doctor['wait_days']} day(s)

---

{confirm_msg}
"""

    bot_say(final_summary, "success")
    with st.chat_message("assistant"):
        st.success(final_summary)

    st.session_state.stage = "confirmed"
    st.rerun()

# --------------------------- Footer ---------------------------
st.markdown("""
<div class="system-footer">
    <span><strong>Women\'s Health Care Intake</strong></span>
    <span>This system supports triage and scheduling. It does not replace professional medical advice.</span>
    <span>For emergencies, call 911.</span>
</div>
""", unsafe_allow_html=True)
