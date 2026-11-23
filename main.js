(() => {
  const shell = document.getElementById("shell");
  const output = document.getElementById("output");
  const form = document.getElementById("prompt");
  const input = document.getElementById("command");
  const history = [];
  let cursor = 0;

  const jump = (id) => {
    document.getElementById(id).scrollIntoView();
    return `Moved to ${id}.`;
  };

  const go = (path) => {
    window.location.href = path;
    return `Opening ${path}`;
  };

  const links = {
    github: "https://github.com/TonyD365",
    ytktv: "https://github.com/TonyD365/YTKTV",
    lanpair: "https://github.com/TonyD365/lanpair",
    inkhue: "https://github.com/TonyD365/Inkhue",
    roickbot: "https://github.com/TonyD365/Roickbot",
    "chess-coach": "https://github.com/TonyD365/Chess-Coach",
  };

  const commands = {
    help: () => "Commands: whoami, projects, ytktv, lanpair, blog, now, contact, open <name>, clear",
    whoami: () => jump("about"),
    projects: () => go("/Projects/"),
    ytktv: () => go("/Projects/YTKTV/"),
    lanpair: () => go("/Projects/lanpair/"),
    now: () => jump("now"),
    blog: () => go("/Blog/"),
    contact: () => go("/Contact/"),
    open: (name) => {
      const url = links[(name || "").toLowerCase()];
      if (!url) return `Usage: open <${Object.keys(links).join("|")}>`;
      window.open(url, "_blank", "noopener");
      return `Opening ${url}`;
    },
    clear: () => {
      output.textContent = "";
      return "";
    },
  };

  const print = (text) => {
    if (!text) return;
    const line = document.createElement("div");
    line.textContent = text;
    output.append(line);
  };

  shell.hidden = false;

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const raw = input.value.trim();
    input.value = "";
    if (!raw) return;
    history.push(raw);
    cursor = history.length;
    const [name, arg] = raw.split(/\s+/);
    const key = name.toLowerCase();
    print(`$ ${raw}`);
    const run = Object.hasOwn(commands, key) ? commands[key] : null;
    print(run ? run(arg) : `command not found: ${name}. Try help.`);
  });

  input.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowUp" && event.key !== "ArrowDown") return;
    event.preventDefault();
    cursor = Math.max(0, Math.min(history.length, cursor + (event.key === "ArrowUp" ? -1 : 1)));
    input.value = history[cursor] || "";
  });
})();
