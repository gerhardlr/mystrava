import { describe, it, expect } from "vitest";
import {
  ActivityDate,
  From,
  To,
  SailingDistance,
  DefaultDistance,
  Time,
  ActivityRow,
} from "@/lib/activity-values";

// ---------------------------------------------------------------------------
// ActivityDate
// ---------------------------------------------------------------------------

describe("ActivityDate", () => {
  const d = new ActivityDate("2026-02-18T16:00:00");

  it("renders with weekday, day, month and year", () => {
    expect(d.render()).toMatch(/wed.*18.*feb.*2026/i);
  });

  it("exposes raw iso string as value", () => {
    expect(d.value).toBe("2026-02-18T16:00:00");
  });

  it("after() returns true when date is later", () => {
    expect(d.after("2026-01-01T00:00:00")).toBe(true);
  });

  it("after() returns false when date is earlier", () => {
    expect(d.after("2026-12-01T00:00:00")).toBe(false);
  });

  it("before() returns true when date is earlier", () => {
    expect(d.before("2026-12-01T00:00:00")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// From
// ---------------------------------------------------------------------------

describe("From", () => {
  const f = new From("2026-03-08T16:11:00");

  it("renders as HH:MM without seconds", () => {
    expect(f.render()).toBe("16:11");
  });

  it("exposes raw iso string as value", () => {
    expect(f.value).toBe("2026-03-08T16:11:00");
  });
});

// ---------------------------------------------------------------------------
// To
// ---------------------------------------------------------------------------

describe("To", () => {
  it("renders time only on same day", () => {
    const t = new To({ from: "2026-03-08T16:11:00", to: "2026-03-08T18:48:00" });
    expect(t.render()).toBe("18:48");
  });

  it("adds +1d when sail ends the following day", () => {
    const t = new To({ from: "2025-10-18T08:00:00", to: "2025-10-19T04:50:00" });
    expect(t.render()).toBe("04:50 +1d");
  });

  it("exposes raw from/to as value", () => {
    const t = new To({ from: "2025-10-18T08:00:00", to: "2025-10-19T04:50:00" });
    expect(t.value.from).toBe("2025-10-18T08:00:00");
    expect(t.value.to).toBe("2025-10-19T04:50:00");
  });
});

// ---------------------------------------------------------------------------
// SailingDistance
// ---------------------------------------------------------------------------

describe("SailingDistance", () => {
  const d = new SailingDistance(10.69);

  it("renders with nm unit", () => {
    expect(d.render()).toBe("10.69 nm");
  });

  it("exposes raw nm value", () => {
    expect(d.value).toBe(10.69);
  });

  it("fromKm() converts km to nm", () => {
    const nm = SailingDistance.fromKm(1.852);
    expect(nm.value).toBeCloseTo(1, 2);
  });

  it("gt/lt comparisons work on nm value", () => {
    expect(d.gt(10)).toBe(true);
    expect(d.lt(10)).toBe(false);
    expect(d.gte(10.69)).toBe(true);
    expect(d.lte(10.69)).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// DefaultDistance
// ---------------------------------------------------------------------------

describe("DefaultDistance", () => {
  const d = new DefaultDistance(12.5);

  it("renders with km unit", () => {
    expect(d.render()).toBe("12.5 km");
  });

  it("exposes raw km value", () => {
    expect(d.value).toBe(12.5);
  });

  it("add() sums two distances", () => {
    const d2 = new DefaultDistance(7.5);
    expect(d.add(d2)).toBe(20);
  });
});

// ---------------------------------------------------------------------------
// Time
// ---------------------------------------------------------------------------

describe("Time", () => {
  const t = new Time(2.3);

  it("renders with hr unit", () => {
    expect(t.render()).toBe("2.3 hr");
  });

  it("exposes raw hours value", () => {
    expect(t.value).toBe(2.3);
  });

  it("fromMinutes() converts minutes to hours", () => {
    const t2 = Time.fromMinutes(90);
    expect(t2.value).toBeCloseTo(1.5, 5);
    expect(t2.render()).toBe("1.5 hr");
  });

  it("gt/lt comparisons work on hours", () => {
    expect(t.gt(2)).toBe(true);
    expect(t.lt(3)).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// ActivityRow.fromSailingActivity
// ---------------------------------------------------------------------------

const sailRaw = {
  start_date_local: "2025-10-18T08:00:00",
  from: "2025-10-18T08:00:00",
  to: "2025-10-19T04:50:00",
  name: "Morning Sail",
  distance_nm: 110.49,
  moving_time_hr: 20.58,
  elapsed_time_hr: 20.85,
  after_sunset_hr: 9.81,
};

describe("ActivityRow.fromSailingActivity", () => {
  const row = ActivityRow.fromSailingActivity(sailRaw, 0);

  it("render() includes formatted date", () => {
    expect(String(row.render().start_date_local)).toMatch(/2025/);
  });

  it("render() includes from time", () => {
    expect(row.render().from).toBe("08:00");
  });

  it("render() includes to time with +1d", () => {
    expect(row.render().to).toBe("04:50 +1d");
  });

  it("render() includes distance in nm", () => {
    expect(row.render().distance).toBe("110.49 nm");
  });

  it("render() includes moving time with hr", () => {
    expect(row.render().moving).toBe("20.58 hr");
  });

  it("render() includes after_sunset with hr", () => {
    expect(row.render().after_sunset).toBe("9.81 hr");
  });
});

// ---------------------------------------------------------------------------
// ActivityRow.fromActivity
// ---------------------------------------------------------------------------

const activityRaw = {
  id: 1,
  name: "Morning Run",
  sport_type: "Run",
  start_date_local: "2026-01-10T07:00:00",
  distance_km: 10,
  moving_time_min: 60,
  elapsed_time_min: 62,
};

const sailActivityRaw = { ...activityRaw, id: 2, name: "Sail", sport_type: "Sail" };

describe("ActivityRow.fromActivity", () => {
  it("uses km for non-sailing activities", () => {
    const row = ActivityRow.fromActivity(activityRaw);
    expect(row.render().distance).toBe("10 km");
  });

  it("uses nm for sailing activities", () => {
    const row = ActivityRow.fromActivity(sailActivityRaw);
    expect(String(row.render().distance)).toMatch(/nm/);
  });

  it("converts moving time from minutes to hours", () => {
    const row = ActivityRow.fromActivity(activityRaw);
    expect(row.render().moving).toBe("1 hr");
  });
});

// ---------------------------------------------------------------------------
// ActivityRow aggregation
// ---------------------------------------------------------------------------

describe("ActivityRow.sum", () => {
  const rows = [
    ActivityRow.fromSailingActivity({ ...sailRaw, distance_nm: 10 }, 0),
    ActivityRow.fromSailingActivity({ ...sailRaw, distance_nm: 20 }, 1),
    ActivityRow.fromSailingActivity({ ...sailRaw, distance_nm: 30 }, 2),
  ];

  it("sums distance across rows", () => {
    expect(ActivityRow.sum(rows, "distance")).toBeCloseTo(60, 5);
  });

  it("sums moving time across rows", () => {
    expect(ActivityRow.sum(rows, "moving")).toBeCloseTo(sailRaw.moving_time_hr * 3, 5);
  });
});

// ---------------------------------------------------------------------------
// ActivityRow.filter
// ---------------------------------------------------------------------------

describe("ActivityRow.typicalTime", () => {
  it("returns median time for odd count", () => {
    // sorted: 08:00, 09:00, 14:00 → median 09:00
    expect(ActivityRow.typicalTime([
      "2026-01-01T14:00:00",
      "2026-01-01T08:00:00",
      "2026-01-01T09:00:00",
    ])).toBe("09:00");
  });

  it("returns midpoint of two middle values for even count", () => {
    // sorted: 08:00, 10:00, 12:00, 14:00 → median (10:00+12:00)/2 = 11:00
    expect(ActivityRow.typicalTime([
      "2026-01-01T08:00:00",
      "2026-01-01T10:00:00",
      "2026-01-01T12:00:00",
      "2026-01-01T14:00:00",
    ])).toBe("11:00");
  });

  it("returns null for empty array", () => {
    expect(ActivityRow.typicalTime([])).toBeNull();
  });

  it("ignores undefined entries", () => {
    expect(ActivityRow.typicalTime([undefined, "2026-01-01T10:00:00"])).toBe("10:00");
  });
});

describe("ActivityRow.filter", () => {
  const rows = [
    ActivityRow.fromSailingActivity({ ...sailRaw, distance_nm: 5 }, 0),
    ActivityRow.fromSailingActivity({ ...sailRaw, distance_nm: 15 }, 1),
    ActivityRow.fromSailingActivity({ ...sailRaw, distance_nm: 25 }, 2),
  ];

  it("filters rows by distance", () => {
    const result = ActivityRow.filter(rows, (r) => r.distance.gt(10));
    expect(result).toHaveLength(2);
  });

  it("filters rows by date", () => {
    const result = ActivityRow.filter(rows, (r) => r.date.after("2025-01-01T00:00:00"));
    expect(result).toHaveLength(3);
  });
});
