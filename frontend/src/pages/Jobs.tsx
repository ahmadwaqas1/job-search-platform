import { useState } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useJobs } from "@/features/jobs/api";
import { useMatches, useRefreshMatches } from "@/features/matching/api";

export function JobsPage() {
  const [q, setQ] = useState("");
  const [location, setLocation] = useState("");
  const [remoteType, setRemoteType] = useState("");
  const [view, setView] = useState<"matches" | "browse">("matches");

  const { data: matches, isLoading: matchesLoading } = useMatches();
  const { data: jobs, isLoading: jobsLoading } = useJobs({ q: q || undefined, location: location || undefined, remote_type: remoteType || undefined });
  const refresh = useRefreshMatches();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Smart Match</h1>
          <p className="text-muted-foreground">AI-ranked jobs from every connected source.</p>
        </div>
        <Button variant="outline" onClick={() => refresh.mutate()} disabled={refresh.isPending}>
          Refresh my matches
        </Button>
      </div>

      <div className="flex gap-2 border-b border-border">
        <button
          className={`border-b-2 px-3 py-2 text-sm font-medium ${view === "matches" ? "border-primary text-primary" : "border-transparent text-muted-foreground"}`}
          onClick={() => setView("matches")}
        >
          Your matches
        </button>
        <button
          className={`border-b-2 px-3 py-2 text-sm font-medium ${view === "browse" ? "border-primary text-primary" : "border-transparent text-muted-foreground"}`}
          onClick={() => setView("browse")}
        >
          Browse all jobs
        </button>
      </div>

      {view === "browse" && (
        <div className="flex gap-2">
          <Input placeholder="Search title or company" value={q} onChange={(e) => setQ(e.target.value)} />
          <Input placeholder="Location" value={location} onChange={(e) => setLocation(e.target.value)} className="w-48" />
          <Select value={remoteType} onChange={(e) => setRemoteType(e.target.value)} className="w-36">
            <option value="">Any type</option>
            <option value="remote">Remote</option>
            <option value="hybrid">Hybrid</option>
            <option value="onsite">Onsite</option>
          </Select>
        </div>
      )}

      {view === "matches" ? (
        <div className="flex flex-col gap-3">
          {matchesLoading && <p className="text-muted-foreground">Loading matches...</p>}
          {matches?.map((m) => (
            <JobCard
              key={m.id}
              id={m.job_posting_id}
              title={m.job_posting.title}
              company={m.job_posting.company}
              location={m.job_posting.location}
              remoteType={m.job_posting.remote_type}
              score={m.llm_score !== null ? Math.round(m.llm_score) : Math.round(m.similarity_score * 100)}
              explanation={m.explanation_text}
            />
          ))}
          {matches?.length === 0 && !matchesLoading && (
            <Card>
              <CardContent className="py-10 text-center text-muted-foreground">
                No matches yet. Make sure your profile has skills/experience saved and job sources are active in Settings -
                matching runs automatically in the background once both are ready.
              </CardContent>
            </Card>
          )}
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {jobsLoading && <p className="text-muted-foreground">Loading jobs...</p>}
          {jobs?.map((j) => (
            <JobCard key={j.id} id={j.id} title={j.title} company={j.company} location={j.location} remoteType={j.remote_type} />
          ))}
        </div>
      )}
    </div>
  );
}

function JobCard({
  id,
  title,
  company,
  location,
  remoteType,
  score,
  explanation,
}: {
  id: string;
  title: string;
  company: string;
  location: string;
  remoteType: string;
  score?: number;
  explanation?: string;
}) {
  return (
    <Link to={`/jobs/${id}`}>
      <Card className="transition-colors hover:bg-accent">
        <CardContent className="flex items-start justify-between gap-4 py-4">
          <div>
            <p className="font-medium">{title}</p>
            <p className="text-sm text-muted-foreground">
              {company} · {location}
            </p>
            {explanation && <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{explanation}</p>}
          </div>
          <div className="flex flex-shrink-0 flex-col items-end gap-1">
            {score !== undefined && <Badge variant={score >= 70 ? "success" : "outline"}>{score}% match</Badge>}
            <Badge variant="secondary">{remoteType}</Badge>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
