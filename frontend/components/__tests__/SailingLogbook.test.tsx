import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import SailingLogbook from "@/components/SailingLogbook";
import mockData from "@/mock_data/mock_sailing_data.json";

const activities = mockData.activities;

describe("SailingLogbook", () => {
  it("renders all column headers", () => {
    render(<SailingLogbook activities={activities} />);
    expect(screen.getByText("Date")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("From")).toBeInTheDocument();
    expect(screen.getByText("To")).toBeInTheDocument();
    expect(screen.getByText("Distance (nm)")).toBeInTheDocument();
    expect(screen.getByText("Moving (hr)")).toBeInTheDocument();
    expect(screen.getByText("Elapsed (hr)")).toBeInTheDocument();
    expect(screen.getByText("After Sunset (hr)")).toBeInTheDocument();
  });

  it("renders activity names from mock data", () => {
    render(<SailingLogbook activities={activities} />);
    expect(screen.getAllByText("Afternoon Sail").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Lunch Sail").length).toBeGreaterThan(0);
  });

  it("renders correct row count", () => {
    render(<SailingLogbook activities={activities} />);
    // DataGrid shows "1–25 of 88" style pagination text
    expect(screen.getByText(/88/)).toBeInTheDocument();
  });

  it("renders distance values", () => {
    render(<SailingLogbook activities={activities} />);
    // First activity distance
    expect(screen.getByText("10.69")).toBeInTheDocument();
  });

  it("renders after_sunset_hr for night activities", () => {
    render(<SailingLogbook activities={activities} />);
    // The overnight sail has after_sunset_hr: 9.81
    expect(screen.getByText("9.81")).toBeInTheDocument();
  });
});
