This project was made to simplify making and customizing themes for [rEFInd](https://www.rodsbooks.com/refind/) so that you dont have to be a "power user" to get the customization you want


<img width="1373" height="1250" alt="image" src="https://github.com/user-attachments/assets/e96c358e-76d8-4a03-9a59-7f3b313496d5" />

Showcase/Tutorial
https://www.youtube.com/watch?v=reH_1cvkUkc


How to Run rEFInd Theme Editor
================================

Requirements:
- Python 3.14+ (may work on older 3.x, tested on 3.14)
- PySide6 6.11+ (pip install PySide6)

Install PySide6:
  pip install PySide6

Run the run.sh

Usage:
- Themes are stored in the "themes/" folder (next to app/)
- Create a new theme with the "Create Theme" button
- Set a background banner, icons, and options in the editor
- Click Save to write refind.conf to the theme folder
- Copy the theme folder to your ESP at /EFI/refind/themes/
- Add "include themes/YourThemeName/refind.conf" to your main refind.conf

================================

Also there will likely be some descrepencies such as people will likely have different install locations of rEFInd depending on how you installed it so youll need to go into the conf and change the directories. if this project gets more attention ill find a way to automate that but for now as of me and some friends being the only ones using it im just gonna leave it be.


Discord: https://discord.gg/UsDPckUATe
feel free to find and share themes here
