"use client";

interface StreamingProgressProps {
  steps: Array<{
    step: string;
    status: string;
    ms?: number;
  }>;
}

const STEP_CONFIG: Record<string, { icon: string; label: string }> = {
  validating_inputs: { icon: "🔍", label: "Validating Inputs" },
  image_forensics: { icon: "📸", label: "Image Forensics" },
  nlp_analysis: { icon: "💬", label: "NLP Analysis" },
  tabular_scoring: { icon: "📊", label: "Tabular Scoring" },
  graph_analysis: { icon: "🕸️", label: "Graph Analysis" },
  rfi_check: { icon: "🚩", label: "RFI Check" },
  ensemble_fusion: { icon: "⚡", label: "Risk Ensemble" },
};

export default function StreamingProgress({ steps }: StreamingProgressProps) {
  const allStepKeys = Object.keys(STEP_CONFIG);

  return (
    <div className="glass-card">
      <h3 className="text-lg font-semibold text-gray-300 mb-6 flex items-center gap-2">
        <span className="animate-pulse">⚙️</span> Processing Pipeline
      </h3>
      <div className="space-y-3">
        {allStepKeys.map((stepKey, index) => {
          const config = STEP_CONFIG[stepKey];
          const stepData = steps.find((s) => s.step === stepKey);
          const isDone = stepData?.status === "done";
          const isRunning = stepData?.status === "running";
          const isFailed = stepData?.status === "failed";
          const isPending = !stepData;

          return (
            <div
              key={stepKey}
              className={`
                flex items-center gap-4 p-3 rounded-xl transition-all duration-500
                ${isDone ? "bg-green-500/10 border border-green-500/20" : ""}
                ${isRunning ? "bg-blue-500/10 border border-blue-500/20" : ""}
                ${isFailed ? "bg-red-500/10 border border-red-500/20" : ""}
                ${isPending ? "bg-white/[0.02] border border-transparent" : ""}
              `}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {/* Status indicator */}
              <div className={`
                w-10 h-10 rounded-full flex items-center justify-center text-lg
                transition-all duration-500
                ${isDone ? "bg-green-500/20 scale-100" : ""}
                ${isRunning ? "bg-blue-500/20 animate-progress-pulse" : ""}
                ${isFailed ? "bg-red-500/20" : ""}
                ${isPending ? "bg-white/5 scale-95 opacity-40" : ""}
              `}>
                {isDone ? "✅" : isFailed ? "❌" : config.icon}
              </div>

              {/* Label */}
              <div className="flex-1">
                <p className={`font-medium text-sm ${isDone ? "text-green-400" : isRunning ? "text-blue-400" : isFailed ? "text-red-400" : "text-gray-500"}`}>
                  {config.label}
                </p>
                {isFailed && stepData && (
                  <p className="text-xs text-red-400 mt-0.5">{(stepData as any).message}</p>
                )}
              </div>

              {/* Timing */}
              <div className="text-right">
                {isDone && stepData?.ms !== undefined && (
                  <span className="text-xs text-green-400/70 font-mono">{stepData.ms}ms</span>
                )}
                {isRunning && (
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" style={{ animationDelay: "200ms" }}></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" style={{ animationDelay: "400ms" }}></div>
                  </div>
                )}
              </div>

              {/* Progress line */}
              {index < allStepKeys.length - 1 && (
                <div className="absolute left-[39px] top-[52px] w-0.5 h-3 bg-white/5"></div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
