"use client";

interface GradCamOverlayProps {
  imageResult?: {
    deepfake_probability: number;
    location_mismatch_km: number;
    gradcam_heatmap_b64: string | null;
    exif_gps: { lat: number; lng: number };
    claimed_location: { lat: number; lng: number };
    timestamp_mismatch_hours: number;
    metadata_stripped: boolean;
  };
}

export default function GradCamOverlay({ imageResult }: GradCamOverlayProps) {
  if (!imageResult) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-8">
        <div className="text-4xl mb-3">📸</div>
        <p className="text-gray-500">No image analysis available</p>
      </div>
    );
  }

  const showOverlay = !imageResult.gradcam_heatmap_b64;
  const deepfakePct = Math.round(imageResult.deepfake_probability * 100);
  const locationMismatch = imageResult.location_mismatch_km > 10;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-300 flex items-center gap-2">
        📸 Image Forensics
      </h3>

      {/* Image with overlay */}
      <div className="relative rounded-xl overflow-hidden bg-gray-800/50 aspect-video flex items-center justify-center">
        {/* Placeholder image area */}
        <div className="w-full h-full bg-gradient-to-br from-gray-700/30 to-gray-800/30 flex items-center justify-center relative">
          <div className="text-center">
            <div className="text-5xl mb-2 opacity-30">🖼️</div>
            <p className="text-xs text-gray-600">Damage Photo</p>
          </div>

          {/* GradCAM overlay (stub mode) */}
          {showOverlay && (
            <div className="absolute top-0 right-0 w-1/2 h-1/2 bg-red-500/25 backdrop-blur-[1px] flex items-center justify-center border-l-2 border-b-2 border-red-500/30">
              <div className="text-center">
                <p className="text-red-400 text-xs font-semibold">Suspicious Region</p>
                <p className="text-red-400/60 text-[10px]">(demo)</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Location mismatch banner */}
      {locationMismatch && (
        <div className="px-4 py-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
          📍 Photo taken <strong>{imageResult.location_mismatch_km}km</strong> from claimed location
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white/5 rounded-xl p-3">
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Deepfake Prob.</p>
          <p className={`text-lg font-bold ${deepfakePct > 60 ? "text-red-400" : deepfakePct > 30 ? "text-yellow-400" : "text-green-400"}`}>
            {deepfakePct}%
          </p>
        </div>
        <div className="bg-white/5 rounded-xl p-3">
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">GPS Mismatch</p>
          <p className={`text-lg font-bold ${locationMismatch ? "text-red-400" : "text-green-400"}`}>
            {imageResult.location_mismatch_km}km
          </p>
        </div>
        <div className="bg-white/5 rounded-xl p-3">
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Time Mismatch</p>
          <p className="text-lg font-bold text-gray-300">{imageResult.timestamp_mismatch_hours}h</p>
        </div>
        <div className="bg-white/5 rounded-xl p-3">
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">EXIF Stripped</p>
          <p className={`text-lg font-bold ${imageResult.metadata_stripped ? "text-red-400" : "text-green-400"}`}>
            {imageResult.metadata_stripped ? "Yes ⚠" : "No ✓"}
          </p>
        </div>
      </div>
    </div>
  );
}
