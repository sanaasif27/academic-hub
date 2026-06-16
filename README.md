# Dr. Sana Asif — academic hub

Your personal academic website: write posts, hand out readings to students, and
share teaching materials with colleagues. It is a **static site** (just files —
no database, nothing to hack), edited from your browser like WordPress, and it
costs **nothing** to run.

- **Pages:** Home · About · Writing (blog) · Teaching (students) · Resources (colleagues) · CV · Contact
- **You edit it** in a visual editor at `yoursite.com/admin`
- **It publishes itself** ~30 seconds after you click *Publish*
- **It is public** and search-engine friendly; drafts stay hidden until you're ready

---

## 1. See it on your own computer first (1 minute)

Open Terminal, `cd` into this `AcademicHub` folder, then run:

```sh
python3 build.py && python3 -m http.server 8000 -d _site
```

Now open **http://localhost:8000** in your browser. Press `Ctrl+C` in Terminal to stop.

> Tip: to `cd` into the folder, type `cd ` (with a space) and drag the AcademicHub
> folder from Finder onto the Terminal window, then press Return.

> First time only, install the two tiny tools the build uses:
> `python3 -m pip install --user markdown pyyaml`

---

## 2. Put it online, free (about an hour, one time)

You need two free accounts: **GitHub** (stores your site + every past version) and
**Netlify** (publishes it). Do this once and never again.

### Step A — Put the site on GitHub
1. Create a free account at **github.com**.
2. Click **New repository**, name it `academic-hub`, keep it **Public**, click **Create**.
3. On the new repo page, follow *"upload an existing file"* and drag in **everything
   inside this `AcademicHub` folder** (or use the git commands GitHub shows you).
   - The `_site/` folder does **not** need to be uploaded — it's rebuilt automatically.

### Step B — Publish it with Netlify
1. Create a free account at **netlify.com** and choose *"Log in with GitHub."*
2. Click **Add new site → Import an existing project → GitHub**, pick `academic-hub`.
3. Netlify reads `netlify.toml` and fills in the build settings for you. Click **Deploy**.
4. In ~1 minute your site is live at a free address like `random-name-123.netlify.app`.
   You can rename it under **Project configuration → General → Change site name**
   (older Netlify dashboards label this top section **"Site configuration"**) to e.g.
   `sanaasif.netlify.app`.
5. Open `content/site.yml` (in the editor, later) and set `base_url:` to that address.

Your site is now **live and public**. The last step turns on the editor.

### Step C — Turn on the visual editor (`/admin`)
The editor logs in with your GitHub account. You authorise it once:

1. **Edit a couple of lines:** open `admin/config.yml` and change
   `repo: your-github-username/academic-hub` to your real GitHub username, and
   update `site_url`/`display_url` to your Netlify address (both are flagged with
   `<-- update after deploy`). (You can do this directly on GitHub: open the file
   → pencil icon → commit.)
2. **Create a GitHub OAuth app:** on GitHub go to
   **Settings → Developer settings → OAuth Apps → New OAuth App**. Fill in:
   - *Application name:* `My site editor`
   - *Homepage URL:* your Netlify address (e.g. `https://sanaasif.netlify.app`)
   - *Authorization callback URL:* `https://api.netlify.com/auth/done`
   - Click **Register**, then **Generate a new client secret**. Copy the
     **Client ID** and **Client secret**.
3. **Give them to Netlify:** in your Netlify site, go to
   **Project configuration → Access & security → OAuth → Install provider → GitHub**
   (older dashboards call the top section **"Site configuration"**), and paste the
   Client ID and Secret. Save.
4. Visit **`https://your-site.netlify.app/admin`**, click **Login with GitHub**,
   approve once — and you're in.

> *Note:* This uses GitHub's OAuth through Netlify's OAuth broker. The Netlify
> **Identity / Git Gateway** feature that was retired in 2025 is a *different*
> mechanism — this site does not use it, so that change doesn't affect you.

> **If Step C ever gives you trouble, use the no-setup alternative below instead.**
> Both edit the exact same content; you don't lose anything.

#### Easiest alternative editor — PagesCMS (zero server setup)
If the OAuth steps feel fiddly, skip them and use **PagesCMS**:
1. Go to **https://app.pagescms.org/**, click *Sign in with GitHub*, and install its
   app on your `academic-hub` repo.
2. That's it — you get the same visual editor (it reads the included `.pages.yml`).
No OAuth app, no Netlify settings. The trade-off is that the editor is hosted by
PagesCMS (it only touches your repo); your live site stays 100% yours on Netlify.

---

## 3. Using it day to day (the "WordPress" part)

Go to **`yoursite.com/admin`** (or **app.pagescms.org**) and log in. You'll see these sections:

| Section | What it's for |
|---|---|
| **Writing (blog posts)** | Write an article. Title, date, a short summary, tags, optional cover image, and the body in a rich editor. Tick **Save as draft** to keep it hidden. |
| **Teaching — for students** | Upload a handout/reading. Add a title, course, description, and **drag in the PDF/DOCX**. It appears as a download button on `/teaching/`. |
| **Resources — for colleagues** | Same idea, for teaching materials you share with other instructors, with an optional license note. |
| **Pages** | Edit the Home hero, About, CV, and Contact pages. Upload your CV as a PDF and it becomes a download button. |
| **Site settings** | Your name, role, institution, tagline, email, social links, and the top menu. |

**To publish:** fill in the fields, click **Publish** (Decap) or **Save** (PagesCMS).
Wait ~30 seconds and refresh your live site — it's there. Every change is saved in
GitHub, so nothing is ever truly lost and any edit can be undone.

---

## 4. The one thing to remember

You only ever touch two kinds of things:

- **Content** → through the `/admin` editor (or by editing files in `content/`).
- **Look & layout** → `assets/css/site.css` and `build.py`. You rarely need these;
  they're plain and commented if you ever want to tweak the design.

---

## 5. Folder map

```
AcademicHub/
├─ content/              ← everything you write (the editor saves here)
│  ├─ site.yml           ← name, nav, links, your live address
│  ├─ pages/             ← home, about, cv, contact
│  ├─ posts/             ← blog posts
│  ├─ students/          ← handouts/readings for students
│  └─ colleagues/        ← teaching materials for colleagues
├─ assets/
│  ├─ css/site.css       ← the design (colours, fonts, layout)
│  ├─ js/site.js         ← tiny menu + reading-progress script
│  ├─ img/               ← favicon, images
│  └─ uploads/           ← files you upload in the editor land here
├─ admin/                ← the visual editor (Decap CMS)
│  ├─ index.html
│  └─ config.yml         ← editor settings (change the `repo:` line)
├─ build.py              ← turns content/ into the finished site
├─ netlify.toml          ← build settings + security headers
├─ requirements.txt      ← the two Python libraries the build needs
├─ .pages.yml            ← config for the PagesCMS alternative editor
└─ _site/                ← the built website (auto-generated; don't edit)
```

---

## 6. Why this is "top notch secure"

- **No database, no server code, no plugins** — the three things that get sites
  hacked. Attackers have almost nothing to push on.
- **HTTPS everywhere**, free, automatic, via Netlify.
- **Hardened HTTP headers** (HSTS, clickjacking + MIME-sniffing protection, a
  Content-Security-Policy) are set in `netlify.toml`.
- **Full version history** in GitHub — every change is recorded and reversible.
- The editor login is your **GitHub account** (turn on 2-factor for it).

### Optional: maximum privacy
The site loads two fonts (Fraunces, Inter) from Google Fonts. If you'd rather make
zero third-party requests, tell me and I'll self-host the fonts — the site falls
back to elegant Georgia either way.

---

## 7. Optional: a custom domain
Free is `yourname.netlify.app`. For ~$12/year you can buy `drsanaasif.com` and point
it at Netlify in a few clicks (**Domain management → Add a domain**). Ask me and I'll
walk you through it.
