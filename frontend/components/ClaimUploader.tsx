"use client";

import { useState, useCallback, useRef } from "react";

interface ClaimUploaderProps {
  onSubmit: (formData: FormData) => void;
  isAnalyzing: boolean;
  error: string | null;
}

export default function ClaimUploader({ onSubmit, isAnalyzing, error }: ClaimUploaderProps) {
  const [claimFile, setClaimFile] = useState<File | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [docFile, setDocFile] = useState<File | null>(null);
  const [manualMode, setManualMode] = useState(false);
  const [formErrors, setFormErrors] = useState<string[]>([]);

  // Manual form fields
  const [formFields, setFormFields] = useState({
    claimant_name: "",
    policy_id: "",
    claim_amount: "",
    claim_date: "",
    hospital_name: "",
    incident_lat: "",
    incident_lng: "",
    incident_description: "",
  });

  const handleDrop = useCallback(
    (setter: (f: File | null) => void) => (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      const file = e.dataTransfer.files[0];
      if (file) setter(file);
    },
    []
  );

  const handleFileInput = useCallback(
    (setter: (f: File | null) => void) => (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) setter(file);
    },
    []
  );

  const validateAndSubmit = () => {
    const errors: string[] = [];

    if (!claimFile && !manualMode) {
      errors.push("Please upload a claim form JSON file or use manual entry");
    }

    if (manualMode) {
      if (!formFields.claimant_name) errors.push("Claimant name is required");
      if (!formFields.policy_id) errors.push("Policy ID is required");
      if (!formFields.claim_amount || parseFloat(formFields.claim_amount) <= 0)
        errors.push("Valid claim amount is required");
      if (!formFields.claim_date) errors.push("Claim date is required");
    }

    setFormErrors(errors);
    if (errors.length > 0) return;

    const formData = new FormData();

    if (manualMode) {
      const claimJson = {
        ...formFields,
        claim_amount: parseFloat(formFields.claim_amount),
        incident_lat: formFields.incident_lat ? parseFloat(formFields.incident_lat) : null,
        incident_lng: formFields.incident_lng ? parseFloat(formFields.incident_lng) : null,
      };
      formData.append("claim_form", JSON.stringify(claimJson));
    } else if (claimFile) {
      // Read the file and append as string
      const reader = new FileReader();
      reader.onload = () => {
        formData.append("claim_form", reader.result as string);
        if (photoFile) formData.append("damage_photo", photoFile);
        if (docFile) formData.append("supporting_doc", docFile);
        onSubmit(formData);
      };
      reader.readAsText(claimFile);
      return;
    }

    if (photoFile) formData.append("damage_photo", photoFile);
    if (docFile) formData.append("supporting_doc", docFile);
    onSubmit(formData);
  };

  return (
    <div className="glass-card space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-gray-200">Submit Insurance Claim</h3>
        <button
          onClick={() => setManualMode(!manualMode)}
          className="text-sm px-4 py-1.5 rounded-lg border border-blue-500/30 text-blue-400 hover:bg-blue-500/10 transition-all"
        >
          {manualMode ? "📁 Upload JSON" : "✏️ Manual Entry"}
        </button>
      </div>

      {/* Error display */}
      {(formErrors.length > 0 || error) && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
          {formErrors.map((e, i) => (
            <p key={i} className="text-red-400 text-sm">⚠ {e}</p>
          ))}
          {error && <p className="text-red-400 text-sm">⚠ {error}</p>}
        </div>
      )}

      {manualMode ? (
        /* Manual Entry Form */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { key: "claimant_name", label: "Claimant Name", type: "text", placeholder: "Full name" },
            { key: "policy_id", label: "Policy ID", type: "text", placeholder: "POL_XXXXX" },
            { key: "claim_amount", label: "Claim Amount (₹)", type: "number", placeholder: "500000" },
            { key: "claim_date", label: "Claim Date", type: "datetime-local", placeholder: "" },
            { key: "hospital_name", label: "Hospital Name", type: "text", placeholder: "Hospital name" },
            { key: "incident_lat", label: "Incident Latitude", type: "number", placeholder: "19.076" },
            { key: "incident_lng", label: "Incident Longitude", type: "number", placeholder: "72.877" },
          ].map((field) => (
            <div key={field.key}>
              <label className="block text-sm text-gray-400 mb-1">{field.label}</label>
              <input
                type={field.type}
                placeholder={field.placeholder}
                value={(formFields as any)[field.key]}
                onChange={(e) =>
                  setFormFields((prev) => ({ ...prev, [field.key]: e.target.value }))
                }
                className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-gray-200 placeholder-gray-600 focus:border-blue-500/50 focus:outline-none focus:ring-1 focus:ring-blue-500/25 transition-all"
              />
            </div>
          ))}
          <div className="md:col-span-2">
            <label className="block text-sm text-gray-400 mb-1">Incident Description</label>
            <textarea
              placeholder="Describe the incident..."
              value={formFields.incident_description}
              onChange={(e) =>
                setFormFields((prev) => ({ ...prev, incident_description: e.target.value }))
              }
              rows={3}
              className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-gray-200 placeholder-gray-600 focus:border-blue-500/50 focus:outline-none focus:ring-1 focus:ring-blue-500/25 transition-all resize-none"
            />
          </div>
        </div>
      ) : (
        /* File Upload Zones */
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Claim Form JSON */}
          <div
            className={`drop-zone ${claimFile ? "has-file" : ""}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop(setClaimFile)}
            onClick={() => document.getElementById("claim-input")?.click()}
          >
            <input
              id="claim-input"
              type="file"
              accept=".json"
              onChange={handleFileInput(setClaimFile)}
              className="hidden"
            />
            <div className="text-3xl mb-2">📋</div>
            <p className="text-sm font-medium text-gray-300">
              {claimFile ? claimFile.name : "Claim Form JSON"}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {claimFile ? "✓ Uploaded" : "Drag & drop or click"}
            </p>
          </div>

          {/* Damage Photo */}
          <div
            className={`drop-zone ${photoFile ? "has-file" : ""}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop(setPhotoFile)}
            onClick={() => document.getElementById("photo-input")?.click()}
          >
            <input
              id="photo-input"
              type="file"
              accept="image/*"
              onChange={handleFileInput(setPhotoFile)}
              className="hidden"
            />
            <div className="text-3xl mb-2">📸</div>
            <p className="text-sm font-medium text-gray-300">
              {photoFile ? photoFile.name : "Damage Photo"}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {photoFile ? "✓ Uploaded" : "Drag & drop or click"}
            </p>
          </div>

          {/* Supporting Document */}
          <div
            className={`drop-zone ${docFile ? "has-file" : ""}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop(setDocFile)}
            onClick={() => document.getElementById("doc-input")?.click()}
          >
            <input
              id="doc-input"
              type="file"
              accept=".pdf,.txt,.doc,.docx"
              onChange={handleFileInput(setDocFile)}
              className="hidden"
            />
            <div className="text-3xl mb-2">📄</div>
            <p className="text-sm font-medium text-gray-300">
              {docFile ? docFile.name : "Supporting Document"}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {docFile ? "✓ Uploaded" : "Optional — Drag & drop"}
            </p>
          </div>
        </div>
      )}

      {/* Submit Button */}
      <div className="flex justify-center">
        <button
          onClick={validateAndSubmit}
          disabled={isAnalyzing}
          className={`
            px-8 py-3.5 rounded-xl font-semibold text-white text-lg
            transition-all duration-300 flex items-center gap-3
            ${isAnalyzing
              ? "bg-gray-600 cursor-not-allowed"
              : "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:scale-[1.02]"
            }
          `}
        >
          {isAnalyzing ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Analyzing Claim...
            </>
          ) : (
            <>🔍 Analyze Claim</>
          )}
        </button>
      </div>
    </div>
  );
}
