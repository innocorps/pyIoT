"""
- Formatted JSON message used for checks against API messages, so bad
    JSON messages are not written to database.
- All lists and booleans are turned into strings to prevent errors,
    but for a real message this would be done already in models.py.
- Ignore all data, only keys are checked.

"""
ACCEPTED_JSON = {
    "datetime": "2017-09-13T:13:01:57Z",
    "sensor_1": "7"
}
