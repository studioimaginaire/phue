#phue changelog

##r9
* Added unit tests (sdague)
* Added scene support (sdague)
* Added sensor support (eldstal)
* Added reachable and type attributes to the Light object (carlosperate)
* Changed License to MIT

##r8
* iOS compatibility (Nathanaël Lécaudé)
* Logging fixes
* Added effect changing options (bradykent)
* Several unicode fixes (Nathanaël Lécaudé)
* Misc bug fixes

##r7
* Added to pypi
* Added support for Python 3 (Nathanaël Lécaudé)
* Logging level can be set with b.set_logging() (Nathanaël Lécaudé)
* Logging level can be set at init: b = Bridge(logging = 'debug') (Nathanaël Lécaudé)
* Added docstrings to Light properties (Nathanaël Lécaudé)
* Added colormode property to Light class (Nathanaël Lécaudé)
* IP is now optional if present in config file (Nathanaël Lécaudé)
* Implemented groups (Nathanaël Lécaudé)
* Implemented schedules (Nathanaël Lécaudé)
* Renamed get_info to get_api (Nathanaël Lécaudé)
* Renamed get_lights to get_light_objects (Nathanaël Lécaudé)
* Renamed set_state and get_state to set_light and get_light (Nathanaël Lécaudé)
* Fixed important bug when using set_state with a list of lights (Nathanaël Lécaudé)
* Add access to Light objects via direct indexing of the Bridge object via __getitem__ (Marshall Perrin)
* Implement real logging using Python's logging module, including error checking and display of responses from the server. (Marshall Perrin)
* Add function colortemp_k for color temperatures in Kelvin. (Marshall Perrin)
* Some additional error checking for invalid or missing parameters (Marshall Perrin)
* More details in docstrings. (Marshall Perrin)


##r6
* Light objects are now obtained using the get_lights method
* Added the alert method to the Light object
* All requests now use httplib for consistency
* Moved all source to github
* Renamed the module to phue

##r5
 * Renamed the Bulb() object to Light() so it reflects the official API better
 * You can now pass the username as argument to the Bridge class if you don't want to read/store to file
 * You can now get the bridge name with brdige.name or set it with bridge.name = 'newname'
 * The set_state method can now use a dictionary as first argument to send more complex messages
