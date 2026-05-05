"""报告库 — 研究报告浏览与管理"""
from __future__ import annotations

import streamlit as st

from streamlit.utils import ROOT
import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def render() -> None:
    st.title("📚 报告库")

    try:
        from backend.services.report_service import list_reports, get_report, get_latest_report, delete_report
    except Exception as exc:
        st.error(f"无法加载报告模块：{exc}")
        return

    # ── 报告列表 ──
    with st.spinner("加载报告列表..."):
        try:
            reports_list = list_reports()
        except Exception as exc:
            st.error(f"加载失败：{exc}")
            return

    if not reports_list.reports:
        st.info("报告库为空。前往「研究生成」页面创建第一份报告。")
        return

    # ── 左侧：报告列表 ──
    c1, c2 = st.columns([1, 2])

    with c1:
        st.subheader(f"共 {len(reports_list.reports)} 份报告")

        selected_file = st.selectbox(
            "选择报告",
            options=[r.filename for r in reports_list.reports],
            format_func=lambda f: next((r.title for r in reports_list.reports if r.filename == f), f),
        )

        if st.button("📄 查看最新报告", use_container_width=True):
            try:
                latest = get_latest_report()
                selected_file = latest.filename
                st.rerun()
            except Exception:
                st.warning("暂无最新报告")

    # ── 右侧：报告内容 ──
    with c2:
        if selected_file:
            with st.spinner("加载报告..."):
                try:
                    report = get_report(selected_file)
                except Exception as exc:
                    st.error(f"加载失败：{exc}")
                    report = None

            if report:
                st.subheader(report.title or report.filename)
                meta_parts = [
                    f"📅 {report.updated_at}",
                    f"📦 {_format_size(report.size_bytes)}",
                ]
                st.caption("  |  ".join(meta_parts))

                st.markdown("---")
                st.markdown(report.content)

                # 删除按钮
                with st.expander("🗑️ 删除此报告"):
                    if st.button("确认删除", type="secondary"):
                        try:
                            delete_result = delete_report(selected_file)
                            if delete_result.deleted:
                                st.success(delete_result.message)
                                st.rerun()
                            else:
                                st.error(delete_result.message)
                        except Exception as exc:
                            st.error(f"删除失败：{exc}")
