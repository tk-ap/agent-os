"""Milchik-managed backlog: rank candidate work for agent attention.

Deterministic and dependency-free. Ranking is a pure function of declared
fields, so attention allocation is auditable and work origin (human vs agent)
can never silently override declared priority.

Weighting model (see agents/milchik/BACKLOG.md for the prose rationale):

- Priority level sets the base: p0=60, p1=45, p2=30, p3=15.
- Confidence refines within a priority band: +confidence*30 (max +30).
- Origin affects two things only, and neither is a hidden score bump:
  1. confidence *default*: a human-triggered item defaults to confidence 1.0
     (direct human intent is a high-confidence signal of relevance); an
     agent/routine item defaults to 0.5 (needs corroboration before it is
     assumed relevant). Explicit confidence always wins over the default.
  2. authorization path: human work carries known intent and is pre-authorized
     to queue; agent/routine work ranks for attention but still requires
     explicit approval before enqueue.

A p0 agent proposal therefore still outranks a p2 human request — declared
priority dominates — but human intent is never under-weighted merely because
its source is not an agent.
"""

PRIORITY_BASE = {"p0": 60.0, "p1": 45.0, "p2": 30.0, "p3": 15.0}
CONFIDENCE_MAX = 30.0
DEFAULT_CONFIDENCE_HUMAN = 1.0
DEFAULT_CONFIDENCE_OTHER = 0.5

SOURCES = ("human", "agent", "routine", "ailhat")

# Lane is a soft gate, not a hard one. Ecosystem-backend work drains before the
# team turns to product directives, so it carries a bonus large enough that any
# ecosystem item at p1 or above outranks any directive — while still letting a
# p0 directive break through ahead of ecosystem p2/p3 rather than starving
# behind cleanup.
LANES = ("ecosystem", "directive")
LANE_BONUS = {"ecosystem": 30.0, "directive": 0.0}
DEFAULT_LANE = "ecosystem"


def _clamp(value, lo=0.0, hi=1.0):
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = lo
    return max(lo, min(hi, value))


def priority_level(item):
    """Return the declared priority level, defaulting to p3 (lowest)."""
    priority = item.get("priority") or {}
    return priority.get("level", "p3")


def confidence(item):
    """Declared confidence, or the origin-based default when not declared."""
    priority = item.get("priority") or {}
    declared = priority.get("confidence")
    if declared is not None:
        return _clamp(declared)
    default = DEFAULT_CONFIDENCE_HUMAN if item.get("source") == "human" else DEFAULT_CONFIDENCE_OTHER
    return default


def lane(item):
    """Declared lane, defaulting to ecosystem (backend work drains first)."""
    value = item.get("lane", DEFAULT_LANE)
    return value if value in LANE_BONUS else DEFAULT_LANE


def attention_score(item):
    """0..120. Lane gates, priority dominates within a lane, confidence refines.

    Ordering of terms is deliberate: the lane bonus (30) is smaller than a full
    priority band gap (15 per level, 45 from p3 to p0), so it sequences classes
    of work without ever making a p3 outrank a p0 in the same lane.
    """
    base = PRIORITY_BASE.get(priority_level(item), 15.0)
    return base + confidence(item) * CONFIDENCE_MAX + LANE_BONUS[lane(item)]


def authority_present(item):
    """Human-triggered work is pre-authorized to queue; agent/routine work is not.

    This is the only place source changes behavior: the authorization path,
    never the attention score.
    """
    return item.get("source") == "human"


def rank(backlog):
    """Return items sorted by attention score (desc), stable on work_id."""
    return sorted(backlog, key=lambda i: (-attention_score(i), str(i.get("work_id", ""))))


def next_for_attention(backlog, k=1):
    """The top-k items Milchik should surface for agent attention."""
    return rank(backlog)[:max(0, k)]
