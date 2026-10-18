# PMc-apps
Claude-made apps

- [Streaks](https://peterwmcdonald-prog.github.io/PMc-apps/streaks-app/) – habit tracker
- [Gramadeg](https://peterwmcdonald-prog.github.io/PMc-apps/gramadeg/) – Welsh grammar practice. Questions live in `gramadeg/content.json`; `gramadeg/review.html` lists them all for checking.
- [Cathays commute](https://peterwmcdonald-prog.github.io/PMc-apps/cathays-commute/) – train planner between Dingle Road / Eastbrook / Penarth and Cathays Park 2. Timetable data sits near the top of the script in `cathays-commute/index.html`.

Every app icon carries the same PMc badge, bottom right. For a new app, make a plain 512×512 `icon-512.png` and run `python3 tools/add-pmc-badge.py plain-icon.png newapp/icons` to create all four badged icon sizes.
