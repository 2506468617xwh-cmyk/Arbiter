import { TaskResponse } from "../api/client";
import ProgressBar from "./ProgressBar";

interface TaskStatusCardProps {
  task: TaskResponse | null;
}

function statusText(status: string): string {
  const map: Record<string, string> = {
    pending: "等待中",
    running: "生成中",
    success: "已完成",
    failed: "失败",
    cancelled: "已取消"
  };
  return map[status] ?? status;
}

function TaskStatusCard({ task }: TaskStatusCardProps) {
  if (!task) {
    return (
      <section className="rounded-lg border border-dashed border-line bg-panel p-5 text-sm text-muted">
        提交任务后，这里会显示后台生成进度。
      </section>
    );
  }

  const isFailed = task.status === "failed";
  const isSuccess = task.status === "success";

  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-medium text-brand">任务状态</p>
          <h2 className="mt-1 text-xl font-semibold text-ink">{statusText(task.status)}</h2>
          <p className="mt-2 text-sm leading-6 text-muted">{task.current_step}</p>
        </div>
        <span
          className={
            isSuccess
              ? "rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs text-emerald-800"
              : isFailed
                ? "rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs text-amber-900"
                : "rounded-full border border-line bg-[var(--bg-card)] px-3 py-1 text-xs text-muted"
          }
        >
          {statusText(task.status)}
        </span>
      </div>

      <div className="mt-5">
        <ProgressBar value={task.progress} />
      </div>

      <dl className="mt-5 grid gap-3 text-xs text-muted md:grid-cols-3">
        <div>
          <dt className="font-medium text-ink">创建时间</dt>
          <dd className="mt-1">{new Date(task.created_at).toLocaleString()}</dd>
        </div>
        <div>
          <dt className="font-medium text-ink">开始时间</dt>
          <dd className="mt-1">{task.started_at ? new Date(task.started_at).toLocaleString() : "未开始"}</dd>
        </div>
        <div>
          <dt className="font-medium text-ink">完成时间</dt>
          <dd className="mt-1">{task.finished_at ? new Date(task.finished_at).toLocaleString() : "未完成"}</dd>
        </div>
      </dl>

      <p className="mt-4 text-sm leading-6 text-muted">{task.message}</p>
      {task.error ? (
        <pre className="mt-4 max-h-48 overflow-auto whitespace-pre-wrap rounded-md border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
          {task.error}
        </pre>
      ) : null}
    </section>
  );
}

export default TaskStatusCard;
