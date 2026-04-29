import app from "ags/gtk4/app"
import { Gtk } from "ags/gtk4"
import { execAsync } from "ags/process"
import Cairo from "cairo"
import GLib from "gi://GLib"

const ROOT = GLib.getenv("TOOLING_SHOWCASE_ROOT") || "/home/small_ed/Projects/local-llm-tooling-showcase"
const BACKEND = `PYTHONPATH=${ROOT}/src python -m tooling_showcase.hypr_sidebar`
const SETTINGS_DIR = `${GLib.get_home_dir()}/.config/tooling-showcase-hypr-sidebar`
const SETTINGS_PATH = `${SETTINGS_DIR}/settings.json`

type SidebarSettings = {
  opacity: number
  locked: boolean
  x: number | null
  y: number | null
}

let currentWindow: Gtk.Window | null = null
let statusNode: Gtk.Label | null = null
let refreshCallback: (() => void) | null = null

const textDecoder = new TextDecoder()

let settings: SidebarSettings = loadSettings()

function runBackend(command: string) {
  return execAsync(["bash", "-lc", `${BACKEND} ${command}`]).then(JSON.parse)
}

function runShell(command: string) {
  return execAsync(["bash", "-lc", command])
}

function loadSettings(): SidebarSettings {
  try {
    const [, bytes] = GLib.file_get_contents(SETTINGS_PATH)
    const parsed = JSON.parse(textDecoder.decode(bytes))
    return {
      opacity: clampOpacity(Number(parsed.opacity ?? 0.94)),
      locked: Boolean(parsed.locked),
      x: Number.isFinite(parsed.x) ? Number(parsed.x) : null,
      y: Number.isFinite(parsed.y) ? Number(parsed.y) : null,
    }
  } catch (_) {
    return { opacity: 0.94, locked: false, x: null, y: null }
  }
}

function saveSettings() {
  GLib.mkdir_with_parents(SETTINGS_DIR, 0o755)
  GLib.file_set_contents(SETTINGS_PATH, JSON.stringify(settings, null, 2))
}

function clampOpacity(value: number) {
  return Math.max(0.35, Math.min(1, Number.isFinite(value) ? value : 0.94))
}

function setStatus(message: string) {
  if (statusNode) statusNode.label = message
}

function applyWindowSettings() {
  if (!currentWindow) return
  currentWindow.set_opacity(settings.opacity)
  currentWindow.set_decorated(false)
  currentWindow.set_focusable(!settings.locked)
  currentWindow.set_can_focus(!settings.locked)
  const surface = currentWindow.get_surface()
  if (surface && "set_input_region" in surface) {
    if (settings.locked) {
      surface.set_input_region(new Cairo.Region())
    } else {
      surface.set_input_region(null)
    }
  }
  if (GLib.getenv("HYPRLAND_INSTANCE_SIGNATURE")) {
    const focusValue = settings.locked ? "1" : "0"
    void runShell(`hyprctl setprop title:^(LLM Sidebar)$ nofocus ${focusValue} lock`).catch(() => null)
  }
}

function schedulePositionRestore() {
  GLib.timeout_add(GLib.PRIORITY_DEFAULT, 900, () => {
    const x = settings.x ?? 0
    const y = settings.y ?? 0
    void runShell([
      `hyprctl dispatch movewindowpixel exact ${x} ${y},title:^(LLM Sidebar)$`,
      `hyprctl dispatch resizewindowpixel exact 520 100%,title:^(LLM Sidebar)$`,
      `hyprctl dispatch movetoworkspacesilent special:llm-sidebar,title:^(LLM Sidebar)$`,
    ].join(" ; ")).catch(() => null)
    return GLib.SOURCE_REMOVE
  })
}

function pollAndPersistGeometry() {
  if (!GLib.getenv("HYPRLAND_INSTANCE_SIGNATURE")) return
  void execAsync(["bash", "-lc", "hyprctl -j clients"])
    .then(JSON.parse)
    .then((clients) => {
      const client = (clients || []).find((item: any) => item.title === "LLM Sidebar")
      if (!client || !Array.isArray(client.at)) return
      settings.x = Number(client.at[0])
      settings.y = Number(client.at[1])
      saveSettings()
    })
    .catch(() => null)
}

export function toggleLock() {
  settings.locked = !settings.locked
  applyWindowSettings()
  saveSettings()
  setStatus(
    settings.locked
      ? "Sidebar locked: input should pass through to what is behind it. Use keybinds to unlock."
      : "Sidebar unlocked and draggable from the header.",
  )
  return settings.locked
}

export function adjustOpacity(delta: number) {
  settings.opacity = clampOpacity(settings.opacity + delta)
  applyWindowSettings()
  saveSettings()
  setStatus(`Opacity ${(settings.opacity * 100).toFixed(0)}%`)
  return settings.opacity
}

export function refreshSidebar() {
  setStatus("Refreshing...")
  refreshCallback?.()
}

export function currentSettingsSummary() {
  return `locked=${settings.locked} opacity=${settings.opacity.toFixed(2)} position=${settings.x ?? "?"},${settings.y ?? "?"}`
}

export function toggleSidebarWorkspace() {
  void runShell([
    "hyprctl dispatch movetoworkspacesilent special:llm-sidebar,title:^(LLM Sidebar)$",
    "hyprctl dispatch togglespecialworkspace llm-sidebar",
  ].join(" ; ")).catch(() => null)
  return "llm-sidebar"
}

function clearBox(box: Gtk.Box) {
  let child = box.get_first_child()
  while (child) {
    const next = child.get_next_sibling()
    box.remove(child)
    child = next
  }
}

function rowCard(title: string, subtitle: string, focused = false) {
  return (
    <box orientation={Gtk.Orientation.VERTICAL} spacing={6} class={`row-card ${focused ? "focused" : ""}`}>
      <label xalign={0} label={title} />
      <label xalign={0} class="muted" label={subtitle} />
    </box>
  )
}

export default function Sidebar() {
  let entry: Gtk.Entry
  let statusLabel: Gtk.Label
  let transcriptLabel: Gtk.Label
  let workspacesBox: Gtk.Box
  let clientsBox: Gtk.Box

  const refresh = () => {
    if (!statusLabel || !workspacesBox || !clientsBox) return
    runBackend("status")
      .then((payload) => {
        statusLabel.label = payload.message || "Ready."
        const snapshot = payload.state || {}
        const workspaces = snapshot.workspaces || []
        const clients = snapshot.clients || []

        clearBox(workspacesBox)
        if (!workspaces.length) {
          workspacesBox.append(<label xalign={0} class="muted" label="No workspace data yet." />)
        } else {
          workspaces.forEach((workspace: any) => {
            workspacesBox.append(
              rowCard(`${workspace.name} (${workspace.id})`, `${workspace.windows} windows`, Boolean(workspace.focused)),
            )
          })
        }

        clearBox(clientsBox)
        if (!clients.length) {
          clientsBox.append(<label xalign={0} class="muted" label="No client data yet." />)
        } else {
          clients.slice(0, 12).forEach((client: any) => {
            clientsBox.append(
              rowCard(client.title || client.class || "Untitled window", `${client.class || "unknown"} · ws ${client.workspace ?? "?"}`),
            )
          })
        }
      })
      .catch((error) => {
        if (statusLabel) statusLabel.label = String(error)
      })
  }
  refreshCallback = refresh

  const submit = () => {
    if (!entry || !statusLabel || !transcriptLabel) return
    const request = entry.text.trim()
    if (!request) {
      statusLabel.label = "Type a request first."
      return
    }
    transcriptLabel.label = `${transcriptLabel.label}\n\nYou: ${request}\nAssistant: ...`
    entry.text = ""
    statusLabel.label = "Thinking..."

    const escaped = JSON.stringify(request)
    runBackend(`act ${escaped}`)
      .then((payload) => {
        const commands = (payload.commands || []).map((item: any) => `${item.ok ? "ok" : "fail"}: ${item.dispatch}`).join("\n")
        transcriptLabel.label = `${transcriptLabel.label.slice(0, -3)}${payload.message || "Done."}${commands ? `\n${commands}` : ""}`
        statusLabel.label = payload.message || "Done."
        refresh()
      })
      .catch((error) => {
        transcriptLabel.label = `${transcriptLabel.label.slice(0, -3)}Error: ${String(error)}`
        statusLabel.label = String(error)
      })
  }

  GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 3, () => {
    refresh()
    return GLib.SOURCE_CONTINUE
  })

  GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 2, () => {
    pollAndPersistGeometry()
    return GLib.SOURCE_CONTINUE
  })

  return (
    <Gtk.Window
      name="llm-sidebar"
      class="Sidebar"
      application={app}
      title="LLM Sidebar"
      defaultWidth={520}
      defaultHeight={980}
      visible
      resizable
      $={(self) => {
        currentWindow = self
        statusNode = statusLabel
        applyWindowSettings()
        schedulePositionRestore()
        refresh()
      }}
    >
      <box orientation={Gtk.Orientation.VERTICAL} spacing={12} class="shell">
        <box spacing={12} class="header">
          <box orientation={Gtk.Orientation.VERTICAL} spacing={6} hexpand>
            <label xalign={0} class="title" label="Hypr Assistant" />
            <label xalign={0} class="muted" label="Sidebar assistant for Hyprland, projects, questions, and the local tool runtime." />
          </box>
          <button class="ghost" onClicked={() => toggleSidebarWorkspace()}><label label="Toggle" /></button>
          <button class="ghost" onClicked={() => toggleLock()}><label label={settings.locked ? "Unlock" : "Lock"} /></button>
          <button class="ghost" onClicked={() => adjustOpacity(-0.05)}><label label="-" /></button>
          <button class="ghost" onClicked={() => adjustOpacity(0.05)}><label label="+" /></button>
          <button class="ghost" onClicked={() => refresh()}><label label="Refresh" /></button>
        </box>

        <box orientation={Gtk.Orientation.VERTICAL} spacing={12} class="composer">
          <entry $={(self) => (entry = self)} placeholderText="Move active window to workspace 3" onActivate={() => submit()} />
          <box spacing={12}>
            <button class="send" onClicked={() => submit()}><label label="Send" /></button>
            <label $={(self) => (statusLabel = self)} class="muted" xalign={0} label="Ready. Sidebar should open on the special workspace." hexpand />
          </box>
        </box>

        <Gtk.Separator orientation={Gtk.Orientation.HORIZONTAL} />

        <box orientation={Gtk.Orientation.VERTICAL} spacing={12} vexpand class="content">
          <label xalign={0} class="section" label="Transcript" />
          <scrolledwindow vexpand>
            <box orientation={Gtk.Orientation.VERTICAL}>
              <label $={(self) => (transcriptLabel = self)} xalign={0} wrap selectable class="transcript" label="Local Hypr assistant ready." />
            </box>
          </scrolledwindow>

          <label xalign={0} class="section" label="Workspaces" />
          <scrolledwindow vexpand>
            <box orientation={Gtk.Orientation.VERTICAL} spacing={8} $={(self) => (workspacesBox = self)} class="list-box" />
          </scrolledwindow>

          <label xalign={0} class="section" label="Clients" />
          <scrolledwindow vexpand>
            <box orientation={Gtk.Orientation.VERTICAL} spacing={8} $={(self) => (clientsBox = self)} class="list-box" />
          </scrolledwindow>
        </box>
      </box>
    </Gtk.Window>
  )
}
