import sqlite3
from datetime import date
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.runtime import Runtime
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field

from assistant import config, database
from assistant.llm import get_llm
from assistant.prompts import GRADE_PROMPT, REWRITE_PROMPT, SYSTEM_PROMPT
from assistant.tools import TOOLS, Context

DAY_NAMES = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


class State(MessagesState):
    rewrite_count: int  # berapa kali kata kunci pencarian sudah ditulis ulang


class Grade(BaseModel):
    relevant: bool = Field(description="True jika hasil pencarian berisi informasi untuk menjawab pertanyaan")


llm = get_llm()
agent_llm = llm.bind_tools(TOOLS)
# Penilaian diminta sebagai pemanggilan fungsi, cara yang sama dengan agent memanggil tool
grader_llm = llm.with_structured_output(Grade, method="function_calling")


# ---------- Node ----------

def agent(state: State, runtime: Runtime[Context]):
    employee = database.get_employee(runtime.context.employee_id)
    today = date.today()
    system_prompt = SYSTEM_PROMPT.format(
        name=employee["name"],
        position=employee["position"],
        department=employee["department"],
        day=DAY_NAMES[today.weekday()],
        today=today.isoformat(),
    )
    response = agent_llm.invoke([SystemMessage(system_prompt)] + state["messages"])
    return {"messages": [response]}


def confirm_leave(state: State) -> Command[Literal["tools", "agent"]]:
    last_message = state["messages"][-1]
    leave = next(call["args"] for call in last_message.tool_calls if call["name"] == "request_leave")

    answer = interrupt(leave)  # graph berhenti di sini sampai karyawan menjawab "yes" atau "no"

    if answer == "yes":
        return Command(goto="tools")

    # Setiap permintaan tool wajib punya hasil. Tandai semuanya belum dijalankan,
    # lalu sampaikan pembatalan sebagai pesan dari karyawan agar LLM tidak salah membaca.
    not_run = [ToolMessage("Belum dijalankan.", tool_call_id=call["id"], name=call["name"])
               for call in last_message.tool_calls]
    decline = HumanMessage("Saya membatalkan pengajuan cuti tersebut. Jangan ajukan cuti itu, tapi lanjutkan permintaan saya yang lain.")
    return Command(goto="agent", update={"messages": not_run + [decline]})


def grade_documents(state: State) -> Command[Literal["agent", "rewrite_question"]]:
    query, documents = get_last_search(state["messages"])
    grade = grader_llm.invoke(GRADE_PROMPT.format(query=query, documents=documents))

    if grade.relevant or state["rewrite_count"] >= config.MAX_REWRITES:
        return Command(goto="agent")
    return Command(goto="rewrite_question")


def rewrite_question(state: State):
    query, _ = get_last_search(state["messages"])
    new_query = llm.invoke(REWRITE_PROMPT.format(query=query)).text.strip()
    message = HumanMessage(f"Hasil pencarian untuk '{query}' kurang relevan. Cari lagi dengan kata kunci: {new_query}")
    return {"messages": [message], "rewrite_count": state["rewrite_count"] + 1}


# ---------- Routing ----------

def route_after_agent(state: State) -> Literal["tools", "confirm_leave", "__end__"]:
    tool_calls = state["messages"][-1].tool_calls
    if not tool_calls:
        return END
    if any(call["name"] == "request_leave" for call in tool_calls):
        return "confirm_leave"
    return "tools"


def route_after_tools(state: State) -> Literal["grade_documents", "agent"]:
    # Jika di antara hasil tool terbaru ada hasil pencarian dokumen, nilai dulu relevansinya
    for message in reversed(state["messages"]):
        if not isinstance(message, ToolMessage):
            break
        if message.name == "search_documents":
            return "grade_documents"
    return "agent"


def get_last_search(messages) -> tuple[str, str]:
    tool_message = next(m for m in reversed(messages) if isinstance(m, ToolMessage) and m.name == "search_documents")
    ai_message = next(m for m in reversed(messages) if isinstance(m, AIMessage) and m.tool_calls)
    query = next(call["args"]["query"] for call in ai_message.tool_calls if call["id"] == tool_message.tool_call_id)
    return query, tool_message.content


# ---------- Graph ----------

def build_graph():
    graph = StateGraph(State, context_schema=Context)

    graph.add_node("agent", agent)
    # handle_tool_errors: error di dalam tool (misalnya tanggal tidak valid) dikirim ke LLM, bukan membuat aplikasi crash
    graph.add_node("tools", ToolNode(TOOLS, handle_tool_errors=True))
    graph.add_node("confirm_leave", confirm_leave)
    graph.add_node("grade_documents", grade_documents)
    graph.add_node("rewrite_question", rewrite_question)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", route_after_agent)
    graph.add_conditional_edges("tools", route_after_tools)
    graph.add_edge("rewrite_question", "agent")

    # Memori agent disimpan di database, jadi percakapan lama bisa dibuka dan dilanjutkan.
    # check_same_thread=False karena Streamlit menjalankan setiap pengguna di thread yang berbeda.
    connection = sqlite3.connect(config.DATABASE_PATH, check_same_thread=False)
    return graph.compile(checkpointer=SqliteSaver(connection))
