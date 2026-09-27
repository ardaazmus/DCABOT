import { useState } from "react";

// E.2: Lab bölümü iskeleti (§8.2 + §8.1). Ana motordan ayrı ürün alanı:
// borsayı yorabilecek özellikler önce burada yaşar. Bu dilim iskelet:
// gerçek veri akışı E.3'te bağlanacak, şimdi yalnız tanıtım + zorunlu
// risk uyarısı + tek-seferlik onay var. Uydurma veri yok.

const LAB_ACK_KEY = "dcabot.lab.risk_ack";

function readLabAck(): boolean {
  try {
    return window.localStorage.getItem(LAB_ACK_KEY) === "1";
  } catch {
    return false;
  }
}

export function LabPanel() {
  const [acknowledged, setAcknowledged] = useState<boolean>(readLabAck);
  return (
    <div className="workspace">
      <section className="panel" aria-labelledby="lab-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">LAB · DENEYSEL</p>
            <h2 id="lab-title">Lab</h2>
          </div>
        </div>
        <p className="helper-text">
          Ana motorun dışında, ek içgörü üreten ama borsayı normalden fazla yorabilecek
          özelliklerin ayrı alanı. Buradaki hiçbir özellik canlı emir vermez.
        </p>
      </section>
      <section className="panel" aria-labelledby="lab-whale-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">İLK SAKİN · YAKINDA</p>
            <h2 id="lab-whale-title">Whale Wall Detection</h2>
          </div>
        </div>
        <p className="helper-text">Tespit motoru hazır (E.3) — canlı gösterim ayrı dilimde bağlanacak.</p>
        <p className="liq-fastmove" role="note">
          Bu özellik ek borsa isteği yapar, hesabınızın rate-limit&apos;ini kullanır.
        </p>
        {acknowledged ? (
          <p className="helper-text" role="status">
            Risk bildirimi onaylandı.
          </p>
        ) : (
          <div className="whatif-opt-in">
            <label htmlFor="lab-risk-ack">
              <input
                id="lab-risk-ack"
                type="checkbox"
                checked={false}
                onChange={() => {
                  try {
                    window.localStorage.setItem(LAB_ACK_KEY, "1");
                  } catch {
                    return;
                  }
                  setAcknowledged(true);
                }}
              />{" "}
              <span>Anladım, Lab özelliklerinin ek borsa isteği yapacağını kabul ediyorum.</span>
            </label>
          </div>
        )}
      </section>
    </div>
  );
}
