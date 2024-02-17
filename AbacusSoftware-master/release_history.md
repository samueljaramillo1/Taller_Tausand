# Release Notes 1.6.0 - January 2023
## New features
* Added compatibility with new family AB2000 devices: AB2502 and AB2504.

## Bug Fixes
* Icon in win32 systems of better resolution.

# Release Notes 1.5.0 - November 2021
## New features
* Checkboxes were added to check/unckeck all single or double channels at once (Issue #55).
* Buttons to show/hide Current and Plots subwindows. 
* Single channels, double coincidences and multiple coincidenced data can each be seen separately in individual subwindows (Current single, Plots single, Current double, Plots double, Current multiple, Plots Multiple).
* Buttons to show/hide the new available subwindows.
* New and improved dark theme. Dark and light themes are consistent with each other and among platforms.
* Colors for plots and channel labels are set automatically according to the theme (Issue #53).
* The color of each plot line can be customized (Issue #53).
* The marker size and linewidth of plots can be customized (Issue #53).
* Smaller steps between values can be chosen in different ranges for the fields Coincidence Window (ns), Delay X (ns) and Sleep X (ns) for the soon-to-come 1 (ns) resolution devices (Issue #57).
* Checksum errors or communication errors are not longer shown in a dialog but rather in the status bar. Acquisition is no longer interrupted because of those errors (Issue #59).
* Support for soon-to-come 8 channel devices. Up to 8 multiple channel combinations (of triple or cuadruple coincidences) can be selected (Issue #56).
* New button to restart local time that also clear plots (Issue #54).
* Time range for the x-axis of plots can be chosen among particular values (Issue 48).
* The program remembers the state of the user interface from the previous session: the size and position of subwindows, channels chosen, theme, colores, linewidths, etc (Issue 46).
* If a multiple coincidence is not active, the related data is saved in the data file as an empty string instead of a 0.
* New plots in Delay time sweep dialog that show single counts of the chosen channels.

## Bug Fixes
* If not admisible values of the settings fields (Coincidence Window (ns), Delay X (ns) and Sleep X (ns)) are typed, the value is automatically fixed when pressing enter, after a few seconds, of if the field looses focus.
* Faster data update to avoid differences between data shown in hardware and software (Issue #49).
* Legends are shown in plots.

