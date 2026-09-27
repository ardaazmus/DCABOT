import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ExplanationSection } from "./ExplanationSection";

describe("ExplanationSection", () => {
  it("açıklama yoksa boş durum mesajını gösterir", () => {
    render(<ExplanationSection explanations={[]} />);

    expect(screen.getByText("Ek açıklama bulunmuyor.")).toBeInTheDocument();
  });

  it("backend açıklamalarını teknik ayrıntılarıyla gösterir", () => {
    render(
      <ExplanationSection
        explanations={[
          {
            code: "INFO_CODE",
            severity: "INFO",
            title: "Bilgi",
            message: "İşlem tamamlandı.",
            source: "test",
            context: {},
          },
          {
            code: "ERROR_CODE",
            severity: "ERROR",
            title: "Teknik hata",
            message: "Veri doğrulanamadı.",
            source: "test",
            context: { artifact_sha256: "eşleşmedi" },
          },
        ]}
      />,
    );

    expect(screen.getAllByText("Teknik hata")).toHaveLength(3);
    expect(screen.getByText("Veri doğrulanamadı.")).toBeInTheDocument();
    expect(screen.getByText(/artifact_sha256.*eşleşmedi/s)).toBeInTheDocument();
    expect(screen.getAllByText("Bilgi")).toHaveLength(3);
  });
});
