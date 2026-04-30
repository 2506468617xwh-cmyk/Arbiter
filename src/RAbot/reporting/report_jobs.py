# src/RAbot/reporting/report_jobs.py
from __future__ import annotations

import inspect
import json
import sqlite3
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


# ============================================================
# RAbot Background Report Jobs
# ------------------------------------------------------------
# 作用：
# 1. 把 LLM 报告生成放到后台线程执行，避免 Streamlit 前端灰屏卡死。
# 2. 用 SQLite 持久化任务状态，页面刷新后仍然能看到任务进度。
# 3. 暴露 create_job / run_job_async / get_job / list_jobs 等通用接口。
#
# 设计原则：
# - 不强依赖你现有的 research_writer 具体函数名；
# - 任何耗时函数都可以被包装成后台任务；
# - 如果耗时函数支持 progress_callback 参数，就能实时更新进度；
# - 如果不支持，也能正常执行，只是进度会从 5% 跳到 100%。
# ============================================================


def _project_root() -> Path:
    """
    当前文件路径：
    project_root / src / RAbot / reporting / report_jobs.py
    所以 parents[3] 是项目根目录。
    """
    return Path(__file__).resolve().parents[3]


def _default_db_path() -> Path:
    root = _project_root()
    db_dir = root / "data" / "market"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "index_research.db"


DEFAULT_DB_PATH = _default_db_path()


JOB_STATUS_PENDING = "pending"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCESS = "success"
JOB_STATUS_FAILED = "failed"


_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="RAbotReportJob")
_RUNNING_LOCK = threading.Lock()
_RUNNING_JOBS: Dict[str, bool] = {}


@dataclass
class ReportJob:
    job_id: str
    job_type: str
    status: str
    progress: int
    message: str
    created_at: str
    updated_at: str
    finished_at: Optional[str]
    input_json: Dict[str, Any]
    result_json: Optional[Dict[str, Any]]
    error: Optional[str]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _json_loads(text: Optional[str]) -> Any:
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return text


def get_connection(db_path: Optional[Path | str] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_job_store(db_path: Optional[Path | str] = None) -> None:
    """
    初始化后台任务表。
    """
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS report_jobs (
                job_id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                status TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                finished_at TEXT,
                input_json TEXT,
                result_json TEXT,
                error TEXT
            )
            """
        )
        conn.commit()


def create_job(
    job_type: str,
    input_data: Optional[Dict[str, Any]] = None,
    db_path: Optional[Path | str] = None,
) -> str:
    """
    创建一个后台任务，返回 job_id。
    """
    init_job_store(db_path)

    job_id = uuid.uuid4().hex
    now = _now()

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO report_jobs (
                job_id, job_type, status, progress, message,
                created_at, updated_at, finished_at,
                input_json, result_json, error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                job_type,
                JOB_STATUS_PENDING,
                0,
                "任务已创建，等待启动。",
                now,
                now,
                None,
                _json_dumps(input_data or {}),
                None,
                None,
            ),
        )
        conn.commit()

    return job_id


def update_job(
    job_id: str,
    *,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    message: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    finished: bool = False,
    db_path: Optional[Path | str] = None,
) -> None:
    """
    更新任务状态。
    """
    init_job_store(db_path)

    fields: List[str] = []
    values: List[Any] = []

    if status is not None:
        fields.append("status = ?")
        values.append(status)

    if progress is not None:
        progress = max(0, min(100, int(progress)))
        fields.append("progress = ?")
        values.append(progress)

    if message is not None:
        fields.append("message = ?")
        values.append(message)

    if result is not None:
        fields.append("result_json = ?")
        values.append(_json_dumps(result))

    if error is not None:
        fields.append("error = ?")
        values.append(error)

    fields.append("updated_at = ?")
    values.append(_now())

    if finished:
        fields.append("finished_at = ?")
        values.append(_now())

    if not fields:
        return

    values.append(job_id)

    sql = f"""
        UPDATE report_jobs
        SET {", ".join(fields)}
        WHERE job_id = ?
    """

    with get_connection(db_path) as conn:
        conn.execute(sql, values)
        conn.commit()


def set_progress(
    job_id: str,
    progress: int,
    message: str = "",
    db_path: Optional[Path | str] = None,
) -> None:
    """
    给耗时函数使用的进度回调。
    """
    update_job(
        job_id,
        progress=progress,
        message=message,
        db_path=db_path,
    )


def get_job(
    job_id: str,
    db_path: Optional[Path | str] = None,
) -> Optional[ReportJob]:
    """
    获取单个任务。
    """
    init_job_store(db_path)

    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT *
            FROM report_jobs
            WHERE job_id = ?
            """,
            (job_id,),
        ).fetchone()

    if row is None:
        return None

    return ReportJob(
        job_id=row["job_id"],
        job_type=row["job_type"],
        status=row["status"],
        progress=int(row["progress"] or 0),
        message=row["message"] or "",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        finished_at=row["finished_at"],
        input_json=_json_loads(row["input_json"]) or {},
        result_json=_json_loads(row["result_json"]),
        error=row["error"],
    )


def list_jobs(
    job_type: Optional[str] = None,
    limit: int = 20,
    db_path: Optional[Path | str] = None,
) -> List[ReportJob]:
    """
    获取最近任务列表。
    """
    init_job_store(db_path)

    with get_connection(db_path) as conn:
        if job_type:
            rows = conn.execute(
                """
                SELECT *
                FROM report_jobs
                WHERE job_type = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (job_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM report_jobs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    jobs: List[ReportJob] = []
    for row in rows:
        jobs.append(
            ReportJob(
                job_id=row["job_id"],
                job_type=row["job_type"],
                status=row["status"],
                progress=int(row["progress"] or 0),
                message=row["message"] or "",
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                finished_at=row["finished_at"],
                input_json=_json_loads(row["input_json"]) or {},
                result_json=_json_loads(row["result_json"]),
                error=row["error"],
            )
        )

    return jobs


def _call_target_with_optional_progress(
    target_func: Callable[..., Any],
    job_id: str,
    args: tuple,
    kwargs: dict,
    db_path: Optional[Path | str] = None,
) -> Any:
    """
    如果 target_func 支持 progress_callback 参数，就自动传入。
    如果不支持，就正常调用。
    """
    signature = inspect.signature(target_func)

    if "progress_callback" in signature.parameters:
        kwargs["progress_callback"] = lambda p, m="": set_progress(
            job_id,
            p,
            m,
            db_path=db_path,
        )

    return target_func(*args, **kwargs)


def _run_job_worker(
    job_id: str,
    target_func: Callable[..., Any],
    args: tuple,
    kwargs: dict,
    db_path: Optional[Path | str] = None,
) -> None:
    """
    后台线程真正执行的 worker。
    """
    try:
        update_job(
            job_id,
            status=JOB_STATUS_RUNNING,
            progress=5,
            message="后台任务已启动。",
            db_path=db_path,
        )

        result = _call_target_with_optional_progress(
            target_func=target_func,
            job_id=job_id,
            args=args,
            kwargs=kwargs,
            db_path=db_path,
        )

        if isinstance(result, dict):
            result_data = result
        else:
            result_data = {"result": result}

        update_job(
            job_id,
            status=JOB_STATUS_SUCCESS,
            progress=100,
            message="任务完成。",
            result=result_data,
            finished=True,
            db_path=db_path,
        )

    except Exception as exc:
        error_text = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )

        update_job(
            job_id,
            status=JOB_STATUS_FAILED,
            progress=100,
            message="任务失败。",
            error=error_text,
            finished=True,
            db_path=db_path,
        )

    finally:
        with _RUNNING_LOCK:
            _RUNNING_JOBS.pop(job_id, None)


def run_job_async(
    job_id: str,
    target_func: Callable[..., Any],
    *args: Any,
    db_path: Optional[Path | str] = None,
    **kwargs: Any,
) -> bool:
    """
    异步启动任务。

    返回：
    - True：成功提交到后台线程。
    - False：任务已在运行中，避免重复提交。
    """
    init_job_store(db_path)

    with _RUNNING_LOCK:
        if _RUNNING_JOBS.get(job_id):
            return False
        _RUNNING_JOBS[job_id] = True

    update_job(
        job_id,
        status=JOB_STATUS_PENDING,
        progress=1,
        message="任务已提交到后台线程。",
        db_path=db_path,
    )

    _EXECUTOR.submit(
        _run_job_worker,
        job_id,
        target_func,
        args,
        kwargs,
        db_path,
    )

    return True


def is_job_running_in_memory(job_id: str) -> bool:
    """
    判断当前 Python 进程内是否有这个任务在跑。
    注意：
    如果 Streamlit 进程被重启，内存状态会丢失，但 SQLite 里的任务记录还在。
    """
    with _RUNNING_LOCK:
        return bool(_RUNNING_JOBS.get(job_id))


def clear_old_jobs(
    keep_latest: int = 50,
    db_path: Optional[Path | str] = None,
) -> int:
    """
    清理旧任务，只保留最近 keep_latest 条。
    """
    init_job_store(db_path)

    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT job_id
            FROM report_jobs
            ORDER BY created_at DESC
            LIMIT -1 OFFSET ?
            """,
            (keep_latest,),
        ).fetchall()

        old_ids = [row["job_id"] for row in rows]

        if not old_ids:
            return 0

        conn.executemany(
            """
            DELETE FROM report_jobs
            WHERE job_id = ?
            """,
            [(job_id,) for job_id in old_ids],
        )
        conn.commit()

    return len(old_ids)