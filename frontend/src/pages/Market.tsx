import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useSalaryInsights, useSalarySuggestions } from "@/features/salary/api";

const SOURCE_LABEL: Record<string, string> = {
  aggregated_postings: "From ingested job postings",
  adzuna: "Adzuna live estimate",
  bls: "US Bureau of Labor Statistics",
  usajobs: "USAJobs",
};

export function MarketPage() {
  const { data: suggestions } = useSalarySuggestions();
  const [role, setRole] = useState("Software Engineer");
  const [location, setLocation] = useState("Remote");
  const { data: snapshots, isLoading } = useSalaryInsights(role, location);

  const chartData = (snapshots ?? [])
    .filter((s) => s.median !== null)
    .map((s) => ({
      source: SOURCE_LABEL[s.source] ?? s.source,
      p10: s.p10 ?? 0,
      median: s.median ?? 0,
      p90: s.p90 ?? 0,
      sample_size: s.sample_size,
    }));

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Market Insights</h1>
        <p className="text-muted-foreground">Salary ranges pulled from live job data and public wage sources.</p>
      </div>

      <div className="flex gap-2">
        <Select value={role} onChange={(e) => setRole(e.target.value)} className="w-64">
          {(suggestions?.roles ?? [role]).map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </Select>
        <Select value={location} onChange={(e) => setLocation(e.target.value)} className="w-48">
          {(suggestions?.locations ?? [location]).map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </Select>
        <Input placeholder="Or type a custom role" onBlur={(e) => e.target.value && setRole(e.target.value)} className="w-56" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {role} · {location}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && <p className="text-muted-foreground">Loading...</p>}
          {!isLoading && chartData.length === 0 && (
            <p className="text-muted-foreground">
              No salary data yet for this role/location. As more jobs are ingested with salary info, this will fill in.
            </p>
          )}
          {chartData.length > 0 && (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ left: 8, right: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="source" tick={{ fontSize: 11 }} />
                  <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v: number) => `$${v.toLocaleString()}`} />
                  <Bar dataKey="p10" stackId="range" fill="hsl(var(--muted-foreground))" fillOpacity={0.25} name="P10" />
                  <Bar dataKey="median" fill="hsl(var(--primary))" name="Median" />
                  <Bar dataKey="p90" fillOpacity={0.4} fill="hsl(var(--primary))" name="P90" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {(snapshots ?? []).map((s) => (
          <Card key={s.source}>
            <CardContent className="py-4">
              <p className="text-xs font-medium text-muted-foreground">{SOURCE_LABEL[s.source] ?? s.source}</p>
              <p className="mt-1 text-xl font-semibold">{s.median ? `$${Math.round(s.median).toLocaleString()}` : "–"}</p>
              <p className="text-xs text-muted-foreground">
                {s.p10 && s.p90 ? `$${Math.round(s.p10).toLocaleString()} – $${Math.round(s.p90).toLocaleString()}` : "range unavailable"}
                {s.sample_size > 0 ? ` · n=${s.sample_size}` : ""}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
