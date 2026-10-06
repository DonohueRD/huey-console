# How to Push to GitHub

This guide walks you through getting the HUEY Console project on GitHub. All files have been sanitized to remove network paths, IP addresses, and personal information.

## What Was Sanitized

Before pushing, the following sensitive information was removed or obfuscated:

- ✅ Network paths (e.g., `192.168.1.12`, `192.168.1.169`)
- ✅ Bluetooth device MAC addresses
- ✅ SSH key references
- ✅ Full home folder paths (replaced with placeholders)
- ✅ Device-specific configuration values

**Files to note:**
- `carts.json.example` — a template showing the structure (use this as reference)
- `.gitignore` — prevents accidentally committing sensitive files

## Push Instructions

These files are ready to push to your GitHub repo: `git@github.com:DonohueRD/huey-console.git`

### Using Git (Command Line)

```bash
# Navigate to the repo directory (this scratchpad)
cd huey-console

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial HUEY console commit: software, hardware (STL/SCAD), docs, and build guides"

# Add remote (if not already done)
git remote add origin git@github.com:DonohueRD/huey-console.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### If You Already Have a Repo

If your repo already exists with files, merge instead:

```bash
# Pull existing content
git pull origin main

# Add new files
git add .

# Commit
git commit -m "Add hardware STLs, build guides, and complete software setup"

# Push
git push origin main
```

## What's Included

```
huey-console/
├── README.md                 # Project overview and quick start
├── .gitignore               # Git rules (keeps sensitive files out)
├── software/                # Python daemon and tools
│   ├── cartridge_daemon.py  # Main console software
│   ├── add_cart.py          # Cartridge registration tool
│   ├── cartridge_3.service  # Systemd service (adapt to your paths)
│   ├── install_cores.sh     # Fetch libretro cores
│   ├── PressStart2P.ttf     # Console font
│   └── carts.json.example   # Template for cartridge mapping
├── hardware/                # 3D printing files
│   ├── huey_walnut_v1/      # Current console enclosure
│   ├── huey_cart_v3/        # Current cartridge design
│   └── huey_station_v1/     # Older capsule variant (reference)
├── docs/                    # Project documentation
│   ├── PROJECT_HISTORY.md   # Full project history and decisions
│   └── CLAUDE.md            # Development notes (adapt to your setup)
└── splash/                  # Splash screen renderer and assets
    └── huey_splash_ps1.py   # Render script for custom variants
```

## Blog Integration

To connect this to your blog at `blog.hueyserver.dev`, add a post like:

```markdown
# Building HUEY: Episode 1 - The Console Daemon

Check out the full source code on GitHub: https://github.com/DonohueRD/huey-console

[Your narrative and deep dives here...]
```

Then link back to GitHub whenever referencing code or STL files.

## After Pushing

1. **Check the repo looks good:** `https://github.com/DonohueRD/huey-console`
2. **Write your first blog post** on `blog.hueyserver.dev` — link to the GitHub repo and specific files
3. **Keep syncing:** When you make changes on your Pi or NAS, push them to keep the repo up to date
4. **Document as you build** — rough notes in `docs/` are fine; flesh them out in blog posts

## Tips for Ongoing Documentation

- **Update `README.md`** whenever a major feature is added or changed
- **Keep `PROJECT_HISTORY.md`** current with decisions and why they matter (helps future you and others)
- **Push regularly** — even rough work-in-progress is better than stale repo
- **Blog posts can link to commits** — e.g., "See the controller code here: `github.com/DonohueRD/huey-console/blob/main/software/cartridge_daemon.py#L179`"

## Customizing for Your Setup

A few files reference paths that may differ on your Pi:

- **`software/cartridge_daemon.py` line 40-43**: ROM and core directory paths
- **`software/add_cart.py` line 24**: Network share path (adjust to your NAS mount)
- **`software/cartridge_3.service`**: User and group (should be `pi`)

These are designed to be forked and customized per setup — leave the defaults as-is for a clean reference, or adjust if publishing as a guide.

---

**Ready to push?** Run the git commands above, and your project is live!
