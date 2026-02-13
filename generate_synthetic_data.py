"""Generate 3 synthetic CSV files simulating regression cycle evolution."""
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

OUTPUT_DIR = Path(__file__).parent / "data" / "synthetic"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COMPONENTS = [
    "Authentication", "Payment", "Dashboard", "Reports", "User Management",
    "Notifications", "Search", "API Gateway", "File Upload", "Settings",
]

TESTERS = {
    "alice.johnson": {"accuracy": 0.85, "name": "Alice Johnson"},
    "bob.smith": {"accuracy": 0.65, "name": "Bob Smith"},
    "carol.williams": {"accuracy": 0.90, "name": "Carol Williams"},
    "dave.brown": {"accuracy": 0.55, "name": "Dave Brown"},
    "eve.davis": {"accuracy": 0.78, "name": "Eve Davis"},
    "frank.miller": {"accuracy": 0.72, "name": "Frank Miller"},
}

VALID_SUMMARIES = [
    "Login fails with valid credentials on Firefox",
    "Payment processing timeout after 30 seconds",
    "Dashboard charts not rendering for large datasets",
    "Report export produces empty CSV file",
    "User profile update does not save phone number",
    "Email notifications sent with wrong recipient name",
    "Search returns no results for exact match queries",
    "API rate limiting not enforced for authenticated users",
    "File upload fails silently for files over 10MB",
    "Settings page crashes when timezone is changed",
    "Password reset token expires before email arrives",
    "Two-factor authentication bypass via session cookie",
    "Credit card validation accepts expired cards",
    "Chart tooltips show wrong values on hover",
    "Scheduled report runs at wrong time zone",
    "Cannot delete user with active subscriptions",
    "Push notifications not received on Android 14",
    "Autocomplete search shows deleted items",
    "GraphQL query returns 500 for nested pagination",
    "Drag and drop file upload breaks on Safari",
    "CSRF token validation fails after session refresh",
    "Bulk payment import skips rows with special characters",
    "Dashboard widget positions not saved after rearrange",
    "PDF report has overlapping text in footer",
    "User cannot change email without re-verification",
    "Notification preferences reset after password change",
    "Full-text search ignores hyphenated words",
    "API returns 200 instead of 404 for deleted resources",
    "Large file upload causes memory spike on server",
    "Dark mode toggle does not persist across sessions",
    "Session token not invalidated after logout",
    "Dropdown menu clips behind adjacent card component",
    "Currency conversion uses stale exchange rates",
    "Batch email sender silently drops attachments above 5MB",
    "OAuth redirect loop when third-party cookies disabled",
    "Pagination off-by-one error on last page of results",
    "Breadcrumb navigation shows wrong hierarchy after deep link",
    "Concurrent edits overwrite each other without conflict warning",
    "Invoice PDF generator crashes on Unicode company names",
    "Role-based access control allows viewer to edit shared dashboard",
    "CSV import fails when header row contains trailing whitespace",
    "Timezone offset calculated incorrectly for daylight saving dates",
    "Mobile responsive layout breaks at 768px viewport width",
    "SSO login redirects to blank page after IdP timeout",
    "Database connection pool exhausted under concurrent report generation",
    "Markdown renderer executes embedded script tags",
    "Export to Excel truncates cell content at 32767 characters",
    "Webhook retry logic sends duplicate payloads on network timeout",
    "Forgot-password link is valid beyond the stated 24 hour window",
    "Audit trail missing entries for bulk status change operations",
    "Date range filter excludes end-date results due to midnight cutoff",
    "Table sort on numeric column treats values as strings",
    "Avatar upload accepts SVG files containing embedded JavaScript",
    "Autocomplete suggestion list flickers when typing fast",
    "Background job scheduler skips runs after server clock adjustment",
    "Team member invitation email contains broken unsubscribe link",
    "Multi-select filter loses state when navigating back from detail page",
    "Locale-specific number formatting breaks chart axis labels",
    "REST API PATCH endpoint returns full object instead of delta",
    "Password complexity rules not enforced on API-created accounts",
    "Kanban board drag handle unresponsive on touch devices",
    "Attachment preview fails for HEIC image format",
    "Custom field validation skipped during bulk import",
    "Activity feed shows duplicate entries after page reconnects WebSocket",
    "Print stylesheet cuts off right margin of wide tables",
    "API key rotation endpoint does not revoke previous key",
    "Comment thread collapses unexpectedly when new reply arrives",
    "Geolocation lookup returns null for IPv6 addresses",
    "Data retention policy deletes records one day early",
    "Status badge color contrast ratio fails WCAG AA on light theme",
    "Recursive folder move endpoint allows circular reference",
    "Notification bell count includes dismissed notifications",
    "Histogram bin width calculation wrong for log-scaled data",
    "Inline code block styling lost when content pasted from Word",
    "Retry-after header missing on 429 rate limit response",
    "Environment variable secrets logged in plain text during startup",
    "Tag autocomplete does not escape HTML entities in suggestions",
    "Gantt chart milestone overlap detection incorrect for zero-duration tasks",
    "Two-column PDF layout breaks when left column content overflows",
    "Lazy-loaded images flash alt text before rendering on slow connection",
    "User preference sync across tabs lost after service worker update",
    "Certificate pinning bypass when proxy rewrites response headers",
    "Clickjacking possible on account settings page missing X-Frame-Options",
    "Long file names overflow attachment chip component in message thread",
    "Saved search query does not URL-encode special characters",
    "Dashboard auto-refresh interval doubles after each browser tab switch",
    "Email template engine crashes on nested conditional blocks",
    "Admin bulk-disable accounts still allows active sessions to continue",
    "Bar chart Y-axis label collides with large tick values",
    "Workflow transition allows skip from Open directly to Closed",
    "REST endpoint returns 500 when Accept header specifies XML",
    "Project archive action does not cascade to child work items",
    "Spell checker underlines technical jargon stored in custom dictionary",
    "Matrix permission view does not scroll horizontally on small screens",
    "Background image in hero section causes layout shift on initial paint",
    "Merge request diff viewer crashes on binary file comparison",
    "Pipeline artifact download link expires before notification email arrives",
    "Hotkey conflict between global search and inline cell editing",
]

INVALID_SUMMARIES = [
    "The button color should be darker blue",
    "I think the font size is too small on my monitor",
    "Application is slow on my old laptop",
    "Would be nice to have keyboard shortcuts",
    "The loading spinner is not centered perfectly",
    "Expected different behavior based on my assumption",
    "Cannot reproduce the issue anymore after clearing cache",
    "This works differently than the competitor product",
    "Feature request: add bulk delete option",
    "The error message could be more user-friendly",
    "Page loads slower than I expected on 3G network",
    "UI looks different than the mockup from last year",
    "Need more sorting options in the table",
    "The confirmation dialog is annoying for frequent users",
    "Would prefer a different date picker component",
    "Tooltips are distracting when I scroll quickly",
    "Can we change the default landing page to analytics",
    "Sidebar navigation takes too many clicks to reach settings",
    "Would like dark mode for the login page as well",
    "Table column widths feel inconsistent across pages",
    "Suggestion: allow drag-reorder of dashboard widgets",
    "Icons look pixelated on my high-DPI external monitor",
    "Contrast between header and body text could be better",
    "Request: add CSV export button to every table",
    "Calendar widget starts week on Sunday instead of Monday",
    "Placeholder text disappears too quickly in search box",
    "Dropdown animation feels sluggish compared to competitor",
    "Would appreciate breadcrumb trail on every page",
    "Status badge colors are hard to distinguish for colorblind users",
    "Notification sound is too loud and there is no volume control",
    "Graphs should use company brand colors instead of defaults",
    "Mobile app: bottom nav bar covers submit button on short screens",
    "Auto-save indicator is confusing, suggest using a toast instead",
    "Suggested improvement: group related settings into collapsible sections",
    "Login page background image takes too long to load on hotel wifi",
    "Tab order on form skips the middle name field",
    "Title case in menu items feels inconsistent with sentence case elsewhere",
    "Timestamp format should be relative instead of absolute",
    "Would be nice to have a global undo action",
    "Help tooltip uses technical jargon unfamiliar to new users",
]

VALID_DESCRIPTIONS = [
    "Steps to reproduce:\n1. Navigate to {component}\n2. Perform the action described\n3. Observe incorrect behavior\n\nExpected: Feature works correctly\nActual: Feature fails as described in summary\n\nEnvironment: Chrome 120, Windows 11",
    "Reproducible 100% of the time.\n\nSteps:\n1. Log in as any user\n2. Go to {component}\n3. Trigger the issue\n\nThis blocks QA testing for the current sprint.",
    "Found during regression testing of {component}.\n\nThe issue occurs consistently and impacts user workflow. Screenshots attached.\n\nBrowser: Firefox 121\nOS: macOS Sonoma",
]

INVALID_DESCRIPTIONS = [
    "I think this might be an issue but I'm not sure. It happened once and I couldn't reproduce it.",
    "This is more of a suggestion than a bug. The current behavior works but could be improved.",
    "Saw this on my personal device. Not sure if it's related to my setup or the application.",
]

PRIORITIES = ["Critical", "Major", "Minor", "Trivial"]
PRIORITY_WEIGHTS = [0.1, 0.35, 0.4, 0.15]
SEVERITIES = ["Critical", "Major", "Minor", "Trivial"]
STATUSES = ["Open", "In Progress", "Resolved", "Closed", "Reopened"]


def pick_weighted(items, weights):
    return random.choices(items, weights=weights, k=1)[0]


def generate_duplicate_summary(original: str) -> str:
    transforms = [
        lambda s: s.replace("fails", "is broken").replace("not", "doesn't"),
        lambda s: "Issue: " + s.lower(),
        lambda s: s.replace("after", "when").replace("for", "with"),
        lambda s: s + " (intermittent)",
    ]
    return random.choice(transforms)(original)


def generate_cycle(cycle_num: int, n_bugs: int, invalid_rate: float, dup_rate: float) -> pd.DataFrame:
    base_date = datetime(2025, 1 + (cycle_num - 1) * 2, 5)
    rows = []
    n_valid = int(n_bugs * (1 - invalid_rate - dup_rate))
    n_invalid = int(n_bugs * invalid_rate)
    n_dup = n_bugs - n_valid - n_invalid

    valid_pool = random.sample(VALID_SUMMARIES, min(n_valid, len(VALID_SUMMARIES)))

    for i in range(n_valid):
        tester = random.choice(list(TESTERS.keys()))
        component = random.choice(COMPONENTS)
        desc_template = random.choice(VALID_DESCRIPTIONS)
        rows.append({
            "Issue key": f"PROJ-{cycle_num}{i+1:03d}",
            "Summary": valid_pool[i],
            "Description": desc_template.format(component=component),
            "Status": random.choice(STATUSES),
            "Priority": pick_weighted(PRIORITIES, PRIORITY_WEIGHTS),
            "Severity": random.choice(SEVERITIES),
            "Component/s": component,
            "Reporter": tester,
            "Assignee": random.choice(list(TESTERS.keys())),
            "Created": (base_date + timedelta(days=random.randint(0, 20), hours=random.randint(0, 23))).isoformat(),
            "Resolved": (base_date + timedelta(days=random.randint(21, 40))).isoformat() if random.random() > 0.3 else "",
            "Resolution": random.choice(["Fixed", "Fixed", "Won't Fix", ""]),
            "Labels": random.choice(["regression", "regression,ui", "regression,backend", "regression,critical", ""]),
            "Issue Type": "Bug",
            "_true_label": "valid",
        })

    for i in range(n_invalid):
        tester_keys = list(TESTERS.keys())
        low_accuracy = sorted(tester_keys, key=lambda t: TESTERS[t]["accuracy"])
        tester = random.choice(low_accuracy[:3]) if random.random() < 0.7 else random.choice(tester_keys)
        component = random.choice(COMPONENTS)
        rows.append({
            "Issue key": f"PROJ-{cycle_num}{n_valid+i+1:03d}",
            "Summary": random.choice(INVALID_SUMMARIES),
            "Description": random.choice(INVALID_DESCRIPTIONS),
            "Status": random.choice(STATUSES),
            "Priority": pick_weighted(PRIORITIES, [0.02, 0.18, 0.5, 0.3]),
            "Severity": random.choice(["Minor", "Trivial", "Minor"]),
            "Component/s": component,
            "Reporter": tester,
            "Assignee": "",
            "Created": (base_date + timedelta(days=random.randint(0, 20), hours=random.randint(0, 23))).isoformat(),
            "Resolved": "",
            "Resolution": "",
            "Labels": random.choice(["", "needs-triage", "question"]),
            "Issue Type": "Bug",
            "_true_label": "invalid",
        })

    dup_sources = [r for r in rows if r["_true_label"] == "valid"]
    for i in range(n_dup):
        source = random.choice(dup_sources) if dup_sources else rows[0]
        tester = random.choice(list(TESTERS.keys()))
        rows.append({
            "Issue key": f"PROJ-{cycle_num}{n_valid+n_invalid+i+1:03d}",
            "Summary": generate_duplicate_summary(source["Summary"]),
            "Description": source["Description"][:200] + "\n\n(Similar issue observed independently)",
            "Status": random.choice(STATUSES),
            "Priority": source["Priority"],
            "Severity": source["Severity"],
            "Component/s": source["Component/s"],
            "Reporter": tester,
            "Assignee": "",
            "Created": (base_date + timedelta(days=random.randint(0, 20), hours=random.randint(0, 23))).isoformat(),
            "Resolved": "",
            "Resolution": "Duplicate",
            "Labels": "duplicate",
            "Issue Type": "Bug",
            "_true_label": "duplicate",
        })

    random.shuffle(rows)
    return pd.DataFrame(rows)


def main():
    random.seed(42)

    cycles = [
        (1, 120, 0.30, 0.12),  # Early/messy
        (2, 100, 0.20, 0.10),  # Improving
        (3, 90, 0.15, 0.08),   # Mature
    ]

    for cycle_num, n_bugs, invalid_rate, dup_rate in cycles:
        df = generate_cycle(cycle_num, n_bugs, invalid_rate, dup_rate)
        outpath = OUTPUT_DIR / f"regression_cycle_{cycle_num}.csv"
        df.to_csv(outpath, index=False)
        true_counts = df["_true_label"].value_counts().to_dict()
        print(f"Cycle {cycle_num}: {len(df)} bugs -> {true_counts} => {outpath}")

    print("\nDone. Files written to", OUTPUT_DIR)


if __name__ == "__main__":
    main()
