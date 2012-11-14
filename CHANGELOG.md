#phue changelog

##r5
 * Renamed the Bulb() object to Light() so it reflects the official API better
 * You can now pass the username as argument to the Bridge class if you don't want to read/store to file
 * You can now get the bridge name with brdige.name or set it with bridge.name = 'newname'
 * The set_state method can now use a dictionary as first argument to send more complex messages