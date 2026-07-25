import os
from core import storage

# every project gets these three asset buckets by default
ASSET_CATEGORIES = ["Scripts", "Edited Videos", "Thumbnails"]

# only these fields can be set via update_value -- keeps list fields safe
SCALAR_FIELDS = {"title", "status"}


# --- low-level helpers ---

def _resolve_list(project, list_path):
    # returns a reference to the actual list inside the project dict
    # so callers can append/pop/replace in place
    if list_path == "alternate_titles":
        return project.get("alternate_titles")

    if isinstance(list_path, tuple) and list_path[0] == "assets":
        category = list_path[1]
        assets_dict = project.get("assets", {})
        return assets_dict.get(category)

    # unrecognized path
    return None


def _sanitize_asset(asset):
    # make sure each asset entry is a dict with string name and path
    # guards against hand-edited storage.json where someone set path to null or a number
    if not isinstance(asset, dict):
        return {"name": "(unknown file)", "path": ""}

    name = asset.get("name")
    path = asset.get("path")

    clean_name = name if isinstance(name, str) and name else "(unknown file)"
    clean_path = path if isinstance(path, str) else ""

    return {"name": clean_name, "path": clean_path}


# --- project lookups ---

def get_all_projects(data):
    return data["projects"]


def get_project(data, project_id):
    # always cast to string -- ids are stored as "1", "2", etc
    return data["projects"].get(str(project_id))


# --- asset helpers ---

def get_assets(data, project_id, category):
    project = get_project(data, project_id)
    if project is None:
        return []

    raw_assets = project.get("assets", {}).get(category, [])

    # sanitize every entry before returning so downstream code never sees a bad shape
    sanitized = []
    for asset in raw_assets:
        sanitized.append(_sanitize_asset(asset))

    return sanitized


def asset_exists_on_disk(asset):
    path = asset.get("path", "")
    if not path:
        return False
    return os.path.isfile(path)


def make_asset_from_path(path):
    # expand ~ and resolve to absolute so the stored path always works
    # regardless of what directory the user launched the app from
    expanded = os.path.expanduser(path)
    absolute = os.path.abspath(expanded)
    name = os.path.basename(absolute)
    # print(f"make_asset_from_path: {path} -> {absolute}")  # debug
    return {"name": name, "path": absolute}


def get_display_names(assets):
    # build display labels for the asset list
    # if two assets share the same filename, add context to tell them apart
    # tier 1: plain filename
    # tier 2: filename + parent folder
    # tier 3: filename + full path
    # tier 4: filename + list position (always unique, last resort)
    n = len(assets)

    def tier1(i):
        return assets[i]["name"]

    def tier2(i):
        raw_path = assets[i]["path"]
        parent = os.path.basename(os.path.dirname(raw_path.rstrip("/\\")))
        if parent:
            return f"{assets[i]['name']} ({parent})"
        return None  # no parent folder available, skip this tier

    def tier3(i):
        return f"{assets[i]['name']} [{assets[i]['path']}]"

    def tier4(i):
        return f"{assets[i]['name']} (#{i + 1})"

    tiers = [tier1, tier2, tier3, tier4]
    display = [None] * n
    remaining = set(range(n))

    # track names already assigned so a later tier can't produce a duplicate
    # of something a earlier tier already settled
    used_names = set()

    for tier_fn in tiers:
        if not remaining:
            break

        # compute each candidate name for assets still unresolved
        candidates = {}
        for i in remaining:
            candidates[i] = tier_fn(i)

        # count how many unresolved assets map to each candidate at this tier
        counts = {}
        for i in remaining:
            name = candidates[i]
            if name is None:
                continue
            counts[name] = counts.get(name, 0) + 1

        # settle any asset whose candidate is unique at this tier AND not already used
        settled = []
        for i in remaining:
            name = candidates[i]
            is_unique_here = name is not None and counts[name] == 1
            not_already_taken = name not in used_names
            if is_unique_here and not_already_taken:
                display[i] = name
                used_names.add(name)
                settled.append(i)

        remaining -= set(settled)

    # handle anything still unresolved after all four tiers
    # tier4 is index-based so it's normally unique, but a literal filename
    # like "thumb.png (#2)" could collide with it -- bump suffix until clear
    for i in remaining:
        base_name = assets[i]["name"]
        candidate = f"{base_name} (#{i + 1})"

        suffix = 1
        while candidate in used_names:
            candidate = f"{base_name} (#{i + 1}.{suffix})"
            suffix += 1

        display[i] = candidate
        used_names.add(candidate)

    return display


# --- project write operations ---

def create_project(data, title):
    # strip whitespace here so callers don't have to remember to
    title = title.strip()
    new_id = str(data["next_id"])

    data["projects"][new_id] = {
        "title": title,
        "status": "Idea",
        "alternate_titles": [],
        "assets": {category: [] for category in ASSET_CATEGORIES},
    }

    data["next_id"] += 1
    storage.save_data(data)
    # print(f"created project {new_id}: {title}")  # debug
    return new_id


def delete_project(data, project_id):
    project_id = str(project_id)

    if project_id not in data["projects"]:
        return False

    del data["projects"][project_id]
    storage.save_data(data)
    return True


def update_value(data, project_id, field, new_value):
    # guard against accidentally overwriting a list field (assets, alternate_titles)
    if field not in SCALAR_FIELDS:
        raise ValueError(
            f"update_value() cannot set '{field}' -- only {SCALAR_FIELDS} "
            f"are allowed. List fields must use add_to_list/remove_from_list."
        )

    project = get_project(data, project_id)
    if project is None:
        return False

    project[field] = new_value
    storage.save_data(data)
    return True


# --- list operations (work for both alternate_titles and asset lists) ---

def add_to_list(data, project_id, list_path, item):
    # strip strings on the way in so callers don't have to
    if isinstance(item, str):
        item = item.strip()

    project = get_project(data, project_id)
    if project is None:
        return False

    target_list = _resolve_list(project, list_path)
    if target_list is None:
        return False

    target_list.append(item)
    storage.save_data(data)
    return True


def remove_from_list(data, project_id, list_path, index):
    project = get_project(data, project_id)
    if project is None:
        return None

    target_list = _resolve_list(project, list_path)
    if target_list is None:
        return None

    # bounds check before popping
    if index < 0 or index >= len(target_list):
        return None

    removed = target_list.pop(index)
    storage.save_data(data)
    return removed


def replace_in_list(data, project_id, list_path, index, new_item):
    # update in place -- keeps the item at the same position in the list
    if isinstance(new_item, str):
        new_item = new_item.strip()

    project = get_project(data, project_id)
    if project is None:
        return False

    target_list = _resolve_list(project, list_path)
    if target_list is None:
        return False

    if index < 0 or index >= len(target_list):
        return False

    target_list[index] = new_item
    storage.save_data(data)
    return True
