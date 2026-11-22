from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from langchain.tools import ToolRuntime, tool
from langchain_qdrant import QdrantVectorStore
from qdrant_client import models

from assistant import config, database
from assistant.prompts import SEARCH_TOOL_DESCRIPTION

SATURDAY = 5  # date.weekday(): Senin = 0, ..., Sabtu = 5, Minggu = 6


@dataclass
class Context:
    # Data sesi yang dikirim aplikasi ke tool. LLM tidak bisa melihat atau mengubahnya.
    employee_id: str
    vector_store: QdrantVectorStore


def blocked_documents(department: str) -> list[str]:
    return [document for document, allowed in config.CONFIDENTIAL_DOCUMENTS.items() if department not in allowed]


def search_filter(source: str, department: str) -> models.Filter:
    is_regulation = models.FieldCondition(
        key="metadata.department", match=models.MatchValue(value=config.REGULATION_FOLDER)
    )
    must, must_not = ([is_regulation], []) if source == "regulasi" else ([], [is_regulation])

    # Hak akses diterapkan sebelum pencarian, sehingga dokumen rahasia tidak pernah sampai ke LLM
    blocked = blocked_documents(department)
    if blocked:
        must_not.append(models.FieldCondition(key="metadata.document", match=models.MatchAny(any=blocked)))
    return models.Filter(must=must, must_not=must_not)


@tool(description=SEARCH_TOOL_DESCRIPTION)
def search_documents(query: str, source: Literal["internal", "regulasi"], runtime: ToolRuntime[Context]) -> str:
    employee = database.get_employee(runtime.context.employee_id)
    results = runtime.context.vector_store.similarity_search(
        query, k=config.SEARCH_RESULTS, filter=search_filter(source, employee["department"])
    )
    return "\n\n".join(
        f"[Sumber: {document.metadata['title']}, hal. {document.metadata['page']}]\n{document.page_content}"
        for document in results
    )


@tool(description="Cek sisa cuti tahunan milik karyawan yang sedang bertanya.")
def check_leave_balance(runtime: ToolRuntime[Context]) -> str:
    employee = database.get_employee(runtime.context.employee_id)
    return f"Sisa cuti tahunan {employee['name']}: {employee['leave_balance']} hari."


@tool(description="Ajukan cuti tahunan untuk karyawan yang sedang bertanya. Format tanggal: YYYY-MM-DD.")
def request_leave(start_date: str, end_date: str, reason: str, runtime: ToolRuntime[Context]) -> str:
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    days = count_workdays(start, end)
    employee = database.get_employee(runtime.context.employee_id)

    if days == 0:
        return "Pengajuan gagal: tanggal yang dipilih tidak mencakup hari kerja."
    if days > employee["leave_balance"]:
        return f"Pengajuan gagal: butuh {days} hari kerja, tetapi sisa cuti hanya {employee['leave_balance']} hari."

    request_id = database.add_leave_request(employee["id"], start_date, end_date, days, reason)
    return (f"Pengajuan cuti #{request_id} tersimpan: {start_date} s.d. {end_date} ({days} hari kerja). "
            "Status: menunggu persetujuan atasan. Sisa cuti baru dipotong setelah disetujui.")


@tool(description="Buat tiket laporan masalah perangkat, akun, atau jaringan ke tim IT Support.")
def create_it_ticket(problem: str, runtime: ToolRuntime[Context]) -> str:
    ticket_id = database.add_it_ticket(runtime.context.employee_id, problem)
    return f"Tiket IT-{ticket_id:04d} sudah dibuat. Tim IT Support akan menghubungi lewat email kantor."


def count_workdays(start: date, end: date) -> int:
    total_days = (end - start).days + 1
    return sum(1 for offset in range(total_days) if (start + timedelta(days=offset)).weekday() < SATURDAY)


TOOLS = [search_documents, check_leave_balance, request_leave, create_it_ticket]
