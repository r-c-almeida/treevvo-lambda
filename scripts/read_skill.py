import zipfile, pathlib

skill_path = pathlib.Path(r"c:\private\treevvo-lambda\.claude\treevvo.skill")
skills_dir = pathlib.Path.home() / ".claude" / "skills"
skills_dir.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(skill_path) as z:
    print("Contents:", z.namelist())
    z.extractall(skills_dir)

print("Installed to:", skills_dir)
print("Files:", sorted(str(p) for p in skills_dir.rglob("*")))
