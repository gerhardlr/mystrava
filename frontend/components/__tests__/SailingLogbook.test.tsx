import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import SailingLogbook from "@/components/SailingLogbook";
import mockData from "@/mock_data/mock_sailing_data.json";

// Import format helpers for unit testing
import { formatDate, formatTime, formatTo } from "@/lib/format";

const activities = mockData.activities;

describe("format helpers", () => {
  it("formats date as weekday day month year", () => {
    expect(formatDate("2026-02-18T16:00:00")).toMatch(/wed.*18.*feb.*2026/i);
  });

  it("formats time as HH:MM without seconds", () => {
    expect(formatTime("2026-03-08T16:11:00")).toBe("16:11");
  });

  it("formats to-time without +1d on same day", () => {
    expect(formatTo("2026-03-08T16:11:00", "2026-03-08T18:48:00")).toBe("18:48");
  });

  it("adds +1d when sail ends the following day", () => {
    expect(formatTo("2025-10-18T08:00:00", "2025-10-19T04:50:00")).toBe("04:50 +1d");
  });
});

describe("SailingLogbook", () => {
  it("renders all column headers", () => {
    render(<SailingLogbook activities={activities} />);
    expect(screen.getByText("Date")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("From")).toBeInTheDocument();
    expect(screen.getByText("To")).toBeInTheDocument();
    expect(screen.getByText("Distance")).toBeInTheDocument();
    expect(screen.getByText("Moving")).toBeInTheDocument();
    expect(screen.getByText("Elapsed")).toBeInTheDocument();
    expect(screen.getByText("After Sunset")).toBeInTheDocument();
  });

  it("renders activity names from mock data", () => {
    render(<SailingLogbook activities={activities} />);
    expect(screen.getAllByText("Afternoon Sail").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Lunch Sail").length).toBeGreaterThan(0);
  });

  it("renders correct row count", () => {
    render(<SailingLogbook activities={activities} />);
    expect(screen.getByText(/88/)).toBeInTheDocument();
  });

  it("shows nm unit next to distance value", () => {
    render(<SailingLogbook activities={activities} />);
    expect(screen.getByText("10.69 nm")).toBeInTheDocument();
  });

  it("shows +1d indicator for overnight sail", () => {
    render(<SailingLogbook activities={activities} />);
    expect(screen.getByText(/\+1d/)).toBeInTheDocument();
  });
});
