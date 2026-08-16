import { ExternalLink } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCreateApplication } from "@/features/applications/api";
import { useJob } from "@/features/jobs/api";
import { useMatch } from "@/features/matching/api";
import { toast } from "@/store/toastStore";

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: job, isLoading } = useJob(id);
  const { data: match } = useMatch(id);
  const createApplication = useCreateApplication();

  if (isLoading || !job) return <p className="text-muted-foreground">Loading...</p>;

  const score = match ? (match.llm_score ?? match.similarity_score * 100) : null;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">{job.title}</h1>
        <p className="text-muted-foreground">
          {job.company} · {job.location}
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge variant="secondary">{job.remote_type}</Badge>
          {job.salary_min && (
            <Badge variant="outline">
              {job.salary_currency} {job.salary_min.toLocaleString()}
              {job.salary_max ? `–${job.salary_max.toLocaleString()}` : ""} / {job.salary_period}
            </Badge>
          )}
          {job.tags.slice(0, 6).map((t) => (
            <Badge key={t} variant="outline">
              {t}
            </Badge>
          ))}
        </div>
      </div>

      <div className="flex gap-2">
        <Button
          disabled={createApplication.isPending}
          onClick={() =>
            createApplication.mutate(
              { job_posting_id: job.id, match_id: match?.id },
              {
                onSuccess: (app) => {
                  toast({ title: "Draft started", description: "Generating a tailored resume and cover letter...", variant: "success" });
                  navigate(`/applications/${app.id}`);
                },
              }
            )
          }
        >
          Start application draft
        </Button>
        {job.url && (
          <Button variant="outline" onClick={() => window.open(job.url, "_blank", "noopener,noreferrer")}>
            View original posting <ExternalLink className="h-3.5 w-3.5" />
          </Button>
        )}
      </div>

      {match && (
        <Card className="border-primary/30 bg-primary/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Match score: {score !== null ? Math.round(score) : "–"}%
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {match.explanation_text && <p className="text-sm">{match.explanation_text}</p>}
            <div className="flex gap-6">
              {match.matched_skills.length > 0 && (
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">You have</p>
                  <div className="flex flex-wrap gap-1">
                    {match.matched_skills.map((s) => (
                      <Badge key={s} variant="success">
                        {s}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {match.missing_skills.length > 0 && (
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">Gaps</p>
                  <div className="flex flex-wrap gap-1">
                    {match.missing_skills.map((s) => (
                      <Badge key={s} variant="outline">
                        {s}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Job description</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-line text-sm leading-relaxed">{job.description_text}</p>
        </CardContent>
      </Card>
    </div>
  );
}
