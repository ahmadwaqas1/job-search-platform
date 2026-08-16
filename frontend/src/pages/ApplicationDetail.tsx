import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import {
  useApplication,
  useDownloadTailoredResume,
  useEditApplication,
  useRegenerateDraft,
  useUpdateApplicationStatus,
} from "@/features/applications/api";
import type { ApplicationStatus } from "@/api/types";
import { toast } from "@/store/toastStore";

const STATUSES: ApplicationStatus[] = ["saved", "applied", "interviewing", "offer", "rejected", "withdrawn"];

export function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: app } = useApplication(id);
  const editApp = useEditApplication();
  const updateStatus = useUpdateApplicationStatus();
  const regenerate = useRegenerateDraft();
  const downloadResume = useDownloadTailoredResume();

  const [coverLetter, setCoverLetter] = useState("");
  const [answers, setAnswers] = useState<{ question: string; answer: string }[]>([]);

  useEffect(() => {
    if (app) {
      setCoverLetter(app.cover_letter_text);
      setAnswers(app.application_answers);
    }
  }, [app?.id, app?.draft_status]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!app || !id) return <p className="text-muted-foreground">Loading...</p>;

  const saveEdits = () => {
    editApp.mutate(
      { id, cover_letter_text: coverLetter, application_answers: answers },
      { onSuccess: () => toast({ title: "Saved", variant: "success" }) }
    );
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{app.job_posting.title}</h1>
          <p className="text-muted-foreground">
            {app.job_posting.company} · {app.job_posting.location}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Label className="text-xs">Status</Label>
          <Select
            value={app.status}
            onChange={(e) => updateStatus.mutate({ id, status: e.target.value as ApplicationStatus })}
            className="w-40"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s[0].toUpperCase() + s.slice(1)}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {app.draft_status === "generating" && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="flex items-center gap-2 py-4 text-sm">
            <Spinner /> Drafting a tailored resume, cover letter, and answers with your local LLM...
          </CardContent>
        </Card>
      )}
      {app.draft_status === "failed" && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="flex items-center justify-between py-4">
            <p className="text-sm">Draft generation failed.</p>
            <Button size="sm" onClick={() => regenerate.mutate(id)}>
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {app.draft_status === "ready" && (
        <>
          <Card className="border-amber-500/30 bg-amber-500/5">
            <CardContent className="py-3 text-sm">
              This is a <strong>draft</strong>, written by AI from your real profile data. Review it carefully, then submit
              the application yourself on the employer's site - nothing here gets sent automatically.
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle>Tailored resume</CardTitle>
              <Button variant="outline" size="sm" onClick={() => downloadResume.mutate(id)} disabled={downloadResume.isPending}>
                Download PDF
              </Button>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Cover letter</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea rows={12} value={coverLetter} onChange={(e) => setCoverLetter(e.target.value)} />
            </CardContent>
          </Card>

          {answers.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Draft answers to common questions</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                {answers.map((a, i) => (
                  <div key={i} className="flex flex-col gap-1">
                    <Label>{a.question}</Label>
                    <Textarea
                      rows={2}
                      value={a.answer}
                      onChange={(e) => {
                        const next = [...answers];
                        next[i] = { ...next[i], answer: e.target.value };
                        setAnswers(next);
                      }}
                    />
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => regenerate.mutate(id)} disabled={regenerate.isPending}>
              Regenerate draft
            </Button>
            <Button onClick={saveEdits} disabled={editApp.isPending}>
              Save edits
            </Button>
          </div>
        </>
      )}

      {app.events.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">History</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {app.events.map((e) => (
              <div key={e.id} className="flex items-center gap-2 text-xs text-muted-foreground">
                <Badge variant="outline">{e.to_status || e.event_type}</Badge>
                {new Date(e.created_at).toLocaleString()}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
