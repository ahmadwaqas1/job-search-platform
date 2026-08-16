import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  useCreateJobSource,
  useDeleteJobSource,
  useJobSources,
  usePollSourceNow,
  useSetSourceActive,
} from "@/features/jobs/api";
import { useEffectiveSettings } from "@/features/settings/api";
import { toast } from "@/store/toastStore";

const SOURCE_TYPES = [
  { value: "custom_rss", label: "RSS/Atom feed (regional job board)" },
  { value: "greenhouse", label: "Greenhouse company board" },
  { value: "lever", label: "Lever company board" },
];

export function SettingsPage() {
  const { data: settings } = useEffectiveSettings();
  const { data: sources } = useJobSources();
  const createSource = useCreateJobSource();
  const setActive = useSetSourceActive();
  const deleteSource = useDeleteJobSource();
  const pollNow = usePollSourceNow();

  const [type, setType] = useState("custom_rss");
  const [name, setName] = useState("");
  const [value, setValue] = useState("");

  const configKey = type === "custom_rss" ? "feed_url" : "board_token";

  const addSource = () => {
    if (!name || !value) return;
    const config = type === "lever" ? { company: value } : { [configKey]: value };
    createSource.mutate(
      { type, name, config, poll_interval_minutes: 60 },
      {
        onSuccess: () => {
          setName("");
          setValue("");
          toast({ title: "Source added", variant: "success" });
        },
        onError: () => toast({ title: "Failed to add source", variant: "destructive" }),
      }
    );
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-muted-foreground">Manage job sources and see what's configured on the server.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Server configuration</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <ConfigStat label="Chat model" value={settings?.ollama_chat_model} />
          <ConfigStat label="Embedding model" value={settings?.ollama_embed_model} />
          <ConfigStat label="Adzuna" ok={settings?.adzuna_configured} />
          <ConfigStat label="USAJobs" ok={settings?.usajobs_configured} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Add a job source</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="text-sm text-muted-foreground">
            Beyond the built-in sources (Remotive, RemoteOK, Arbeitnow, The Muse), add any company's Greenhouse/Lever board
            or a regional job board's RSS feed.
          </p>
          <div className="grid grid-cols-3 gap-2">
            <Select value={type} onChange={(e) => setType(e.target.value)}>
              {SOURCE_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </Select>
            <Input placeholder="Display name" value={name} onChange={(e) => setName(e.target.value)} />
            <Input
              placeholder={type === "custom_rss" ? "https://example.com/jobs.rss" : "company-slug"}
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
          </div>
          <Button className="w-fit" onClick={addSource} disabled={createSource.isPending}>
            Add source
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Job sources</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col divide-y divide-border">
          {sources?.map((s) => (
            <div key={s.id} className="flex items-center justify-between py-2">
              <div>
                <p className="text-sm font-medium">{s.name}</p>
                <p className="text-xs text-muted-foreground">
                  {s.type} · every {s.poll_interval_minutes}min ·{" "}
                  {s.last_polled_at ? `last polled ${new Date(s.last_polled_at).toLocaleString()}` : "never polled"}
                  {s.last_poll_status === "error" && <span className="text-destructive"> · error</span>}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={s.is_active ? "success" : "outline"}>{s.is_active ? "Active" : "Paused"}</Badge>
                <Button size="sm" variant="outline" onClick={() => pollNow.mutate(s.id)}>
                  Poll now
                </Button>
                <Button size="sm" variant="outline" onClick={() => setActive.mutate({ id: s.id, isActive: !s.is_active })}>
                  {s.is_active ? "Pause" : "Resume"}
                </Button>
                {s.user_id !== null && (
                  <Button size="sm" variant="ghost" className="text-destructive" onClick={() => deleteSource.mutate(s.id)}>
                    Delete
                  </Button>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function ConfigStat({ label, value, ok }: { label: string; value?: string; ok?: boolean }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      {value !== undefined ? (
        <p className="font-mono text-sm">{value}</p>
      ) : (
        <Badge variant={ok ? "success" : "outline"}>{ok ? "Configured" : "Not configured"}</Badge>
      )}
    </div>
  );
}
