import React from "react";
import { formatDate, formatTime, formatTo, formatHours, KM_TO_NM } from "./format";

// ---------------------------------------------------------------------------
// Base value classes
// ---------------------------------------------------------------------------

abstract class ColumnValue<T> {
  constructor(protected _value: T) {}
  abstract render(): string;
  get value(): T { return this._value; }
}

abstract class NumericValue extends ColumnValue<number> {
  add(other: NumericValue): number { return this._value + other._value; }
  gt(n: number): boolean { return this._value > n; }
  lt(n: number): boolean { return this._value < n; }
  gte(n: number): boolean { return this._value >= n; }
  lte(n: number): boolean { return this._value <= n; }
}

// ---------------------------------------------------------------------------
// Concrete value classes
// ---------------------------------------------------------------------------

export class ActivityDate extends ColumnValue<string> {
  render(): string { return formatDate(this._value); }
  after(iso: string): boolean { return this._value > iso; }
  before(iso: string): boolean { return this._value < iso; }
}

export class From extends ColumnValue<string> {
  render(): string { return formatTime(this._value); }
}

export class To extends ColumnValue<{ from: string; to: string }> {
  render(): string { return formatTo(this._value.from, this._value.to); }
}

export class SailingDistance extends NumericValue {
  /** raw value is stored in nm */
  render(): string { return `${this._value.toFixed(2)} nm`; }
  static fromKm(km: number): SailingDistance {
    return new SailingDistance(km * KM_TO_NM);
  }
}

export class DefaultDistance extends NumericValue {
  /** raw value is stored in km */
  render(): string { return `${this._value} km`; }
}

export class Time extends NumericValue {
  /** raw value is stored in hours */
  render(): string { return formatHours(this._value); }
  static fromMinutes(min: number): Time {
    return new Time(min / 60);
  }
}

export class Speed extends NumericValue {
  /** raw value is stored in knots */
  render(): string { return `${this._value.toFixed(1)} kn`; }
}

export class Name {
  constructor(private readonly _value: string) {}
  get value(): string { return this._value; }
  render(stravaId?: number): React.ReactNode {
    if (stravaId) {
      return React.createElement(
        "a",
        { href: `https://www.strava.com/activities/${stravaId}`, target: "_blank", rel: "noopener noreferrer" },
        this._value,
      );
    }
    return this._value;
  }
}

// ---------------------------------------------------------------------------
// Row container
// ---------------------------------------------------------------------------

export interface ActivityRowFields {
  id:           number | string;
  stravaId?:    number;
  name:         string;
  sportType?:   string;
  date:         ActivityDate;
  from?:        From;
  to?:          To;
  distance:     SailingDistance | DefaultDistance;
  moving:       Time;
  elapsed:      Time;
  afterSunset?: Time;
  maxSpeed?:    Speed;
  avgSpeed?:    Speed;
}

export class ActivityRow {
  readonly id:          number | string;
  readonly stravaId?:   number;
  readonly name:        string;
  readonly sportType?:  string;
  readonly date:        ActivityDate;
  readonly from?:       From;
  readonly to?:         To;
  readonly distance:    SailingDistance | DefaultDistance;
  readonly moving:      Time;
  readonly elapsed:     Time;
  readonly afterSunset?: Time;
  readonly maxSpeed?:    Speed;
  readonly avgSpeed?:    Speed;

  constructor(fields: ActivityRowFields) {
    Object.assign(this, fields);
    this.id          = fields.id;
    this.stravaId    = fields.stravaId;
    this.name        = fields.name;
    this.sportType   = fields.sportType;
    this.date        = fields.date;
    this.from        = fields.from;
    this.to          = fields.to;
    this.distance    = fields.distance;
    this.moving      = fields.moving;
    this.elapsed     = fields.elapsed;
    this.afterSunset = fields.afterSunset;
    this.maxSpeed    = fields.maxSpeed;
    this.avgSpeed    = fields.avgSpeed;
  }

  get nameValue(): Name { return new Name(this.name); }

  render(): Record<string, unknown> {
    return {
      id:               this.id,
      strava_id:        this.stravaId,
      _nameValue:       this.nameValue,
      name:             this.name,
      sport_type:       this.sportType,
      start_date_local: this.date.render(),
      from:             this.from?.render(),
      to:               this.to?.render(),
      distance:         this.distance.render(),
      moving:           this.moving.render(),
      elapsed:          this.elapsed.render(),
      after_sunset:     this.afterSunset?.render(),
      max_speed:        this.maxSpeed?.render(),
      avg_speed:        this.avgSpeed?.render(),
    };
  }

  // ---------------------------------------------------------------------------
  // Factory methods
  // ---------------------------------------------------------------------------

  static fromSailingActivity(a: {
    id?: number;
    start_date_local: string;
    from?: string | null;
    to?: string | null;
    name: string;
    distance_nm: number;
    moving_time_hr: number;
    elapsed_time_hr: number;
    after_sunset_hr?: number | null;
    max_speed_kn?: number | null;
    avg_speed_kn?: number | null;
  }, index: number): ActivityRow {
    return new ActivityRow({
      id:          index,
      stravaId:    a.id,
      name:        a.name,
      sportType:   "Sail",
      date:        new ActivityDate(a.start_date_local),
      from:        a.from ? new From(a.from) : undefined,
      to:          a.from && a.to ? new To({ from: a.from, to: a.to }) : undefined,
      distance:    new SailingDistance(a.distance_nm),
      moving:      new Time(a.moving_time_hr),
      elapsed:     new Time(a.elapsed_time_hr),
      afterSunset: a.after_sunset_hr != null ? new Time(a.after_sunset_hr) : undefined,
      maxSpeed:    a.max_speed_kn != null ? new Speed(a.max_speed_kn) : undefined,
      avgSpeed:    a.avg_speed_kn != null ? new Speed(a.avg_speed_kn) : undefined,
    });
  }

  static fromActivity(a: {
    id: number;
    name: string;
    sport_type: string;
    start_date_local: string;
    distance_km: number;
    moving_time_min: number;
    elapsed_time_min: number;
  }): ActivityRow {
    const isSail = a.sport_type === "Sail";
    return new ActivityRow({
      id:        a.id,
      name:      a.name,
      sportType: a.sport_type,
      date:      new ActivityDate(a.start_date_local),
      distance:  isSail
        ? SailingDistance.fromKm(a.distance_km)
        : new DefaultDistance(a.distance_km),
      moving:    Time.fromMinutes(a.moving_time_min),
      elapsed:   Time.fromMinutes(a.elapsed_time_min),
    });
  }

  // ---------------------------------------------------------------------------
  // Aggregation helpers (operate on collections of rows)
  // ---------------------------------------------------------------------------

  static sum(rows: ActivityRow[], field: "distance" | "moving" | "elapsed" | "afterSunset"): number {
    return rows.reduce((acc, row) => {
      const v = row[field];
      return v ? acc + v.value : acc;
    }, 0);
  }

  static filter(rows: ActivityRow[], predicate: (row: ActivityRow) => boolean): ActivityRow[] {
    return rows.filter(predicate);
  }

  static median(values: (number | undefined)[]): number | null {
    const nums = values.filter((v): v is number => v != null).sort((a, b) => a - b);
    if (nums.length === 0) return null;
    const mid = Math.floor(nums.length / 2);
    return nums.length % 2 === 0
      ? (nums[mid - 1] + nums[mid]) / 2
      : nums[mid];
  }

  static typicalTime(isoTimes: (string | undefined)[]): string | null {
    const minutes = isoTimes
      .filter((t): t is string => !!t)
      .map((t) => {
        const d = new Date(t);
        return d.getHours() * 60 + d.getMinutes();
      })
      .sort((a, b) => a - b);
    if (minutes.length === 0) return null;
    const mid = Math.floor(minutes.length / 2);
    const median = minutes.length % 2 === 0
      ? Math.round((minutes[mid - 1] + minutes[mid]) / 2)
      : minutes[mid];
    const h = String(Math.floor(median / 60)).padStart(2, "0");
    const m = String(median % 60).padStart(2, "0");
    return `${h}:${m}`;
  }

  static dateRange(rows: ActivityRow[]): { from: ActivityDate; to: ActivityDate } | null {
    if (rows.length === 0) return null;
    const sorted = [...rows].sort((a, b) => a.date.value.localeCompare(b.date.value));
    return { from: sorted[0].date, to: sorted[sorted.length - 1].date };
  }
}
