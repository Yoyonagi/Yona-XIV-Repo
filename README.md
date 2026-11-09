# Yona XIV Repo

A custom [Dalamud](https://github.com/goatcorp/Dalamud) plugin repository for Yona plugins.
**This is not the official Dalamud repository** — plugins here are not reviewed by the Dalamud team.

## Add the repository

1. In game, open `/xlsettings` → **Experimental**.
2. Under **Custom Plugin Repositories**, paste:
   ```
   https://raw.githubusercontent.com/Yoyonagi/Yona-XIV-Repo/main/repo.json
   ```
3. Tick **Enabled**, click **Save**, and browse the plugins in `/xlplugins`.

## Plugins

| Plugin | Source |
| --- | --- |
| Yona Toolbox | [Yoyonagi/Yona-Toolbox](https://github.com/Yoyonagi/Yona-Toolbox) |

## How it works

`repo.json` is generated — don't edit it by hand. The **Update repo.json** workflow reads
`plugins.json`, looks up each plugin's GitHub releases, and writes the manifest Dalamud
downloads. It runs:

- when a plugin repo sends a `plugin-released` dispatch after tagging a release,
- every 30 minutes as a fallback,
- when `plugins.json` or the script changes, or manually from the Actions tab.

Pre-releases become the plugin's **testing** build (users opt in per plugin from
`/xlplugins`).

### Adding another plugin

Add an entry to `plugins.json`:

```json
{ "repo": "Yoyonagi/Another-Plugin", "internalName": "AnotherPlugin", "iconUrl": "https://…/icon.png" }
```

The plugin's releases must contain `latest.zip` and `<InternalName>.json`, which the
Yona Toolbox build workflow already produces — copy it as a starting point.

> GitHub pauses scheduled workflows in repositories with no activity for 60 days. If that
> happens, re-enable it from the Actions tab or rely on the release dispatch.
