# Bug Bounty Lab (Python)

Local-first legal bug bounty training platform with a flag submission system inspired by CTF/THM style workflows.

## Features

- User registration and login
- Organized bounty challenges (category, difficulty, points)
- Flag submission and solve tracking
- Auto score calculation
- Scoreboard and rank list
- SQLite database with automatic challenge seeding
- 20+ local-safe bounty entries across multiple categories
- Built-in smoke test to validate full flow

## Safety / Legal

Use this project only for:

- Your own local lab targets
- Systems you own
- Environments where you have explicit written permission

Do not use against unauthorized websites or services.

## Quick Start (Windows / PowerShell)

```powershell
cd "c:\Users\Abdo\Desktop\ctf program\bugbounty_lab"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open:

- http://127.0.0.1:5000

Start local vulnerable target labs in another terminal:

```powershell
cd "c:\Users\Abdo\Desktop\ctf program\bugbounty_lab"
python target_lab.py
```

Target lab URL:

- http://127.0.0.1:5001

## Verify Everything Works

```powershell
python smoke_test.py
python target_lab_smoke_test.py
```

Expected output:

`Smoke test passed: register/login/submit/scoreboard flow works.`
`Target lab smoke test passed: all bounty flags reachable.`

## Project Structure

```text
bugbounty_lab/
  app.py
  requirements.txt
  lab/
    __init__.py
    config.py
    models.py
    seed.py
  templates/
  static/
```

## Customize Challenges

Edit `lab/seed.py` and update:

- title
- description
- objective
- local_target
- flag
- points

Restart app after updates.
