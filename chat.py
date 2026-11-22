import sys
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from assistant import config, database, knowledge
from assistant.graph import build_graph
from assistant.tools import Context

TOOL_RESULT_PREVIEW = 80  # jumlah karakter hasil tool yang ditampilkan di terminal


def run(graph_input):
    for chunk in graph.stream(graph_input, run_config, context=context, stream_mode="updates"):
        for node, update in chunk.items():
            if node == "grade_documents":
                print("  [langkah] menilai relevansi hasil pencarian")
            if node in ("__interrupt__", "grade_documents") or not update:
                continue
            for message in update.get("messages", []):
                if isinstance(message, AIMessage) and message.tool_calls:
                    for call in message.tool_calls:
                        print(f"  [langkah] memanggil {call['name']} {call['args']}")
                elif isinstance(message, ToolMessage):
                    print(f"  [langkah] hasil {message.name}: {message.content[:TOOL_RESULT_PREVIEW]}...")
                elif isinstance(message, HumanMessage):  # dari node rewrite_question atau pembatalan cuti
                    print(f"  [langkah] {message.content}")


# Akun bisa dipilih lewat argumen, misalnya: python chat.py EMP002
employee_id = sys.argv[1] if len(sys.argv) > 1 else config.DEMO_EMPLOYEE_ID

print("Menyiapkan asisten...")
database.init_database()
graph = build_graph()
run_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
context = Context(employee_id=employee_id, vector_store=knowledge.load_index())
employee = database.get_employee(employee_id)
print(f"Siap! Masuk sebagai {employee['name']} ({employee['department']}). Ketik 'keluar' untuk berhenti.")

while True:
    question = input("\nKamu: ")
    if question.lower() == "keluar":
        break

    run({"messages": [HumanMessage(question)], "rewrite_count": 0})

    # Jika agent berhenti untuk meminta konfirmasi cuti, tanyakan ke pengguna lalu lanjutkan graph
    while graph.get_state(run_config).interrupts:
        leave = graph.get_state(run_config).interrupts[0].value
        answer = input(f"\nAjukan cuti {leave['start_date']} s.d. {leave['end_date']} ({leave['reason']})? (ya/tidak): ")
        run(Command(resume="yes" if answer.lower() == "ya" else "no"))

    answer = graph.get_state(run_config).values["messages"][-1].content
    print(f"\nAsisten: {answer}")
