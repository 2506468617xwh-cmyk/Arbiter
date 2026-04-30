# src/RAbot/reporting/streamlit_report_jobs.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Optional

import streamlit as st

from RAbot.reporting.report_jobs import (
    JOB_STATUS_FAILED,
    JOB_STATUS_PENDING,
    JOB_STATUS_RUNNING,
    JOB_STATUS_SUCCESS,
    create_job,
    get_job,
    list_jobs,
    run_job_async,
)


def _status_label(status: str) -> str:
    if status == JOB_STATUS_PENDING:
        return "等待中"
    if status == JOB_STATUS_RUNNING:
        return "生成中"
    if status == JOB_STATUS_SUCCESS:
        return "已完成"
    if status == JOB_STATUS_FAILED:
        return "失败"
    return status


def _render_job_result(result_json: Optional[Dict[str, Any]]) -> None:
    if not result_json:
        return

    report_path = (
        result_json.get("report_path")
        or result_json.get("path")
        or result_json.get("file_path")
        or result_json.get("result")
    )

    if report_path:
        path = Path(str(report_path))
        st.success("报告已生成。")

        if path.exists():
            st.code(str(path), language="text")
            try:
                text = path.read_text(encoding="utf-8")
                with st.expander("预览报告内容", expanded=False):
                    st.markdown(text)
            except Exception:
                st.info("报告文件已生成，但当前无法直接预览。")
        else:
            st.code(str(report_path), language="text")
    else:
        with st.expander("查看任务结果", expanded=False):
            st.json(result_json)


def render_job_card(job_id: str) -> None:
    job = get_job(job_id)

    if job is None:
        st.warning("没有找到这个后台任务。")
        return

    status_text = _status_label(job.status)

    st.markdown(f"**任务状态：{status_text}**")
    st.progress(job.progress / 100)
    st.caption(f"{job.progress}% ｜ {job.message}")
    st.caption(f"创建时间：{job.created_at} ｜ 更新时间：{job.updated_at}")

    if job.status == JOB_STATUS_SUCCESS:
        st.toast("LLM 报告已经生成完成。", icon="✅")
        _render_job_result(job.result_json)

    elif job.status == JOB_STATUS_FAILED:
        st.error("报告生成失败。")
        with st.expander("查看错误详情", expanded=False):
            st.code(job.error or "未知错误", language="text")

    elif job.status in {JOB_STATUS_PENDING, JOB_STATUS_RUNNING}:
        st.info("任务正在后台执行。你可以切换到其他板块继续看行情、新闻或宏观数据。")


def render_latest_jobs(job_type: str = "llm_report", limit: int = 5) -> None:
    jobs = list_jobs(job_type=job_type, limit=limit)

    if not jobs:
        st.caption("暂无历史报告任务。")
        return

    with st.expander("最近报告任务", expanded=False):
        for job in jobs:
            st.markdown(
                f"""
                **{_status_label(job.status)}** ｜ `{job.job_id[:8]}`  
                进度：{job.progress}%  
                创建时间：{job.created_at}  
                更新时间：{job.updated_at}
                """
            )
            if job.status == JOB_STATUS_SUCCESS and job.result_json:
                report_path = (
                    job.result_json.get("report_path")
                    or job.result_json.get("path")
                    or job.result_json.get("file_path")
                    or job.result_json.get("result")
                )
                if report_path:
                    st.caption(f"报告路径：{report_path}")

            if job.status == JOB_STATUS_FAILED:
                with st.expander(f"错误详情 {job.job_id[:8]}", expanded=False):
                    st.code(job.error or "未知错误", language="text")

            st.divider()


def render_async_report_button(
    *,
    button_label: str,
    job_type: str,
    input_data: Dict[str, Any],
    target_func: Callable[..., Any],
    target_kwargs: Optional[Dict[str, Any]] = None,
    session_key: str = "current_llm_report_job_id",
) -> None:
    """
    在 Streamlit 里渲染一个异步报告按钮。

    参数说明：
    - button_label：按钮文案，例如“生成 LLM 研究报告”
    - job_type：任务类型，例如 "llm_report"
    - input_data：写入 SQLite 的任务输入信息，方便追踪
    - target_func：你原来那个同步生成报告的函数
    - target_kwargs：传给 target_func 的参数
    - session_key：当前页面保存 job_id 的 session_state key
    """
    target_kwargs = target_kwargs or {}

    col1, col2 = st.columns([1, 1])

    with col1:
        clicked = st.button(button_label, type="primary", use_container_width=True)

    with col2:
        if st.button("刷新任务状态", use_container_width=True):
            st.rerun()

    if clicked:
        job_id = create_job(job_type=job_type, input_data=input_data)
        st.session_state[session_key] = job_id

        submitted = run_job_async(
            job_id,
            target_func,
            **target_kwargs,
        )

        if submitted:
            st.success("报告任务已提交到后台。你可以继续使用其他功能。")
        else:
            st.warning("这个任务已经在运行中。")

    current_job_id = st.session_state.get(session_key)

    if current_job_id:
        st.divider()
        render_job_card(current_job_id)

    st.divider()
    render_latest_jobs(job_type=job_type, limit=5)