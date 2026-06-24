# OverMouse
<img width="1434" height="812" alt="image" src="https://github.com/user-attachments/assets/21ff25cf-dbf7-47c2-b540-e86db2a1c016" />

OverMouse is a small Python overlay tool that adds a larger, brighter custom cursor on top of your game or desktop. It is useful for games where the default cursor is hard to see.

The overlay does not replace the game cursor or inject into the game. It draws a transparent, click-through cursor overlay that follows your mouse.

Depending on which mouse cursor is used, you will have overlay aligning like this:\
<img width="143" height="150" alt="image" src="https://github.com/user-attachments/assets/0f99d2fe-8a64-4077-a5ab-cc05c1a58d7b" /> <img width="148" height="143" alt="image" src="https://github.com/user-attachments/assets/fa8ccaed-5919-4f30-b662-4e02f10a579d" />


## Features

* **Large visible cursor overlay**: Makes the cursor easier to see in dark or busy games.
* **Multiple cursor themes**: Includes Pink/Purple, Cyan/Blue, Lime/Green, and Amber/Orange.
* **Theme memory**: Remembers the last selected cursor theme using `OverMouse.state.json`.
* **Terminal preview**: Shows small cursor previews directly in the terminal when launched.
* **Click-through overlay**: The overlay does not block clicks or mouse interaction.
* **Right-click hide**: Temporarily hides the overlay while holding right mouse button, useful when rotating the camera in games.
* **Simple hotkeys**: Toggle overlay and cursor theme while the script is running.

## Files

### `OverMouse.py`

Main script for the cursor overlay.

It creates a transparent always-on-top window that follows your mouse position and draws the selected cursor theme.

### `OverMouse.state.json`

Automatically created after running the script.

Stores the currently selected cursor theme so OverMouse remembers it the next time you launch it.

## Controls

* **[`F6`]**: Start/stop the cursor overlay.
* **[`F7`]**: Toggle between cursor themes.
* **[`Right Mouse Held`]**: Temporarily hides the overlay.
* **[`Ctrl+C`]**: Abort the script from the terminal.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/YourUsername/OverMouse.git
   ```

2. Navigate to the directory:

   ```bash
   cd OverMouse
   ```

3. Install the required dependency:

   ```bash
   pip install PyQt6
   ```

## Usage

Run the script:

```bash
python3 OverMouse.py
```

The terminal will show:

* Available cursor themes
* Current active theme
* Hotkeys
* State file location

Use `F6` to toggle the overlay and `F7` to switch cursor themes.

## Customization

### Changing Cursor Size

In `OverMouse.py`, change:

```python
SCALE = 0.5
```

Higher values make the in-game overlay cursor larger. Lower values make it smaller.

Example:

```python
SCALE = 0.4
```

### Changing Terminal Preview Size

Change:

```python
TERMINAL_PREVIEW_SCALE = 0.26
```

This only changes the cursor preview shown in the terminal. It does not affect the actual overlay size.

### Changing Hotkeys

The current hotkeys are defined near the top of the script:

```python
VK_F6 = 0x75
VK_F7 = 0x76
```

Windows virtual key examples:

* `F5` = `0x74`
* `F6` = `0x75`
* `F7` = `0x76`
* `F8` = `0x77`

## Notes

OverMouse works best in borderless/windowed games. Some fullscreen games or anti-cheat systems may block or interfere with overlays.

If the cursor flickers, try increasing:

```python
POLL_MS = 12
```

to:

```python
POLL_MS = 20
```

or:

```python
POLL_MS = 25
```

## Known issues
- Please submit a bug if you find one
  
## Credits

→ by hitem 🖰
