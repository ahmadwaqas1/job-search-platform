import { DndContext, type DragEndEvent, useDraggable, useDroppable } from "@dnd-kit/core";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { useApplications, useUpdateApplicationStatus } from "@/features/applications/api";
import type { Application, ApplicationStatus } from "@/api/types";
import { cn } from "@/lib/utils";

const COLUMNS: { status: ApplicationStatus; label: string }[] = [
  { status: "saved", label: "Saved" },
  { status: "applied", label: "Applied" },
  { status: "interviewing", label: "Interviewing" },
  { status: "offer", label: "Offer" },
  { status: "rejected", label: "Rejected" },
  { status: "withdrawn", label: "Withdrawn" },
];

export function ApplicationsPage() {
  const { data: applications } = useApplications();
  const updateStatus = useUpdateApplicationStatus();

  const onDragEnd = (event: DragEndEvent) => {
    const appId = event.active.id as string;
    const newStatus = event.over?.id as ApplicationStatus | undefined;
    const app = applications?.find((a) => a.id === appId);
    if (!newStatus || !app || app.status === newStatus) return;
    updateStatus.mutate({ id: appId, status: newStatus });
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Applications</h1>
        <p className="text-muted-foreground">Drag cards between columns as your applications move forward.</p>
      </div>

      <DndContext onDragEnd={onDragEnd}>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {COLUMNS.map((col) => (
            <Column key={col.status} status={col.status} label={col.label} applications={(applications ?? []).filter((a) => a.status === col.status)} />
          ))}
        </div>
      </DndContext>
    </div>
  );
}

function Column({ status, label, applications }: { status: ApplicationStatus; label: string; applications: Application[] }) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  return (
    <div
      ref={setNodeRef}
      className={cn("flex w-64 flex-shrink-0 flex-col gap-2 rounded-lg border border-border bg-muted/30 p-2", isOver && "bg-primary/5 ring-1 ring-primary")}
    >
      <div className="flex items-center justify-between px-1 py-1">
        <span className="text-sm font-semibold">{label}</span>
        <Badge variant="secondary">{applications.length}</Badge>
      </div>
      <div className="flex flex-col gap-2">
        {applications.map((a) => (
          <ApplicationCard key={a.id} application={a} />
        ))}
      </div>
    </div>
  );
}

function ApplicationCard({ application }: { application: Application }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({ id: application.id });
  const style = transform ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` } : undefined;

  return (
    <div ref={setNodeRef} style={style} {...listeners} {...attributes} className={cn("touch-none", isDragging && "z-10 opacity-70")}>
      <Link to={`/applications/${application.id}`} onClick={(e) => isDragging && e.preventDefault()}>
        <Card className="cursor-grab active:cursor-grabbing hover:bg-accent">
          <CardContent className="p-3">
            <p className="text-sm font-medium leading-tight">{application.job_posting.title}</p>
            <p className="text-xs text-muted-foreground">{application.job_posting.company}</p>
            {application.draft_status === "generating" && (
              <Badge variant="outline" className="mt-2">
                Drafting...
              </Badge>
            )}
          </CardContent>
        </Card>
      </Link>
    </div>
  );
}
