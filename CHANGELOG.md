#phue changelog

##r7
* Added docstrings to Light properties
* Added colormode property to Light class
* IP is now optional if present in config file
* Implemented groups
* Implemented schedules
* Renamed get_info to get_api
* Renamed get_lights to get_light_objects
* Renamed set_state and get_state to set_light and get_light
* Fixed important bug when using set_state with a list of lights

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