import uuid

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from assistant import config, database, documents, knowledge
from assistant.graph import build_graph
from assistant.tools import Context

st.set_page_config(page_title="AI Knowledge Assistant")

TOOL_LABELS = {
    "search_documents": "Mencari dokumen",
    "check_leave_balance": "Mengecek sisa cuti",
    "request_leave": "Mengajukan cuti",
    "create_it_ticket": "Membuat tiket IT",
}
EMPTY_ANSWER = "Maaf, saya belum bisa menjawab. Coba ulangi dengan kalimat lain."


@st.cache_resource(show_spinner="Menyiapkan asisten...")
def load_assistant():
    database.init_database()
    return knowledge.load_index(), build_graph()


def start_new_chat():
    st.session_state.thread_id = str(uuid.uuid4())  # id percakapan untuk memori agent
    st.session_state.chat = []  # riwayat chat yang ditampilkan di layar
    st.session_state.pending_leave = None  # detail cuti yang menunggu konfirmasi


def open_chat(thread_id: str):
    st.session_state.thread_id = thread_id
    st.session_state.chat = database.list_messages(thread_id)
    # Jika percakapan itu berhenti menunggu konfirmasi cuti, panel konfirmasinya ditampilkan lagi
    state = graph.get_state({"configurable": {"thread_id": thread_id}})
    st.session_state.pending_leave = state.interrupts[0].value if state.interrupts else None


def switch_account():
    st.session_state.employee_id = st.session_state.selected_employee
    start_new_chat()


def add_message(role: str, content: str, steps: list[str] | None = None):
    # Ditampilkan di layar dan disimpan ke database, supaya bisa dibuka lagi dari daftar riwayat
    st.session_state.chat.append({"role": role, "content": content, "steps": steps or []})
    database.save_message(st.session_state.thread_id, st.session_state.employee_id, role, content, steps or [])


def describe_step(node: str, update: dict | None) -> list[str]:
    if node == "grade_documents":
        return ["Menilai relevansi hasil pencarian"]

    steps = []
    for message in (update or {}).get("messages", []):
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                args = ", ".join(f"{key}: {value}" for key, value in call["args"].items())
                steps.append(f"{TOOL_LABELS[call['name']]} ({args})" if args else TOOL_LABELS[call["name"]])
        elif isinstance(message, AIMessage):
            steps.append("Menyusun jawaban")
        elif isinstance(message, ToolMessage) and message.name == "search_documents":
            sources = {line.strip("[]").removeprefix("Sumber: ")
                       for line in message.content.splitlines() if line.startswith("[Sumber:")}
            steps.append("Ditemukan: " + "; ".join(sorted(sources)))
        elif isinstance(message, ToolMessage):
            steps.append(f"{TOOL_LABELS[message.name]}: {message.content}")
        elif isinstance(message, HumanMessage):  # dari node rewrite_question atau pembatalan cuti
            steps.append(message.content)
    return steps


def run_assistant(graph_input):
    run_config = {"configurable": {"thread_id": st.session_state.thread_id}}
    context = Context(employee_id=st.session_state.employee_id, vector_store=vector_store)
    steps = []

    with st.chat_message("assistant"):
        with st.status("Agent sedang bekerja...", expanded=True) as status:
            for chunk in graph.stream(graph_input, run_config, context=context, stream_mode="updates"):
                for node, update in chunk.items():
                    if node == "__interrupt__":
                        continue
                    for step in describe_step(node, update):
                        steps.append(step)
                        status.write(step)
            status.update(label="Selesai", state="complete", expanded=False)

    state = graph.get_state(run_config)
    if state.interrupts:  # agent berhenti di node confirm_leave
        st.session_state.pending_leave = state.interrupts[0].value
        answer = "Sebelum saya ajukan, tolong cek detail cuti di bawah ini."
    else:
        answer = state.values["messages"][-1].text or EMPTY_ANSWER

    add_message("assistant", answer, steps)
    st.rerun()


# ---------- Persiapan ----------

if not config.GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY harus diisi. Salin `.env.example` menjadi `.env`, lalu isi API key-nya (lihat README).")
    st.stop()

if not config.INDEX_DIR.exists():
    st.error("Indeks dokumen belum dibuat. Jalankan dulu `python read_documents.py` lalu `python build_index.py`.")
    st.stop()

vector_store, graph = load_assistant()
st.session_state.setdefault("employee_id", config.DEMO_EMPLOYEE_ID)
if "thread_id" not in st.session_state:
    start_new_chat()

# ---------- Sidebar ----------

with st.sidebar:
    st.title("Nusa Teknologi")
    st.button("Percakapan baru", on_click=start_new_chat)

    st.caption("Riwayat")
    conversations = database.list_conversations(st.session_state.employee_id)
    if not conversations:
        st.caption("Belum ada percakapan.")
    for conversation in conversations:
        st.button(conversation["title"], key=conversation["thread_id"], on_click=open_chat,
                  args=(conversation["thread_id"],), disabled=conversation["thread_id"] == st.session_state.thread_id)

    # Profil. Di aplikasi perusahaan sungguhan, profil berasal dari login kantor. Di sini akun demo bisa diganti.
    employees = {employee["id"]: f"{employee['name']} · {employee['department']}" for employee in database.list_employees()}
    st.selectbox("Akun demo", employees, format_func=employees.get, key="selected_employee",
                 index=list(employees).index(st.session_state.employee_id), on_change=switch_account)

# ---------- Chat ----------

st.title("AI Knowledge Assistant")
st.caption("Tanya aturan perusahaan, cek dan ajukan cuti, atau laporkan masalah IT.")

if not st.session_state.chat:
    st.info("Contoh pertanyaan:\n"
            "- Berapa jatah cuti tahunan?\n"
            "- Apakah aturan lembur di kantor sudah sesuai PP 35 Tahun 2021?\n"
            "- Laptop saya mati total dan tanggal 5 sampai 6 Oktober saya mau cuti untuk acara keluarga.")
    with st.expander("Dokumen yang bisa ditanyakan"):
        for department, title in documents.list_documents():
            st.caption(f"{title} · {department}")

for message in st.session_state.chat:
    with st.chat_message(message["role"]):
        if message.get("steps"):
            with st.expander("Langkah agent"):
                st.markdown("\n".join(f"{number}. {step}" for number, step in enumerate(message["steps"], start=1)))
        st.markdown(message["content"])

# Panel konfirmasi muncul saat agent berhenti menunggu persetujuan pengajuan cuti
if st.session_state.pending_leave:
    leave = st.session_state.pending_leave
    with st.chat_message("assistant"):
        st.markdown(f"**Konfirmasi pengajuan cuti**\n\n"
                    f"- Tanggal: {leave['start_date']} s.d. {leave['end_date']}\n"
                    f"- Alasan: {leave['reason']}")
        decision = None
        if st.button("Ya, ajukan"):
            decision = "yes"
        if st.button("Batal"):
            decision = "no"

    if decision:
        st.session_state.pending_leave = None
        add_message("user", "Ya, ajukan" if decision == "yes" else "Batal")
        run_assistant(Command(resume=decision))

question = st.chat_input("Tulis pertanyaan...", disabled=bool(st.session_state.pending_leave))
if question:
    add_message("user", question)
    with st.chat_message("user"):
        st.markdown(question)
    run_assistant({"messages": [HumanMessage(question)], "rewrite_count": 0})
