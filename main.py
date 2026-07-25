from core import storage, projects, utils

# dashboard truncates long titles to keep the list tidy
DASHBOARD_TITLE_MAX = 50

# how many projects to show per page
PAGE_SIZE = 10


# --- small utilities ---

def clear_screen():
    import os
    # cls for windows, clear for mac/linux
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\nPress Enter to continue...")


def truncate(text, max_len):
    # shorten for display only -- never touches the stored value
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def safe_int(text):
    # try to parse as int, return None instead of crashing
    # using try/except instead of isdigit() because isdigit() returns True
    # for some unicode characters that int() then refuses to parse
    try:
        return int(text)
    except (ValueError, TypeError):
        return None


# --- screen 1: dashboard ---

def show_dashboard(data):
    # page persists across project visits within a session
    page = 0

    while True:
        clear_screen()
        print("-- CREATOROS --")
        print("What are we working on today?\n")

        # grab all project ids in insertion order
        project_ids = list(data["projects"].keys())
        total = len(project_ids)

        # figure out how many pages we need
        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

        # clamp page index in case projects were deleted and we're now past the end
        if page >= total_pages:
            page = total_pages - 1
        if page < 0:
            page = 0

        # slice out just the ids for this page
        start = page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_ids = project_ids[start:end]

        # print each project on this page
        for i, pid in enumerate(page_ids, start=1):
            project = data["projects"][pid]
            display_title = truncate(project["title"], DASHBOARD_TITLE_MAX)
            print(f"{i}. {display_title} [{project['status']}]")

        # create option always sits right after the last listed project
        create_option = len(page_ids) + 1
        print(f"{create_option}. Create New Project")

        # only show nav options that are actually usable
        nav_parts = []
        if page > 0:
            nav_parts.append("P. Prev Page")
        if end < total:
            nav_parts.append("N. Next Page")

        if nav_parts:
            print(f"\n{' | '.join(nav_parts)}")
            print(f"(Page {page + 1} of {total_pages})")

        print("\n0. Exit Application")
        print("____")

        choice = input("> ").strip()
        choice_lower = choice.lower()

        if choice == "0":
            print("\nShutting down. See you next session.")
            return

        # handle pagination
        if choice_lower == "n" and end < total:
            page += 1
            continue

        if choice_lower == "p" and page > 0:
            page -= 1
            continue

        # handle numeric selection
        choice_num = safe_int(choice)
        if choice_num is not None:
            if choice_num == create_option:
                handle_create_project(data)
                continue
            if 1 <= choice_num <= len(page_ids):
                selected_id = page_ids[choice_num - 1]
                show_project_page(data, selected_id)
                continue

        print("\n[!] Invalid input, try again")
        pause()


def handle_create_project(data):
    clear_screen()
    print("-- CREATE NEW PROJECT --\n")

    title = input("Enter a title for the new project: ").strip()

    # reject empty input
    if not title:
        print("\n[!] Invalid input, try again")
        pause()
        return

    projects.create_project(data, title)
    print(f"\nCreated '{title}' as a new project.")
    pause()


# --- screen 2: project page ---

def show_project_page(data, project_id):
    while True:
        project = projects.get_project(data, project_id)

        # project might have been deleted -- bail back to dashboard
        if project is None:
            return

        clear_screen()
        # show full title here -- this screen has room, unlike the dashboard list
        print(f"PROJECT: {project['title']}")
        print(f"Status: {project['status']}\n")

        # alternate titles section
        print("Alternate Titles:")
        alt_titles = project["alternate_titles"]
        if alt_titles:
            for alt in alt_titles:
                print(f"- {alt}")
        else:
            print("(none yet)")

        # asset category links
        print("\nAssets:")
        categories = projects.ASSET_CATEGORIES
        for i, category in enumerate(categories, start=1):
            print(f"{i}. {category}")

        # action options -- numbered right after the asset categories
        edit_status_num    = len(categories) + 1
        add_alt_title_num  = len(categories) + 2
        delete_project_num = len(categories) + 3
        back_num           = len(categories) + 4

        print(f"\nOptions:")
        print(f"{edit_status_num}. Edit Status")
        print(f"{add_alt_title_num}. Add Alternate Title")
        print(f"{delete_project_num}. Delete Project")
        print(f"{back_num}. Back")
        print("____")

        choice = input("> ").strip()
        choice_num = safe_int(choice)

        # reject non-numeric input
        if choice_num is None:
            print("\n[!] Invalid input, try again")
            pause()
            continue

        # route to the right handler
        if 1 <= choice_num <= len(categories):
            category = categories[choice_num - 1]
            show_asset_submenu(data, project_id, category)

        elif choice_num == edit_status_num:
            handle_edit_status(data, project_id)

        elif choice_num == add_alt_title_num:
            handle_add_alt_title(data, project_id)

        elif choice_num == delete_project_num:
            deleted = handle_delete_project(data, project_id, project["title"])
            if deleted:
                return  # project is gone, go back to dashboard

        elif choice_num == back_num:
            return

        else:
            print("\n[!] Invalid input, try again")
            pause()


def handle_edit_status(data, project_id):
    clear_screen()
    print("-- EDIT STATUS --\n")

    new_status = input("Enter new status: ").strip()

    if not new_status:
        print("\n[!] Invalid input, try again")
        pause()
        return

    success = projects.update_value(data, project_id, "status", new_status)

    if success:
        print(f"\nStatus updated to '{new_status}'.")
    else:
        print("\n[!] Could not update status -- project no longer exists.")

    pause()


def handle_add_alt_title(data, project_id):
    clear_screen()
    print("-- ADD ALTERNATE TITLE --\n")

    new_title = input("Enter alternate title: ").strip()

    if not new_title:
        print("\n[!] Invalid input, try again")
        pause()
        return

    success = projects.add_to_list(data, project_id, "alternate_titles", new_title)

    if success:
        print(f"\nAdded '{new_title}' as an alternate title.")
    else:
        print("\n[!] Could not add title -- project no longer exists.")

    pause()


def handle_delete_project(data, project_id, title):
    clear_screen()
    print("-- DELETE PROJECT --\n")
    print(f"This will permanently remove '{title}' from CreatorOS.")
    print("Linked files on your computer will NOT be deleted -- only")
    print("the tracking entries inside CreatorOS will be removed.\n")

    # require the user to type the exact title -- makes accidental deletion hard
    confirm = input("Type the project's exact title to confirm deletion: ").strip()

    if confirm != title:
        print("\nTitle did not match. Deletion cancelled.")
        pause()
        return False

    success = projects.delete_project(data, project_id)

    if success:
        print(f"\n'{title}' has been deleted.")
    else:
        print("\n[!] Could not delete -- project no longer exists.")

    pause()
    return success


# --- screen 3: asset submenu (same layout for scripts, videos, thumbnails) ---

def show_asset_submenu(data, project_id, category):
    while True:
        # re-fetch on every loop so the list is always current after add/delete/edit
        assets = projects.get_assets(data, project_id, category)
        display_names = projects.get_display_names(assets)

        clear_screen()
        print(f"-- {category.upper()} MANAGEMENT --\n")

        if assets:
            for i, name in enumerate(display_names, start=1):
                print(f"{i}. {name}")
        else:
            print("(no files linked yet)")

        print("\nA. Add Asset | D. Delete Asset | E. Edit Path | O. Open Asset | B. Back")
        print("____")

        choice = input("> ").strip()
        choice_lower = choice.lower()

        if choice_lower == "a":
            handle_add_asset(data, project_id, category)
        elif choice_lower == "d":
            handle_delete_asset(data, project_id, category, assets, display_names)
        elif choice_lower == "e":
            handle_edit_asset(data, project_id, category, assets, display_names)
        elif choice_lower == "o":
            handle_open_asset(data, project_id, category, assets, display_names)
        elif choice_lower == "b":
            return
        else:
            print("\n[!] Invalid input, try again")
            pause()


def handle_add_asset(data, project_id, category):
    clear_screen()
    print(f"-- ADD {category.upper()} --\n")

    path = input("Paste the full file path: ").strip()

    if not path:
        print("\n[!] Invalid input, try again")
        pause()
        return

    # expand ~ and make absolute before storing
    asset = projects.make_asset_from_path(path)

    # check if the file actually exists
    file_exists = projects.asset_exists_on_disk(asset)

    if not file_exists:
        print(f"\n[!] No file found at that path:")
        print(f"  {path}")
        confirm = input("Link it anyway? (y/n): ").strip().lower()
        if confirm != "y":
            print("\nNot linked.")
            pause()
            return

    success = projects.add_to_list(data, project_id, ("assets", category), asset)

    if success:
        print(f"\nLinked '{asset['name']}'.")
    else:
        print("\n[!] Could not link file -- project no longer exists.")

    pause()


def handle_delete_asset(data, project_id, category, assets, display_names):
    # nothing to delete
    if not assets:
        print("\n[!] No assets to delete")
        pause()
        return

    clear_screen()
    print(f"-- DELETE {category.upper()} --\n")

    for i, name in enumerate(display_names, start=1):
        print(f"{i}. {name}")

    choice = input("\nEnter the number of the file to remove: ").strip()
    choice_num = safe_int(choice)

    # validate selection
    if choice_num is None or not (1 <= choice_num <= len(assets)):
        print("\n[!] Invalid input, try again")
        pause()
        return

    index = choice_num - 1
    removed_name = display_names[index]

    removed = projects.remove_from_list(data, project_id, ("assets", category), index)

    if removed:
        print(f"\nRemoved '{removed_name}' from {category}.")
    else:
        print("\n[!] Could not remove file -- project no longer exists.")

    pause()


def handle_edit_asset(data, project_id, category, assets, display_names):
    # update an existing asset's path in place -- useful if the file moved or was renamed
    if not assets:
        print("\n[!] No assets to edit")
        pause()
        return

    clear_screen()
    print(f"-- EDIT {category.upper()} PATH --\n")

    for i, name in enumerate(display_names, start=1):
        print(f"{i}. {name}")

    choice = input("\nEnter the number of the file to edit: ").strip()
    choice_num = safe_int(choice)

    if choice_num is None or not (1 <= choice_num <= len(assets)):
        print("\n[!] Invalid input, try again")
        pause()
        return

    index = choice_num - 1
    old_name = display_names[index]

    new_path = input(f"Enter the new path for '{old_name}': ").strip()

    if not new_path:
        print("\n[!] Invalid input, try again")
        pause()
        return

    # normalize the new path the same way we do on add
    new_asset = projects.make_asset_from_path(new_path)
    file_exists = projects.asset_exists_on_disk(new_asset)

    if not file_exists:
        print(f"\n[!] No file found at that path:")
        print(f"  {new_path}")
        confirm = input("Save it anyway? (y/n): ").strip().lower()
        if confirm != "y":
            print("\nNot changed.")
            pause()
            return

    # replace at the same index so it stays in the same position in the list
    success = projects.replace_in_list(data, project_id, ("assets", category), index, new_asset)

    if success:
        print(f"\nUpdated '{old_name}' to point to '{new_asset['name']}'.")
    else:
        print("\n[!] Could not update -- project no longer exists.")

    pause()


def handle_open_asset(data, project_id, category, assets, display_names):
    if not assets:
        print("\n[!] No assets to open")
        pause()
        return

    clear_screen()
    print(f"-- OPEN {category.upper()} --\n")

    for i, name in enumerate(display_names, start=1):
        print(f"{i}. {name}")

    choice = input("\nEnter the number of the file to open: ").strip()
    choice_num = safe_int(choice)

    if choice_num is None or not (1 <= choice_num <= len(assets)):
        print("\n[!] Invalid input, try again")
        pause()
        return

    index = choice_num - 1
    asset = assets[index]
    display_name = display_names[index]

    try:
        # quiet=True so the OS tool's own output doesn't bleed into our terminal
        utils.open_file(asset["path"], quiet=True)
        print(f"\nOpened '{display_name}'.")

    except utils.FileNotFoundOnDisk:
        # file was moved or deleted since we linked it
        print(f"\n[!] File not found at saved path: {asset['path']}")
        confirm = input("Remove this entry? (y/n): ").strip().lower()

        if confirm == "y":
            removed = projects.remove_from_list(data, project_id, ("assets", category), index)
            if removed:
                print(f"Removed '{display_name}' from {category}.")
            else:
                print("[!] Could not remove entry -- project no longer exists.")

    except utils.LaunchFailed as e:
        print(f"\n[!] {e}")

    pause()


# --- entry point ---

def main():
    data, warning = storage.load_data()
    # print(f"loaded {len(data['projects'])} projects")  # debug

    # show the warning screen if something was wrong with the save file
    if warning:
        clear_screen()
        print("-- CREATOROS --")
        print("\n[!] ATTENTION -- SAVE FILE PROBLEM\n")
        print(warning)
        pause()

    show_dashboard(data)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # ctrl+c -- data is already saved, just exit cleanly
        print("\n\nShutting down. See you next session.")
    except EOFError:
        # input stream closed (terminal closed, or piped input ran out)
        print("\n\nInput ended unexpectedly. Shutting down.")
