from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>URL Shortener</title>
  <style>
    :root {
      --bg: #f7f8fb;
      --panel: #ffffff;
      --text: #172033;
      --muted: #667085;
      --line: #d9e0ea;
      --accent: #087f8c;
      --accent-dark: #066672;
      --success-bg: #edfdf6;
      --success-line: #9ee6c3;
      --danger-bg: #fff1f2;
      --danger-line: #fecdd3;
      --shadow: 0 18px 50px rgba(23, 32, 51, 0.12);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        linear-gradient(135deg, rgba(8, 127, 140, 0.08), rgba(249, 180, 45, 0.08)),
        var(--bg);
      color: var(--text);
    }

    main {
      width: min(920px, calc(100% - 32px));
      margin: 0 auto;
      padding: 56px 0;
    }

    .app-shell {
      display: grid;
      gap: 24px;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 20px;
      flex-wrap: wrap;
    }

    h1 {
      margin: 0;
      font-size: clamp(2rem, 3vw, 3rem);
      line-height: 1.05;
      letter-spacing: 0;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      min-height: 36px;
      padding: 0 12px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.72);
      color: var(--muted);
      font-size: 0.9rem;
      white-space: nowrap;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 28px;
    }

    form {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: end;
    }

    label {
      display: grid;
      gap: 8px;
      color: var(--muted);
      font-size: 0.95rem;
      font-weight: 600;
    }

    input {
      width: 100%;
      height: 52px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0 16px;
      color: var(--text);
      font-size: 1rem;
      outline: none;
    }

    input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 4px rgba(8, 127, 140, 0.14);
    }

    button {
      height: 52px;
      border: 0;
      border-radius: 8px;
      padding: 0 20px;
      background: var(--accent);
      color: white;
      font-size: 1rem;
      font-weight: 700;
      cursor: pointer;
    }

    button:hover {
      background: var(--accent-dark);
    }

    button:disabled {
      cursor: wait;
      opacity: 0.68;
    }

    .result {
      display: none;
      margin-top: 22px;
      border: 1px solid var(--success-line);
      border-radius: 8px;
      background: var(--success-bg);
      padding: 18px;
    }

    .result.visible {
      display: grid;
      gap: 14px;
    }

    .result-row {
      display: flex;
      gap: 12px;
      align-items: center;
    }

    .short-link {
      min-width: 0;
      flex: 1;
      color: var(--accent-dark);
      font-size: 1.12rem;
      font-weight: 800;
      overflow-wrap: anywhere;
    }

    .copy-button {
      flex: 0 0 auto;
      height: 40px;
      padding: 0 14px;
      background: #172033;
    }

    .meta {
      display: grid;
      gap: 4px;
      color: var(--muted);
      font-size: 0.92rem;
      overflow-wrap: anywhere;
    }

    .error {
      display: none;
      margin-top: 18px;
      border: 1px solid var(--danger-line);
      border-radius: 8px;
      background: var(--danger-bg);
      color: #9f1239;
      padding: 14px 16px;
      font-weight: 650;
    }

    .error.visible {
      display: block;
    }

    @media (max-width: 680px) {
      main {
        width: min(100% - 24px, 920px);
        padding: 28px 0;
      }

      .panel {
        padding: 20px;
      }

      form,
      .result-row {
        grid-template-columns: 1fr;
        display: grid;
      }

      button,
      .copy-button {
        width: 100%;
      }
    }
  </style>
</head>
<body>
  <main>
    <section class="app-shell" aria-label="URL shortener">
      <div class="header">
        <h1>URL Shortener</h1>
        <div class="status-pill">Links expire after 24 hours</div>
      </div>

      <div class="panel">
        <form id="shorten-form">
          <label>
            Long URL
            <input id="long-url" name="long_url" type="url" placeholder="https://example.com/very/long/url" required>
          </label>
          <button id="submit-button" type="submit">Shorten</button>
        </form>

        <div id="error" class="error" role="alert"></div>

        <section id="result" class="result" aria-live="polite">
          <div class="result-row">
            <a id="short-link" class="short-link" href="#" target="_blank" rel="noreferrer"></a>
            <button id="copy-button" class="copy-button" type="button">Copy</button>
          </div>
          <div class="meta">
            <span id="expires-at"></span>
            <span id="original-url"></span>
          </div>
        </section>
      </div>
    </section>
  </main>

  <script>
    const form = document.querySelector("#shorten-form");
    const input = document.querySelector("#long-url");
    const submitButton = document.querySelector("#submit-button");
    const result = document.querySelector("#result");
    const errorBox = document.querySelector("#error");
    const shortLink = document.querySelector("#short-link");
    const copyButton = document.querySelector("#copy-button");
    const expiresAt = document.querySelector("#expires-at");
    const originalUrl = document.querySelector("#original-url");
    let currentShortUrl = "";

    function showError(message) {
      errorBox.textContent = message;
      errorBox.classList.add("visible");
      result.classList.remove("visible");
    }

    function clearError() {
      errorBox.textContent = "";
      errorBox.classList.remove("visible");
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearError();
      submitButton.disabled = true;
      submitButton.textContent = "Shortening";

      try {
        const response = await fetch("/api/urls", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ long_url: input.value.trim() }),
        });

        if (!response.ok) {
          throw new Error("Enter a valid URL including http:// or https://.");
        }

        const data = await response.json();
        currentShortUrl = data.short_url;
        shortLink.href = data.short_url;
        shortLink.textContent = data.short_url;
        expiresAt.textContent = `Expires: ${new Date(data.expires_at).toLocaleString()}`;
        originalUrl.textContent = `Original: ${data.long_url}`;
        copyButton.textContent = "Copy";
        result.classList.add("visible");
      } catch (error) {
        showError(error.message || "Could not shorten this URL.");
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Shorten";
      }
    });

    copyButton.addEventListener("click", async () => {
      if (!currentShortUrl) return;
      await navigator.clipboard.writeText(currentShortUrl);
      copyButton.textContent = "Copied";
    });
  </script>
</body>
</html>
"""

