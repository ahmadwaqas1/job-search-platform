import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useApplications } from "@/features/applications/api";
import { useMatches } from "@/features/matching/api";
import { useProfile } from "@/features/profile/api";

export function DashboardPage() {
  const { data: profile } = useProfile();
  const { data: matches } = useMatches(70);
  const { data: applications } = useApplications();

  const applied = applications?.filter((a) => a.status !== "saved").length ?? 0;
  const profileComplete = !!profile?.full_name && !!profile?.summary && (profile?.skills.length ?? 0) > 0;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Welcome back{profile?.full_name ? `, ${profile.full_name.split(" ")[0]}` : ""}</h1>
        <p className="text-muted-foreground">Here's where your job search stands.</p>
      </div>

      {!profileComplete && (
        <Card className="border-primary/40 bg-primary/5">
          <CardContent className="flex items-center justify-between py-4">
            <div>
              <p className="font-medium">Finish setting up your profile</p>
              <p className="text-sm text-muted-foreground">
                Upload a CV or fill in your experience so Smart Match and Auto-Apply have something to work with.
              </p>
            </div>
            <Link to="/profile" className={buttonVariants({})}>
              Go to Profile
            </Link>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Strong matches</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{matches?.length ?? "–"}</p>
            <p className="text-sm text-muted-foreground">score 70+ waiting for review</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Applications tracked</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{applications?.length ?? "–"}</p>
            <p className="text-sm text-muted-foreground">{applied} moved past "saved"</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Profile status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={profile?.has_embedding ? "success" : "outline"}>
              {profile?.has_embedding ? "Ready for matching" : "Needs skills/experience"}
            </Badge>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Top matches right now</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {(matches ?? []).slice(0, 5).map((m) => (
            <Link
              key={m.id}
              to={`/jobs/${m.job_posting_id}`}
              className="flex items-center justify-between rounded-md border border-border p-3 text-sm hover:bg-accent"
            >
              <div>
                <p className="font-medium">{m.job_posting.title}</p>
                <p className="text-muted-foreground">
                  {m.job_posting.company} · {m.job_posting.location}
                </p>
              </div>
              <Badge>{Math.round(m.llm_score ?? m.similarity_score * 100)}% match</Badge>
            </Link>
          ))}
          {matches?.length === 0 && (
            <p className="py-6 text-center text-sm text-muted-foreground">
              No strong matches yet. Add job sources in Settings and complete your profile to get started.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
