import { describe, expect, it } from "vitest";

import { winLossSlices } from "./ring";

describe("kazanma halkası", () => {
  it("kazanma oranını yüzdeler", () => {
    expect(winLossSlices(3, 4)).toEqual({ win: 75, loss: 25, losses: 1 });
  });

  it("botsuz durumda sıfır döner", () => {
    expect(winLossSlices(0, 0)).toEqual({ win: 0, loss: 0, losses: 0 });
  });

  it("aralık dışı girdiyi kırpar", () => {
    expect(winLossSlices(9, 4)).toEqual({ win: 100, loss: 0, losses: 0 });
  });
});
