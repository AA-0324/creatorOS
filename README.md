# CreatorOS
A lightweight, distraction-free CLI meant to help YouTube creators manage their video production pipelines, asset libraries, and project states.



https://github.com/user-attachments/assets/835aba31-d2bf-494f-8088-d4b2b0ba188b



## The Problem
YouTubers have their ideas everywhere: scattered notes, thumbnail ideas in one software, scripts in another account, etc. CreatorOS solves this. Built entirely in Python, CreatorOS acts as a centralized dashboard that eliminates manual folder-diving and scattered notes. It works hand-in-hand with your OS to launch native applications and manage files right from the terminal.

## Why I Built This
As an aspiring content creator myself, I realized that the actual editing and filming only took up half of my time. The rest? I spent it searching for assets, organizing scripts, and tracking project statuses. I built CreatorOS to solve my own workflow friction, challenging myself to build a robust, modular system from scratch without relying on heavy external frameworks.

## Core Features
* Interactive CLI Dashboard: A clean, terminal interface with easy-to-learn navigation.

* Custom JSON: A lightweight, safe database engine that handles state management and instantly commits without needing external frameworks.
* Cross-Platform OS Integration: Uses Python's native subprocess wrappers to instantly launch scripts, thumbnails, and video drafts in the user's default desktop applications (Windows/macOS/Linux).
* Modular Architecture: UI, logic, utilities, and data storage are separated into distinct, maintainable modules for easier debugging.
* Automated Data Cleansing: Removes hidden OS artifacts (like quotation marks from copied file paths) to prevent crashes.

## Modules
* main.py – The terminal interface, captures keyboard input, and handles all routing between the dashboard, project pages, and asset submenus.
* core/projects.py – The logic brain. Handles all operations, works with the assests, and checks if the user's paths actually exist.
* core/storage.py – The safety layer. Safely reads and writes to the database (data/storage.json), making sure that data is never corrupted during a session.
* core/utils.py – The OS-bridge layer. Contains cross-platform helper functions to interact with the user's OS
* data/storage.json – Acts as the application's database.

## Running It
   ```bash
   git clone https://github.com/AA-0324/creatorOS.git
   cd CreatorOS
   python main.py
  ```

## License
See the LICENSE file for more details :)
