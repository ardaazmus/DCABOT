import { HistoricalProfile } from "./datasetCatalog";

export type HistoricalProfileStatus = "idle" | "loading" | "ready" | "error";

type HistoricalProfileSelectorProps = {
  profiles: HistoricalProfile[];
  status: HistoricalProfileStatus;
  error: string;
  selectedProfileId: string | null;
  disabled: boolean;
  onChange: (profileId: string) => void;
  onRetry: () => void;
};

export function HistoricalProfileSelector({ profiles, status, error, selectedProfileId, disabled, onChange, onRetry }: HistoricalProfileSelectorProps) {
  const selectedProfile = profiles.find((profile) => profile.profile_id === selectedProfileId);
  const fixedSliceSelected = selectedProfile?.simulation_model === "historical_ohlcv_partial_fixed_v1";
  return <section className="historical-profile-selector" aria-labelledby="historical-profile-title">
    <p className="preflight-section-label" id="historical-profile-title">HISTORICAL PROFILE</p>
    <label htmlFor="historical-profile-select">Historical profile</label>
    <select id="historical-profile-select" value={selectedProfileId ?? ""} disabled={disabled || status === "loading" || status === "error"} onChange={(event) => onChange(event.target.value)}>
      <option value="" disabled>Profil seçin…</option>
      {profiles.map((profile) => <option key={profile.profile_id} value={profile.profile_id}>{profile.label}</option>)}
    </select>
    {fixedSliceSelected && <p className="historical-profile-model-helper" role="note"><strong>Fixed-slice model seçildi.</strong> Bu, legacy OHLC modelinden farklı bir offline varsayımdır; çalıştırmadan önce onay gerekir.</p>}
    {status === "loading" && <p className="historical-profile-status" role="status" aria-live="polite">Historical profile katalogu yükleniyor…</p>}
    {status === "error" && <div className="historical-profile-error" role="alert"><p>{error || "Historical profile katalogu okunamadı."}</p><button className="catalog-secondary-button" type="button" onClick={onRetry}>Tekrar dene</button></div>}
    {status === "ready" && !selectedProfileId && <p className="historical-profile-helper">Çalıştırmak için bir historical profile seçin.</p>}
  </section>;
}
