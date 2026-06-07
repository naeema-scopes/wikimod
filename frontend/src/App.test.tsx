import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the header", () => {
    render(<App />);
    expect(screen.getByText("WikiMod")).toBeInTheDocument();
  });

  it("renders the analyze form", () => {
    render(<App />);
    expect(
      screen.getByText("Analyze a Wikipedia Talk Page")
    ).toBeInTheDocument();
  });

  it("renders navigation links", () => {
    render(<App />);
    expect(screen.getByText("Analyze")).toBeInTheDocument();
    expect(screen.getByText("History")).toBeInTheDocument();
    expect(screen.getByText("Model Info")).toBeInTheDocument();
  });
});
