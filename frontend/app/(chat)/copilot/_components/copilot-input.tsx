"use client";

import * as React from "react";
import { ArrowUp, Sparkles, Loader2, CornerDownLeft } from "lucide-react";

interface CopilotInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
}

const SAMPLE_PROMPTS = [
  "What is our forecasted sales demand for Pure Cotton 60s over the next 30 days?",
  "Do we have enough grey cloth stock in Shed 1 to fulfill incoming print orders?",
  "Synthesize current sales growth with warehouse stock buffers to recommend our weekly run.",
  "What is the standard operating procedure for reactive dye bath temperature control?",
];

export function CopilotInput({ onSend, disabled, isLoading }: CopilotInputProps) {
  const [value, setValue] = React.useState("");
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  React.useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        180
      )}px`;
    }
  }, [value]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!value.trim() || disabled || isLoading) return;
    onSend(value.trim());
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSelectPrompt = (prompt: string) => {
    setValue(prompt);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-2 p-4 pt-2">
      {/* Suggestion Chips */}
      <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1 text-xs">
        <span className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1 shrink-0">
          <Sparkles className="w-3 h-3 text-brand" />
          <span>Suggestions:</span>
        </span>
        {SAMPLE_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleSelectPrompt(prompt)}
            className="px-2.5 py-1 rounded-full bg-card hover:bg-muted border border-border text-muted-foreground hover:text-foreground text-[11px] shrink-0 transition-colors truncate max-w-[280px]"
            title={prompt}
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <form
        onSubmit={handleSubmit}
        className="relative flex items-end rounded-2xl border border-border bg-card shadow-lg focus-within:ring-2 focus-within:ring-brand/50 focus-within:border-brand transition-all overflow-hidden p-2"
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Executive Copilot about demand forecasts, stock buffers, or SOPs..."
          rows={1}
          disabled={disabled || isLoading}
          className="flex-1 max-h-44 resize-none bg-transparent px-3 py-1.5 text-xs sm:text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50 font-sans"
        />

        <div className="flex items-center gap-1.5 pb-0.5 pr-1">
          <button
            type="submit"
            disabled={!value.trim() || disabled || isLoading}
            className={`w-8 h-8 rounded-xl flex items-center justify-center transition-all ${
              value.trim() && !isLoading
                ? "bg-brand text-brand-fg hover:opacity-90 shadow-sm"
                : "bg-muted text-muted-foreground opacity-40 cursor-not-allowed"
            }`}
            title="Send message (Enter)"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <ArrowUp className="w-4 h-4 stroke-[2.5]" />
            )}
          </button>
        </div>
      </form>

      <div className="flex items-center justify-between text-[11px] text-muted-foreground px-2">
        <span>Press <kbd className="px-1 py-0.5 rounded bg-muted font-mono text-[10px]">Enter</kbd> to send, <kbd className="px-1 py-0.5 rounded bg-muted font-mono text-[10px]">Shift+Enter</kbd> for new line</span>
        <span className="hidden sm:inline">Orchestrated via Sales, Inventory & Knowledge Specialist Agents</span>
      </div>
    </div>
  );
}
