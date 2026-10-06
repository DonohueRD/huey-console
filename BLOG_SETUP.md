# Blog Setup for HUEY Console Journey

Document your build journey on `blog.hueyserver.dev` while keeping the code and files on GitHub.

## Setup Checklist

### 1. GitHub (Done ✅)
- [x] Repository created: `git@github.com:DonohueRD/huey-console.git`
- [x] Files ready to push
- [ ] Push to GitHub (see `PUSH_TO_GITHUB.md`)

### 2. Blog Site (`blog.hueyserver.dev`)
- [ ] Choose a blogging platform:
  - **Option A (Fastest):** GitHub Pages + Jekyll
    - Markdown files in `/docs` folder
    - Auto-renders to a website
    - Free, no extra setup
  - **Option B:** Existing WordPress/custom site
    - Richer editing experience
    - More themes and customization
  - **Option C:** Static site generator (Hugo, Gatsby)
    - Powerful and flexible
    - Requires more setup

### 3. First Blog Post Template

Use this structure for each build log entry:

```markdown
---
date: 2026-10-06
title: "Building HUEY: Console Daemon & Controller Support"
---

# Building HUEY: Console Daemon & Controller Support

## What I Did This Week

- [Brief summary of accomplishments]

## Technical Deep Dive

### The Controller Detection Problem

[Explain the challenge...]

### The Solution

[How you solved it, with code snippets]

```python
# Example from the console daemon
def connected_pads():
    # Your code here
    ...
```

Link to the full file: [cartridge_daemon.py](https://github.com/DonohueRD/huey-console/blob/main/software/cartridge_daemon.py#L184)

## Next Steps

- Register more cartridges
- Test Bluetooth pairing
- [Your next goal]

## Files This Affects

- [`software/cartridge_daemon.py`](https://github.com/DonohueRD/huey-console/blob/main/software/cartridge_daemon.py) — main daemon + controller thread
- [`hardware/huey_walnut_v1/`](https://github.com/DonohueRD/huey-console/tree/main/hardware/huey_walnut_v1/) — enclosure (unchanged)
```

## Workflow

1. **Work on the console** (code, hardware, config)
2. **Push to GitHub** when you reach a milestone
3. **Write a blog post** about what you built and why
4. **Link to the code** so people can see the implementation
5. **Update `docs/PROJECT_HISTORY.md`** with decisions for future reference

## Blog Post Ideas (Build Your Journey)

- [ ] **Ep 1: The Dream** — Why you built this, what inspired the design
- [ ] **Ep 2: Hardware Assembly** — 3D printing, soldering, testing the NFC reader
- [ ] **Ep 3: Console Daemon** — Writing the main event loop and game launcher
- [ ] **Ep 4: Cartridges** — Designing and printing the cart shells, setting up NFC tags
- [ ] **Ep 5: The Display** — Custom splash art, variant system, animation tuning
- [ ] **Ep 6: Controllers** — Bluetooth auto-pairing, input detection, on-screen status
- [ ] **Ep 7: Deep Dive: The Freezing Bug** — How you diagnosed and fixed the splash freeze
- [ ] **Ep 8: Moonlight Streaming** — Extending beyond the Pi for N64/PS2
- [ ] **Final: Retrospective** — What worked, what you'd change, lessons learned

## Post-Writing Checklist

For each blog post:

- [ ] Include photos/screenshots of the hardware
- [ ] Link to relevant GitHub files (at specific lines/commits if possible)
- [ ] Explain the why, not just the what
- [ ] Include code snippets for technical posts
- [ ] Link back to previous episodes
- [ ] Update the README or GitHub if there are new instructions

## Example Links to GitHub

```markdown
<!-- Full file -->
[View the daemon](https://github.com/DonohueRD/huey-console/blob/main/software/cartridge_daemon.py)

<!-- Specific line -->
[Controller detection logic](https://github.com/DonohueRD/huey-console/blob/main/software/cartridge_daemon.py#L184)

<!-- Diff of a change -->
[Bluetooth fix commit](https://github.com/DonohueRD/huey-console/commit/abc123...)

<!-- File range -->
[Splash animation](https://github.com/DonohueRD/huey-console/blob/main/software/cartridge_daemon.py#L631-L690)
```

## Timeline

- **Week 1:** Push to GitHub, write Ep 1 + Ep 2 (dream & hardware)
- **Week 2:** Write Ep 3 (daemon) once code is stable
- **Ongoing:** Post every 1-2 weeks as you build
- **Final:** Retrospective after the console is fully assembled

---

Ready to blog? Draft your first post and let's refine it together!
