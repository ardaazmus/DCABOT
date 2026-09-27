import { describe, expect, it } from "vitest";

import { barHeights, countBySo } from "./histogram";

describe("SO histogramı", () => {
  it("yalnız kapanan deal'leri 0..max kovalarına sayar", () => {
    const deals = [
      { closed_at_us: 1, safety_orders_filled: 0 },
      { closed_at_us: 2, safety_orders_filled: 2 },
      { closed_at_us: 3, safety_orders_filled: 2 },
      { closed_at_us: null, safety_orders_filled: 0 },
    ];
    expect(countBySo(deals, 3)).toEqual([1, 0, 2, 0]);
  });

  it("aralık dışı dolumu uç kovaya kırpar", () => {
    const deals = [{ closed_at_us: 1, safety_orders_filled: 9 }];
    expect(countBySo(deals, 2)).toEqual([0, 0, 1]);
  });

  it("yükseklikleri tepeye göre yüzdeler", () => {
    expect(barHeights([1, 0, 2, 0])).toEqual([50, 0, 100, 0]);
    expect(barHeights([0, 0])).toEqual([0, 0]);
  });
});
