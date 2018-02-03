API
===

This is a reference for POSTing data to the backend. Accepted message formats are below.

API v0.1 JSON Machine POST Heartbeat
------------------------------------
.. code-block:: javascript
        
        {
                "datetime":"2017-09-13T13:01:57Z",
                "heartbeat":"beep"
        }


API v0.1 JSON Machine POST Heartbeat Response
---------------------------------------------
.. code-block:: javascript

    {
        "Response": "200 OK",
        "Message": "Heartbeat received."
    }


API v0.1 JSON Machine POST
--------------------------
.. code-block:: javascript
	
        {
                "datetime":"2017-09-13T13:01:57Z", 
                "sensor_1":"2.00"
        }


API v0.1 JSON Machine POST Response
-----------------------------------
.. code-block:: javascript

    {
        "Response": "201 data created",
        "Message": "Data was successfully posted!"
    }
