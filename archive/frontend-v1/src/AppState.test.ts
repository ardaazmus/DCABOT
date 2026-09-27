import { describe, expect, it } from "vitest";

import { groupReducer } from "./App";

describe("groupReducer", () => {
  it("updates one grouped field and supports functional updates", () => {
    const initial = { datasets: ["one"], status: "idle" };
    const updated = groupReducer(initial, { key: "datasets", value: ["two"] });
    const final = groupReducer(updated, {
      key: "datasets",
      value: (current) => [...current, "three"],
    });

    expect(final).toEqual({ datasets: ["two", "three"], status: "idle" });
  });
});
