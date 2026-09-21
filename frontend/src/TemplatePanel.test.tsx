import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  TemplatePanel,
  isTemplateBindResponse,
  isTemplateDetail,
  type TemplateBindResult,
  type TemplateDetail,
  type TemplateDiffRow,
  type TemplateMeta,
} from "./TemplatePanel";

const metas: TemplateMeta[] = [
  { template_id: "t1", payload_sha256: "a".repeat(64), declared_capabilities: ["DCA"] },
];

const detail: TemplateDetail = {
  template_id: "t1",
  payload_sha256: "a".repeat(64),
  declared_capabilities: ["DCA"],
  payload: { deviation: "0.2" },
};

const bindResult: TemplateBindResult = {
  binding_id: "b".repeat(64),
  status: "BOUND",
  profile_id: "paper",
  params: [["deviation", "0.2"]],
  config_hash: "c".repeat(64),
};

const diffRows: TemplateDiffRow[] = [{ key: "deviation", before: "0.1", after: "0.2" }];

function renderPanel(overrides = {}) {
  const handlers = {
    onImport: vi.fn(),
    onSelect: vi.fn(),
    onBind: vi.fn(),
    onDiff: vi.fn(),
    ...overrides,
  };
  render(
    <TemplatePanel
      templates={metas}
      detail={detail}
      bindResult={bindResult}
      diffRows={diffRows}
      busy={false}
      error=""
      {...handlers}
    />,
  );
  return handlers;
}

describe("isTemplateDetail", () => {
  it("geçerli detayı kabul eder, bozuk yükü reddeder", () => {
    expect(isTemplateDetail(detail)).toBe(true);
    expect(isTemplateDetail({ ...detail, payload: 5 })).toBe(false);
    expect(isTemplateDetail(null)).toBe(false);
  });
});

describe("isTemplateBindResponse", () => {
  it("POST /api/templates/{id}/bind'in gerçek şeklini kabul eder (config_hash materialized altında)", () => {
    expect(
      isTemplateBindResponse({
        binding: {
          binding_id: "b".repeat(64),
          status: "BOUND",
          profile_id: "paper",
          params: [["deviation", "0.2"]],
        },
        materialized: { config: { deviation: "0.2" }, config_hash: "c".repeat(64) },
      }),
    ).toBe(true);
  });

  it("config_hash binding altında (eski/yanlış şekil) verilirse reddeder", () => {
    expect(isTemplateBindResponse({ binding: bindResult })).toBe(false);
  });
});

describe("TemplatePanel", () => {
  it("listeyi, detayı, bağlama sonucunu ve farkı gösterir", () => {
    renderPanel();
    expect(screen.getByRole("button", { name: /t1/ })).toBeInTheDocument();
    expect(screen.getByText(/"deviation": "0.2"/)).toBeInTheDocument();
    expect(screen.getByText(/BOUND/)).toBeInTheDocument();
    expect(screen.getByText("c".repeat(64))).toBeInTheDocument();
    expect(screen.getByText("0.1")).toBeInTheDocument();
    expect(screen.getByText(/yetkisiz aktivasyon yapmaz/)).toBeInTheDocument();
  });

  it("içe aktarma typed payload ile çağırır", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Şablon ID"), { target: { value: "t2" } });
    fireEvent.change(screen.getByLabelText("Yük (JSON)"), { target: { value: '{"deviation":"0.3"}' } });
    fireEvent.change(screen.getByLabelText("Kapabilite"), { target: { value: "DCA" } });
    fireEvent.click(screen.getByRole("button", { name: /İçe aktar/ }));
    expect(handlers.onImport).toHaveBeenCalledWith({
      template_id: "t2",
      schema_version: "strategy-template-v1",
      payload: { deviation: "0.3" },
      declared_capabilities: ["DCA"],
    });
  });

  it("bozuk JSON içe aktarmayı engeller", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Şablon ID"), { target: { value: "t2" } });
    fireEvent.change(screen.getByLabelText("Yük (JSON)"), { target: { value: "{bozuk" } });
    fireEvent.click(screen.getByRole("button", { name: /İçe aktar/ }));
    expect(handlers.onImport).not.toHaveBeenCalled();
    expect(screen.getByText(/geçerli JSON değil/)).toBeInTheDocument();
  });

  it("bağlama ve fark düğmeleri seçimlerle çağırır", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Profil"), { target: { value: "paper" } });
    fireEvent.click(screen.getByRole("checkbox", { name: /onaylıyorum/ }));
    fireEvent.click(screen.getByRole("button", { name: /Profile bağla/ }));
    expect(handlers.onBind).toHaveBeenCalledWith("t1", {
      profile_id: "paper",
      allowed_capabilities: ["DCA"],
      approval: "APPROVED",
    });
    fireEvent.change(screen.getByLabelText("İkinci şablon"), { target: { value: "t2" } });
    fireEvent.click(screen.getByRole("button", { name: /Karşılaştır/ }));
    expect(handlers.onDiff).toHaveBeenCalledWith("t1", "t2");
  });
});
