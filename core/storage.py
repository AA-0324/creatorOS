import json
import os

# figure out the project root from this file's location
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_PATH = os.path.join(_BASE_DIR, "data", "storage.json")


def _quarantine_corrupted_file():
    # move the broken file out of the way so the next save doesn't overwrite it
    backup_path = STORAGE_PATH + ".corrupted.bak"

    # don't clobber an existing backup -- bump a counter until we find a free name
    counter = 1
    while os.path.exists(backup_path):
        backup_path = f"{STORAGE_PATH}.corrupted.{counter}.bak"
        counter += 1

    try:
        os.replace(STORAGE_PATH, backup_path)
        # rename worked -- caller can tell the user where the file went
        return backup_path, True
    except OSError:
        # rename failed (permissions, read-only fs, etc.)
        # return the original path so the warning message is still accurate
        return STORAGE_PATH, False


def load_data():
    # no file at all = fresh install, just start empty
    if not os.path.exists(STORAGE_PATH):
        return {"projects": {}, "next_id": 1}, None

    try:
        with open(STORAGE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # check projects is actually a dict (could be a list or null if hand-edited)
        projects_val = data.get("projects")
        if not isinstance(projects_val, dict):
            data["projects"] = {}

        # check next_id is an int -- a string or null here would crash create_project
        next_id_val = data.get("next_id")
        if not isinstance(next_id_val, int):
            # don't just reset to 1 -- that could collide with existing project ids
            # instead, find the highest existing numeric id and go one above it
            existing_ids = []
            for key in data["projects"].keys():
                try:
                    existing_ids.append(int(key))
                except (ValueError, TypeError):
                    continue
            if existing_ids:
                data["next_id"] = max(existing_ids) + 1
            else:
                data["next_id"] = 1

        # print(data)  # debug: inspect raw loaded data
        return data, None

    except (json.JSONDecodeError, OSError) as e:
        # file is broken -- move it out of the way and warn the user
        backup_path, quarantined = _quarantine_corrupted_file()

        if quarantined:
            # rename succeeded, user can go find the backup
            warning = (
                f"Your save file was corrupted and could not be read ({e}).\n"
                f"Starting with an empty project list so the app can run.\n"
                f"The damaged file was NOT deleted -- it was saved to:\n"
                f"  {backup_path}\n"
                f"If you know how, you can inspect that file to try to recover your data."
            )
        else:
            # rename failed -- the broken file is still sitting at the original path
            # and will get overwritten the next time the user does anything
            warning = (
                f"Your save file was corrupted and could not be read ({e}).\n"
                f"Starting with an empty project list so the app can run.\n"
                f"CreatorOS could ALSO NOT back up the damaged file at:\n"
                f"  {backup_path}\n"
                f"It is still there, still corrupted, and NOT safely copied.\n"
                f"If you want any chance of recovering your old data, close\n"
                f"this program now and manually copy that file elsewhere\n"
                f"before doing anything else -- the next save in this\n"
                f"session will overwrite it permanently."
            )

        return {"projects": {}, "next_id": 1}, warning


def save_data(data):
    # write to a temp file first, then rename -- avoids a half-written file if we crash mid-save
    os.makedirs(os.path.dirname(STORAGE_PATH), exist_ok=True)
    temp_path = STORAGE_PATH + ".tmp"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # atomic replace -- old file is never partially overwritten
    os.replace(temp_path, STORAGE_PATH)
