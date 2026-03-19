if the pine script indicator is used with another account than mine, I cant set an alert with condition the
indicator - what could this be?

⏺ This is a TradingView platform restriction, not a Pine Script bug. The core issue is how TradingView runs indicators
  for alerts server-side.

  Why Alert Conditions Fail on Another Account

  When you create an alert using an indicator condition (alertcondition()), TradingView's servers need to continuously
  run your indicator to evaluate the condition. The permissions for this differ from just viewing the indicator on a
  chart.

  Most likely cause: The script is not published.

  ┌────────────────────────────┬──────────────────┬─────────────────────────┐
  │       Script status        │ Can add to chart │ Can set alert condition │
  ├────────────────────────────┼──────────────────┼─────────────────────────┤
  │ Private (Pine Editor only) │ Owner only       │ Owner only              │
  ├────────────────────────────┼──────────────────┼─────────────────────────┤
  │ Shared via link (unlisted) │ Anyone with link │ ❌ Only owner           │
  ├────────────────────────────┼──────────────────┼─────────────────────────┤
  │ Published (public)         │ Anyone           │ Anyone                  │
  ├────────────────────────────┼──────────────────┼─────────────────────────┤
  │ Invite-only published      │ Invited users    │ Invited users           │
  └────────────────────────────┴──────────────────┴─────────────────────────┘

  Even if someone adds your script to their chart via a shared link, TradingView won't let them create alerts from it —
   the alert system requires a published script that TradingView can reference by its stable publication ID.

  Fix Options

  1. Publish the script publicly on TradingView (Source: open or protected)
  2. Publish as invite-only and grant the other account access via the script's "Manage Access" panel
  3. Have them copy the source into their own Pine Editor and save it to their account (if source is open)

  Note on Protected Scripts

  If you publish with "Protected" source (code hidden), the other user can still set alerts — they just can't see the
  Pine code. This is the typical approach for sharing commercial indicators.

❯ its published invite only and the other user is invited

⏺ A few things to check in order of likelihood:

  1. Indicator must be on the chart first
  The invited user needs to have the indicator actively loaded on their chart before creating the alert. The condition
  only appears in the "Create Alert" → Condition dropdown if the indicator is currently on that chart/symbol.

  2. Invitation accepted properly
  Being invited via TradingView's system requires the user to:
  - Receive the invite notification on TradingView
  - Visit the script page and click "Add to chart" or "Add to favourites"

  Just sending the invite isn't enough — they must have explicitly added the script to their account through the
  script's page.

  3. Free account alert limits
  If the other user is on a Free plan, they're limited to 1 active alert. They may have hit their limit. Upgrading or
  deleting existing alerts fixes this.

  4. The condition dropdown shows "no condition"
  If alertcondition() calls exist in the script, they only show up in the dropdown when:
  - The indicator is on the chart
  - The correct symbol/timeframe the indicator was designed for is active

  ---
  ★ Insight ─────────────────────────────────────
  TradingView alert conditions are registered per chart session — alertcondition() doesn't globally register
  conditions, it registers them only while the indicator is loaded on an active chart. This is why "indicator on chart"
   is a prerequisite, not just access permission.
  ─────────────────────────────────────────────────

  Most likely fix: have them add the indicator to their chart first, then try creating the alert from that same chart
  tab.
