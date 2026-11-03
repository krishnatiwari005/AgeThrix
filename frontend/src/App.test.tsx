import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("exports the application entry component", () => {
    expect(App).toBeTypeOf("function");
  });
});
