#!/usr/bin/env python3
import zipfile
import pathlib

skill_path = pathlib.Path("c:/private/treevvo-lambda/skills/treevvo.skill")
skills_dir = pathlib.Path.home() / ".claude" / "skills"
skills_dir.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(skill_path) as z:
    print("Contents:", z.namelist())
    z.extractall(skills_dir)

print("Extracted to:", skills_dir)
print("Files:", sorted(str(p) for p in skills_dir.rglob("*")))
