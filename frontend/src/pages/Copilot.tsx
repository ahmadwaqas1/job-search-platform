import { Bot, Plus, Send, Trash2, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { streamChatMessage } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { useChatSession, useChatSessions, useCreateChatSession, useDeleteChatSession } from "@/features/chat/api";
import { useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";

export function CopilotPage() {
  const qc = useQueryClient();
  const { data: sessions } = useChatSessions();
  const [activeId, setActiveId] = useState<string | undefined>(undefined);
  const { data: session } = useChatSession(activeId);
  const createSession = useCreateChatSession();
  const deleteSession = useDeleteChatSession();

  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [liveReply, setLiveReply] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!activeId && sessions && sessions.length > 0) setActiveId(sessions[0].id);
  }, [sessions, activeId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages.length, liveReply]);

  const send = async () => {
    if (!activeId || !input.trim() || streaming) return;
    const content = input;
    setInput("");
    setStreaming(true);
    setLiveReply("");
    try {
      await streamChatMessage(activeId, content, (chunk) => setLiveReply((r) => r + chunk));
    } finally {
      setStreaming(false);
      setLiveReply("");
      qc.invalidateQueries({ queryKey: ["chat-session", activeId] });
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-4">
      <div className="flex w-56 flex-shrink-0 flex-col gap-1 border-r border-border pr-3">
        <Button
          variant="outline"
          size="sm"
          onClick={() => createSession.mutate({ title: "New conversation" }, { onSuccess: (s) => setActiveId(s.id) })}
        >
          <Plus className="h-3.5 w-3.5" /> New chat
        </Button>
        <div className="mt-2 flex flex-col gap-0.5">
          {sessions?.map((s) => (
            <div
              key={s.id}
              className={cn(
                "group flex items-center justify-between rounded-md px-2 py-1.5 text-sm hover:bg-accent",
                activeId === s.id && "bg-accent"
              )}
            >
              <button className="flex-1 truncate text-left" onClick={() => setActiveId(s.id)}>
                {s.title}
              </button>
              <button
                className="hidden text-muted-foreground hover:text-destructive group-hover:block"
                onClick={() => {
                  deleteSession.mutate(s.id);
                  if (activeId === s.id) setActiveId(undefined);
                }}
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-1 flex-col">
        <div className="flex-1 overflow-y-auto pr-1">
          {!session && <p className="text-muted-foreground">Start a new conversation to talk to your local copilot.</p>}
          <div className="flex flex-col gap-4">
            {session?.messages.map((m) => (
              <ChatBubble key={m.id} role={m.role as "user" | "assistant"} content={m.content} />
            ))}
            {streaming && <ChatBubble role="assistant" content={liveReply || "..."} />}
          </div>
          <div ref={bottomRef} />
        </div>

        <div className="mt-3 flex items-end gap-2 border-t border-border pt-3">
          <Textarea
            rows={2}
            placeholder="Ask about a job, get resume feedback, prep for an interview..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            disabled={!activeId}
          />
          <Button onClick={send} disabled={!activeId || streaming || !input.trim()}>
            {streaming ? <Spinner /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
}

function ChatBubble({ role, content }: { role: "user" | "assistant"; content: string }) {
  const isUser = role === "user";
  return (
    <div className={cn("flex gap-2", isUser && "flex-row-reverse")}>
      <div className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-muted">
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div className={cn("max-w-[75%] whitespace-pre-line rounded-lg px-3 py-2 text-sm", isUser ? "bg-primary text-primary-foreground" : "bg-muted")}>
        {content}
      </div>
    </div>
  );
}
