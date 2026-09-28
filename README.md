# Goings On · Barcelona

A compact, serif-led cultural listings widget designed for GitHub Pages and embedding in Notion. GitHub Actions refreshes `events.json` once per day.

## What updates automatically?

Once the RSS feed is configured, GitHub Actions fetches it daily, keeps future-dated events for the next 120 days, removes expired events, and commits the updated `events.json`. The public widget URL stays the same.

**Important limitation:** this is automated aggregation, not a human editor. The RSS feed determines what is available, and the widget classifies listings using keywords. Some events may have incomplete dates, descriptions, or venue details. Always confirm event details with the organiser.

## One-time setup

1. Upload the contents of this folder to your GitHub repository (keep the `.github/workflows/` folder).
2. Open [Agenda Cultural de Catalunya — RSS](https://agenda.cultura.gencat.cat/ca/rss.html).
3. Create an RSS feed for the municipality of **Barcelona**. Select the themes you want, especially visual arts, cinema, shows and music. The feed page provides a generated RSS link.
4. In `sources.json`, replace `PASTE_YOUR_BARCELONA_RSS_URL_HERE` with that full RSS URL. Commit the change.
5. In GitHub, open **Settings → Actions → General → Workflow permissions** and ensure workflows have read and write permissions. The workflow also declares `contents: write`.
6. Open the **Actions** tab → **Refresh cultural agenda** → **Run workflow** to run the first refresh.
7. Enable GitHub Pages for the repository if it is not already enabled. If Pages publishes from the `main` branch and `/ (root)`, keep `index.html`, `events.json`, and `sources.json` in the repository root.

## Embed in Notion

After GitHub Pages is published, copy the public URL for `index.html` and paste it into a Notion `/embed` block.

## How it behaves

- The whole agenda opens/closes from the header.
- Individual listings can expand to show more information.
- Filters include broad cultural categories and upcoming months.
- Saved plans and filters work in the current browser session.
- The widget uses Cormorant Garamond and Libre Franklin from Google Fonts, with serif/system fallbacks.
- The scheduled job runs daily. GitHub may start scheduled workflows a little later than the exact time.

## Feed notes

The parser deliberately skips items without a usable future event date rather than inventing one. If the selected RSS feed only provides publication dates rather than event start dates, many items may be skipped. In that case, use an RSS feed that includes event dates or add another feed from a venue that publishes structured event dates.

The official RSS page is here: https://agenda.cultura.gencat.cat/ca/rss.html
