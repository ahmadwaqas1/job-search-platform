import { CheckCircle2, FileText, UploadCloud, XCircle } from "lucide-react";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useCVDocument, useUploadCV } from "@/features/profile/api";
import { toast } from "@/store/toastStore";

export function CVUpload({ onExtracted }: { onExtracted: (parsed: Record<string, unknown>) => void }) {
  const upload = useUploadCV();
  const [documentId, setDocumentId] = useState<string | null>(null);
  const { data: doc } = useCVDocument(documentId);

  const onDrop = useCallback(
    (accepted: File[]) => {
      const file = accepted[0];
      if (!file) return;
      upload.mutate(file, {
        onSuccess: (created) => setDocumentId(created.id),
        onError: () => toast({ title: "Upload failed", variant: "destructive" }),
      });
    },
    [upload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
    maxFiles: 1,
  });

  return (
    <div className="flex flex-col gap-3">
      <div
        {...getRootProps()}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-6 text-center transition-colors ${
          isDragActive ? "border-primary bg-primary/5" : "border-border hover:bg-accent"
        }`}
      >
        <input {...getInputProps()} />
        <UploadCloud className="h-6 w-6 text-muted-foreground" />
        <p className="text-sm">
          <span className="font-medium text-primary">Upload your CV</span> (PDF, DOCX, or TXT) and we'll pull out your
          experience, education, and skills automatically.
        </p>
      </div>

      {upload.isPending && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Spinner /> Uploading...
        </div>
      )}

      {doc && (
        <div className="flex items-center justify-between rounded-md border border-border p-3">
          <div className="flex items-center gap-2 text-sm">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span>{doc.original_filename}</span>
            <StatusBadge status={doc.parse_status} />
          </div>
          {doc.parse_status === "parsed" && doc.parsed_json && (
            <Button size="sm" onClick={() => onExtracted(doc.parsed_json as Record<string, unknown>)}>
              Use this data
            </Button>
          )}
        </div>
      )}
      {doc?.parse_status === "failed" && <p className="text-xs text-destructive">{doc.parse_error}</p>}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "parsed") return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
  if (status === "failed") return <XCircle className="h-4 w-4 text-destructive" />;
  return <Spinner className="h-3.5 w-3.5" />;
}
