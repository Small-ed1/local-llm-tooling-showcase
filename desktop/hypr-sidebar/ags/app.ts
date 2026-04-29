import app from "ags/gtk4/app"
import style from "./style.css"
import Sidebar, {
  adjustOpacity,
  currentSettingsSummary,
  refreshSidebar,
  toggleSidebarWorkspace,
  toggleLock,
} from "./widget/Sidebar"

app.start({
  instanceName: "tooling-showcase-sidebar",
  css: style,
  requestHandler(argv, response) {
    const command = (argv[0] || "").trim()
    if (!command || command === "request") {
      response("ok")
      return
    }
    if (command === "toggle-lock") {
      response(toggleLock() ? "locked" : "unlocked")
      return
    }
    if (command === "toggle-sidebar") {
      response(toggleSidebarWorkspace())
      return
    }
    if (command === "opacity-up") {
      response(`opacity=${adjustOpacity(0.05).toFixed(2)}`)
      return
    }
    if (command === "opacity-down") {
      response(`opacity=${adjustOpacity(-0.05).toFixed(2)}`)
      return
    }
    if (command === "refresh") {
      refreshSidebar()
      response("refresh requested")
      return
    }
    if (command === "settings") {
      response(currentSettingsSummary())
      return
    }
    response("ok")
  },
  main() {
    Sidebar()
  },
})
