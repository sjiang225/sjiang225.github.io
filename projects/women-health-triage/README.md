# Right Care, Right Timing – AI-Powered Subspecialty Triage for Women's Health


An intelligent clinical triage assistant that automatically converses with patients, collects key medical information, determines urgency, matches the most appropriate OB/GYN subspecialty, and generates appointment summaries **with transparent RAG-based references** from the textbook *Telephone Triage for Obstetrics and Gynecology*.


## Key Features

- **Multi-turn patient dialogue**
  - Collects patient name, DOB, contact info, menstrual and pregnancy details, symptoms, allergies, and insurance.
- **Intelligent slot-filling**
  - Dynamically decides which question to ask next based on missing information.
- **RAG-powered clinical reasoning**
  - Retrieves relevant pages from *Telephone Triage for Obstetrics and Gynecology* using FAISS + OpenAI Embeddings.
  - Displays referenced page numbers and excerpts alongside the triage report.
- **Automatic urgency & specialty classification**
  - Identifies whether the case is *Emergency / Urgent / Routine* and recommends the appropriate subspecialty.
- **Doctor schedule integration**
  - Reads an internal `.xlsx` schedule and assigns the earliest available physician automatically.
- **Dual-mode compatibility**
  - Works with both **Streamlit web chat** and **Twilio phone call** interfaces.


## System Architecture

```
Streamlit (text chat UI)
TriageAgent (core logic)
├── Slot extraction & next-question logic
├── RAG retrieval from obgyn_index/
├── LLM summarization & confirmation
└── Reference display (page numbers + snippets)

Twilio (voice input/output)
└── OpenAI Realtime prompt for phone triage
```


## Project Structure

```
women-health-triage/
├── app_chat.py               # Streamlit chat interface
├── main.py                   # Twilio voice interface (FastAPI + WebSocket)
├── appointment_db.py         # SQLite appointment booking utilities
├── schedule_loader.py        # Utility to read doctor schedule Excel
├── triage_agent.py           # Core multi-agent logic (slots + RAG + LLM)
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── fig1.pdf                  # Project architecture figure
└── README.md
```

## Public Repository Note

This public snapshot intentionally excludes local secrets and generated/private data:

- `.env` with real API keys
- `appointments.sqlite3`
- `uploaded_schedule.xlsx`
- `obgyn_index/` FAISS artifacts derived from the clinical reference text
- Python cache files

To run the full RAG workflow, recreate or provide your own local `obgyn_index/`
directory and point the app to a non-sensitive schedule file.


## Quick Start

### Install dependencies
```bash
pip install -r requirements.txt
```

### Prepare your `.env`

Create a file named `.env` in the root folder:

```bash
OPENAI_API_KEY=your-openai-api-key
```

For a full template, copy `.env.example` and fill in your real values.

### Launch the Streamlit App

```bash
streamlit run app_chat.py
```

Then open the displayed local URL (e.g., `http://localhost:8501`).

### Configure the clinic schedule

The patient app reads the clinic schedule from an internal `.xlsx` file. By default:

```text
uploaded_schedule.xlsx
```

To use a different file, set:

```bash
DOCTOR_SCHEDULE_PATH=/path/to/doctor_schedule.xlsx
```

Supported schedule formats:

```text
Wide format: Doctor | Specialty | Insurance (optional) | Mon | Tue | Wed ...
Long format: Doctor | Specialty | Insurance (optional) | Day | Time
```

Day cells can contain `Y`, `Yes`, `Available`, or concrete times such as `09:00, 14:00`.

If a day cell contains only `Y`, the app treats that doctor as available for the
whole clinic day and expands it into one-hour slots. By default the clinic day is
`09:00` to `17:00`, so the generated slots are `09:00`, `10:00`, ..., `16:00`.
You can override this with environment variables:

```bash
CLINIC_DAY_START=08:00
CLINIC_DAY_END=18:00
```

## Appointment Database

The Streamlit app stores booked appointments in a local SQLite database:

```text
appointments.sqlite3
```

Each `(doctor, date, time)` can be booked only once. Once a patient selects a
slot, that slot is written to the database and disappears from future available
slot lists. To place the database somewhere else, set:

```bash
APPOINTMENTS_DB=/path/to/appointments.sqlite3
```

## RAG Integration

The **RAG pipeline** retrieves the most relevant passages from the OB/GYN telephone triage textbook to support model reasoning.
These references are displayed at the end of the summary.

Example output:

```
Triage Summary
- Patient: Alice Chen
- Complaint: Light spotting at 32 weeks
- Urgency: Urgent
- Specialty: Maternal-Fetal Medicine

References from Handbook:
Page 132: Patients presenting with spotting after 30 weeks should be assessed for placental causes...
Page 135: If bleeding is associated with pain, immediate evaluation is recommended...
```

## Optional: Twilio Voice Interface

To enable phone-based triage:

```bash
python main.py
```

* This spins up a FastAPI WebSocket server compatible with **Twilio Media Streams**.
* Patients can talk to a Realtime API voice triage assistant through a phone call.
* The system uses real-time speech detection and synthesis.

Recommended phone settings in `.env`:

```bash
VOICE_PORT=5050
PUBLIC_BASE_URL=https://your-ngrok-or-domain.example.com
CLINIC_NAME=Women's Health Clinic
OPENAI_REALTIME_MODEL=gpt-realtime
OPENAI_REALTIME_VOICE=verse
OPENAI_REALTIME_TEMPERATURE=0.7
```

`PUBLIC_BASE_URL` should be the public HTTPS domain that Twilio can reach. For
local development, this is usually your ngrok URL. Do not include
`/incoming-call` in `PUBLIC_BASE_URL`; the webhook path is added in Twilio.

You can check that the phone server is running at:

```text
http://localhost:5050/health
```

### Change the Twilio phone number

No code change is needed to switch the inbound phone number. In Twilio Console:

1. Buy or select the phone number you want to use.
2. Open that number's **Voice Configuration**.
3. Set **A call comes in** to your public HTTPS URL ending in `/incoming-call`, for example:

```text
https://your-ngrok-or-domain.example.com/incoming-call
```

4. Keep the method as `POST` or `GET`.

If your public tunnel/domain changes, update both places:

1. `.env` → `PUBLIC_BASE_URL=https://new-domain.example.com`
2. Twilio number Voice Configuration → `https://new-domain.example.com/incoming-call`

Then restart `python main.py`.

## Technologies Used

| Component               | Description                         |
| ----------------------- | ----------------------------------- |
| **OpenAI GPT-4o-mini**  | LLM reasoning & response generation |
| **LangChain + FAISS**   | RAG pipeline for textbook retrieval |
| **Streamlit**           | Web chat frontend                   |
| **Twilio Realtime API** | Phone call streaming interface      |
| **dotenv**              | Secure API key management           |
