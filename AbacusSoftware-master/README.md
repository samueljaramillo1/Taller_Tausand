# AbacusSoftware
Abacus Software is a suite of tools built to ensure your experience with Tausand's coincidence counters becomes simplified.

Written in Python3, abacusSoftware relies on the following modules:

- pyAbacus
- pyqtgraph
- NumPy
- PyQt5
- pyserial
- qtmodern

## Preview

A quick demo video to preview this software is available at: https://youtu.be/c4QO8p1WeSE

## Installation
`abacusSoftware` can be installed using `pip` as: 
```
pip install abacusSoftware
```

Or from GitHub
```
pip install git+https://github.com/Tausand-dev/abacusSoftware.git
```

## Execute abacusSoftware
On a terminal or command prompt type
```
abacusSoftware
```

### Grant port access on Linux
Most Linux configurations have a dialout group for full and direct access to serial ports. By adding your user account to this group you will have the necessary permissions for Abacus Software to communicate with the serial ports.

1. Open Terminal.
2. Enter the following command, replacing ```<username>``` with the name of your account.
```
sudo usermod -a -G dialout <username>
```
3. Sign in and out for the changes to take effect.


## For developers
### Creating a virtual environment
Run the following code to create a virtual environment called `.venv`
```
python -m venv .venv
```

#### Activate
- On Unix systems:
```
source .venv/bin/activate
```
- On Windows:
```
.venv\Scripts\activate
```

#### Deactivate
```
deactivate
```

### Installing packages
After the virtual environment has been activated, install required packages by using:
```
python -m pip install -r requirements.txt
```

### Freezing code
After activating the virtual environment

#### Windows
Run the following command 
```
pyinstaller --additional-hooks-dir installers/pyinstaller_hooks/ --name AbacusSoftware --onefile --noconsole -i abacusSoftware/GUI/images/abacus_small.ico test.py
```
Two folders will be created: build and dist. Inside `dist` you'll find the `.exe` file. To create an installer, first install Inno Setup from https://jrsoftware.org/isinfo.php#stable. Then, using the File Explorer, go to the folder `installers` and double-click `installer_builder.iss` or open it from Inno Setup if it is already opened. Click on the play icon and then follow the process, which includes the creation of the installer and the installation itself.

The installer will be saved in a folder called `Output`.

### MacOS
Run the following command
```
pyinstaller --additional-hooks-dir installers/pyinstaller_hooks/ --name AbacusSoftware --onefile --noconsole -i abacusSoftware/GUI/images/Abacus_small.png test.py
```
Two folders will be created: build and dist. Inside `dist` you'll find the `.app` file. This file can be run from a console by executing the command
To change the icon of the `.app` file follow the instructions here https://appleinsider.com/articles/21/01/06/how-to-change-app-icons-on-macos

### Linux
Run the following command
```
pyinstaller --additional-hooks-dir installers/pyinstaller_hooks/ --name AbacusSoftware --onefile --noconsole -i abacusSoftware/GUI/images/Abacus_small.png test.py
```
Two folders will be created: build and dist. Inside dist you'll find the executable file. This file can be run from a console by executing the command

```
./AbacusSoftware
```
If it doesn't run, make sure it has execute permissions. In case it doesn't run `chmod +x AbacusSoftware` and then try again. The executable file could be used to create a Desktop entry so it can be lauched as an application (for example in Gnome, an icon could be assigned)

To create an AppImage that can be run from multiple Linux distributions and be launch by double clicking, follow the next steps.
* Create the following folder path: 
	AbacusSoftware.AppDir/usr/bin
* Place the executable inside the bin folder 
* Place the icon Abacus_small.png located at abacusSoftware/GUI/images/Abacus_small.png inside AbacusSoftware.AppDir
* Create a file called AbacusSoftware.desktop inside AbacusSoftware.AppDir
* Edit the `.desktop` file with the following

```
[Desktop Entry]
Name=AbacusSoftware
Exec=AbacusSoftware
Icon=Abacus_small
Type=Application
Categories=Utility;
```

* Give execution permisions to the `.desktop` file: `chmod +x AbacusSoftware.desktop`
* Create a script called `AppRun` with the following contents

```
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
EXEC="${HERE}/usr/bin/AbacusSoftware"
exec "${EXEC}"
```

* Give execution permisions to the `AppRun` file: `chmod +x AppRun`. After this step, the app should run after doing `./AppRun` on a Terminal.
* For 64-bit architecture, download appimagetool-x86_64.AppImage from https://github.com/AppImage/AppImageKit/releases/ and give execution permisions to it. 
* Place appimagetool outside AbacusSoftware.AppDir and run
```
ARCH=x86_64 ./appimagetool-x86_64.AppImage AbacusSoftware.AppDir
```
* The file `AbacusSoftware-x86_64.AppImage` will be created. This file can be opened by double clicking it.


### Generating images and icons
In linux, `cd` into `abacusSoftware/GUI/images/`, where you'll find the image files that will be used in the application. You'll also find a .qrc file which specifies any image that you want to include. If you want to use new images you'll need to specify their name inside such file. Next execute the following command

```
pyrcc5 -o __GUI_images__.py images.qrc
```
This will update the `__GUI_images__.py` file, which needs to be copied into the folder `abacusSoftware` and replace the file located there with the same name. Now the image resources can be called from within the code by doing, for example,

```
splash_pix = QtGui.QPixmap(':/splash.png').scaledToWidth(600)
```

### Fixing pyinstaller:
https://github.com/pyinstaller/pyinstaller/commit/082078e30aff8f5b8f9a547191066d8b0f1dbb7e

https://github.com/pyinstaller/pyinstaller/commit/59a233013cf6cdc46a67f0d98a995ca65ba7613a
