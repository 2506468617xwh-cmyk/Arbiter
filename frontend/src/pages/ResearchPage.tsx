import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchReport,
  fetchTask,
  fetchTaskResult,
  generateResearchReport,
  ReportContentResponse,
  ResearchGenerateRequest,
  TaskResponse
} from "../api/client";
import ReportReader from "../components/ReportReader";
import ResearchForm from "../components/ResearchForm";
import ResearchPet from "../components/ResearchPet";
import TaskStatusCard from "../components/TaskStatusCard";
import { useI18n } from "../i18n";

function getFilename(result: Record<string, unknown> | null): string | null {
  if (!result) {
    return null;
  }
  const value = result.filename;
  return typeof value === "string" ? value : null;
}

interface ResearchPageProps {
  defaultUseLlm: boolean;
}

function ResearchPage({ defaultUseLlm }: ResearchPageProps) {
  const { language, page } = useI18n();
  const [submitting, setSubmitting] = useState(false);
  const [task, setTask] = useState<TaskResponse | null>(null);
  const [report, setReport] = useState<ReportContentResponse | null>(null);
  const [readerLoading, setReaderLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [readerError, setReaderError] = useState<string | null>(null);
  const loadedReportForTask = useRef<string | null>(null);
  const isEn = language === "en";

  const loadGeneratedReport = useCallback(async (taskId: string) => {
    if (loadedReportForTask.current === taskId) {
      return;
    }
    loadedReportForTask.current = taskId;
    setReaderLoading(true);
    setReaderError(null);
    try {
      const result = await fetchTaskResult(taskId);
      const filename = getFilename(result.result);
      if (!filename) {
        throw new Error(isEn ? "The task finished, but no report filename was returned." : "任务已完成，但结果中没有报告文件名。");
      }
      setReport(await fetchReport(filename));
    } catch (exc) {
      loadedReportForTask.current = null;
      setReaderError(exc instanceof Error ? exc.message : (isEn ? "Failed to read report." : "报告读取失败。"));
    } finally {
      setReaderLoading(false);
    }
  }, [isEn]);

  const handleSubmit = useCallback(async (payload: ResearchGenerateRequest) => {
    setSubmitting(true);
    setError(null);
    setReport(null);
    setReaderError(null);
    loadedReportForTask.current = null;
    try {
      const response = await generateResearchReport(payload);
      const firstTask = await fetchTask(response.task_id);
      setTask(firstTask);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : (isEn ? "Failed to submit report task." : "研究报告任务提交失败。"));
    } finally {
      setSubmitting(false);
    }
  }, [isEn]);

  useEffect(() => {
    if (!task || task.status === "success" || task.status === "failed" || task.status === "cancelled") {
      if (task?.status === "success") {
        void loadGeneratedReport(task.task_id);
      }
      return;
    }

    const timer = window.setInterval(async () => {
      try {
        const nextTask = await fetchTask(task.task_id);
        setTask(nextTask);
        if (nextTask.status === "success") {
          window.clearInterval(timer);
          void loadGeneratedReport(nextTask.task_id);
        }
        if (nextTask.status === "failed" || nextTask.status === "cancelled") {
          window.clearInterval(timer);
        }
      } catch (exc) {
        setError(exc instanceof Error ? exc.message : (isEn ? "Failed to read task status." : "任务状态读取失败。"));
        window.clearInterval(timer);
      }
    }, 1500);

    return () => window.clearInterval(timer);
  }, [task, loadGeneratedReport, isEn]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-medium text-brand">{page.research.eyebrow}</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink">{page.research.title}</h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-muted">{page.research.subtitle}</p>
        </div>
        <ResearchPet
          pageName="research"
          useLlm={defaultUseLlm}
          context={{
            title: page.research.title,
            subtitle: page.research.subtitle,
            current_task: task?.current_step,
            task_status: task?.status,
            report_title: report?.title
          }}
        />
      </div>

      {error ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {error}
        </div>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-[380px_1fr]">
        <ResearchForm submitting={submitting || task?.status === "running"} defaultUseLlm={defaultUseLlm} onSubmit={handleSubmit} />
        <TaskStatusCard task={task} />
      </div>

      {task?.status === "success" ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          {isEn ? "The report has been generated and is shown below." : "报告已生成，正在下方展示最新内容。"}
        </div>
      ) : null}

      <ReportReader report={report} loading={readerLoading} error={readerError} />
    </div>
  );
}

export default ResearchPage;
