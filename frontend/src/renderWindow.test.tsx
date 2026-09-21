import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { WindowExpander, useWindowedList } from "./renderWindow";

function List({ items, pageSize }: { items: string[]; pageSize: number }) {
  const windowed = useWindowedList(items, pageSize);
  return (
    <div>
      <ul>{windowed.visible.map((item) => <li key={item}>{item}</li>)}</ul>
      {windowed.hasMore && <WindowExpander shown={windowed.shown} total={windowed.total} onMore={windowed.showMore} />}
    </div>
  );
}

describe("useWindowedList", () => {
  it("ilk sayfayı gösterir, genişletince artırır", () => {
    render(<List items={["a", "b", "c", "d"]} pageSize={2} />);
    expect(screen.queryByText("c")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Daha fazla göster \(2\/4\)/ }));
    expect(screen.getByText("d")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Daha fazla/ })).not.toBeInTheDocument();
  });

  it("yeni listede başa döner", () => {
    const { rerender } = render(<List items={["a", "b", "c"]} pageSize={2} />);
    fireEvent.click(screen.getByRole("button", { name: /Daha fazla/ }));
    expect(screen.getByText("c")).toBeInTheDocument();
    rerender(<List items={["x", "y", "z"]} pageSize={2} />);
    expect(screen.queryByText("z")).not.toBeInTheDocument();
    expect(screen.getByText("x")).toBeInTheDocument();
  });

  it("kısa liste genişletici göstermez", () => {
    render(<List items={["a"]} pageSize={50} />);
    expect(screen.queryByRole("button", { name: /Daha fazla/ })).not.toBeInTheDocument();
  });
});
