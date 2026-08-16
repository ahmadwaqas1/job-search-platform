import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { CVUpload } from "@/features/profile/CVUpload";
import { mapExtractedToFormValues } from "@/features/profile/extractedToForm";
import { EMPTY_PROFILE, type ProfileFormValues } from "@/features/profile/formTypes";
import { ProfileForm } from "@/features/profile/ProfileForm";
import { useDownloadCV, useProfile, useSaveProfile } from "@/features/profile/api";
import { toast } from "@/store/toastStore";

function toFormValues(profile: NonNullable<ReturnType<typeof useProfile>["data"]>): ProfileFormValues {
  const { id: _id, has_embedding: _he, ...rest } = profile;
  return rest;
}

export function ProfilePage() {
  const { data: profile, isLoading } = useProfile();
  const saveProfile = useSaveProfile();
  const downloadCV = useDownloadCV();
  const [template, setTemplate] = useState<"modern" | "classic">("modern");
  const [pendingValues, setPendingValues] = useState<ProfileFormValues | null>(null);
  const [resetSignal, setResetSignal] = useState(0);

  const defaultValues = useMemo(
    () => pendingValues ?? (profile ? toFormValues(profile) : EMPTY_PROFILE),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [profile, resetSignal]
  );

  if (isLoading) return <p className="text-muted-foreground">Loading profile...</p>;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Profile & CV</h1>
          <p className="text-muted-foreground">
            This is the single source of truth used for Smart Match and your downloadable resume.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={template} onChange={(e) => setTemplate(e.target.value as "modern" | "classic")} className="w-32">
            <option value="modern">Modern</option>
            <option value="classic">Classic</option>
          </Select>
          <Button variant="outline" disabled={downloadCV.isPending} onClick={() => downloadCV.mutate(template)}>
            Download PDF
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Import from an existing CV</CardTitle>
        </CardHeader>
        <CardContent>
          <CVUpload
            onExtracted={(parsed) => {
              const base = pendingValues ?? (profile ? toFormValues(profile) : EMPTY_PROFILE);
              setPendingValues(mapExtractedToFormValues(parsed, base));
              setResetSignal((n) => n + 1);
              toast({ title: "CV data loaded", description: "Review the fields below, then save.", variant: "success" });
            }}
          />
        </CardContent>
      </Card>

      <ProfileForm
        key={profile?.id}
        defaultValues={defaultValues}
        resetSignal={resetSignal}
        isSaving={saveProfile.isPending}
        onSubmit={(values) => {
          saveProfile.mutate(values, {
            onSuccess: () => {
              setPendingValues(null);
              toast({ title: "Profile saved", description: "Re-matching your jobs in the background.", variant: "success" });
            },
            onError: () => toast({ title: "Failed to save profile", variant: "destructive" }),
          });
        }}
      />
    </div>
  );
}
