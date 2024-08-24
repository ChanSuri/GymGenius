import cherrypy
import json
import requests

# URL of the Resource Catalog
RESOURCE_CATALOG_URL = 'http://localhost:8081/devices'

class DeviceConnector:
    exposed = True

    def GET(self, *uri, **params):
        """Handles GET requests (not used in this case)"""
        return json.dumps({"message": "Welcome to the Gym Genius Device Connector"})

    def POST(self, *uri, **params):
        """Register a new device in the Resource Catalog"""
        # Read the JSON data from the request body
        body = cherrypy.request.body.read().decode('utf-8')
        input_data = json.loads(body)
        device_id = input_data.get("device_id")

        # Ensure device_id is provided
        if not device_id:
            raise cherrypy.HTTPError(400, "device_id is required")

        # Send a POST request to the Resource Catalog to register the device
        try:
            response = requests.post(RESOURCE_CATALOG_URL, json=input_data)
            if response.status_code in [200, 201]:
                return json.dumps({"status": "success", "message": "Device registered successfully"})
            elif response.status_code == 409:
                return json.dumps({"status": "error", "message": "Device already exists"})
            else:
                cherrypy.response.status = response.status_code
                return json.dumps({"status": "error", "message": response.text})
        except requests.exceptions.RequestException as e:
            cherrypy.response.status = 500
            return json.dumps({"status": "error", "message": str(e)})

    def PUT(self, *uri, **params):
        """Update a device in the Resource Catalog"""
        # Ensure device_id is provided in the URI
        if len(uri) == 0:
            raise cherrypy.HTTPError(400, "device_id is required")

        device_id = uri[0]

        # Read the JSON data from the request body
        body = cherrypy.request.body.read().decode('utf-8')
        input_data = json.loads(body)

        # Send a PUT request to the Resource Catalog to update the device
        try:
            response = requests.put(f"{RESOURCE_CATALOG_URL}/{device_id}", json=input_data)
            if response.status_code == 200:
                return json.dumps({"status": "success", "message": "Device updated successfully"})
            elif response.status_code == 404:
                return json.dumps({"status": "error", "message": "Device not found"})
            else:
                cherrypy.response.status = response.status_code
                return json.dumps({"status": "error", "message": response.text})
        except requests.exceptions.RequestException as e:
            cherrypy.response.status = 500
            return json.dumps({"status": "error", "message": str(e)})

    def DELETE(self, *uri, **params):
        """Delete a device from the Resource Catalog"""
        # Ensure device_id is provided in the URI
        if len(uri) == 0:
            raise cherrypy.HTTPError(400, "device_id is required")

        device_id = uri[0]

        # Send a DELETE request to the Resource Catalog to delete the device
        try:
            response = requests.delete(f"{RESOURCE_CATALOG_URL}/{device_id}")
            if response.status_code == 200:
                return json.dumps({"status": "success", "message": "Device deleted successfully"})
            elif response.status_code == 404:
                return json.dumps({"status": "error", "message": "Device not found"})
            else:
                cherrypy.response.status = response.status_code
                return json.dumps({"status": "error", "message": response.text})
        except requests.exceptions.RequestException as e:
            cherrypy.response.status = 500
            return json.dumps({"status": "error", "message": str(e)})


if __name__ == '__main__':
    # CherryPy configuration with port and host settings
    cherrypy.config.update({'server.socket_port': 8082, 'server.socket_host': '0.0.0.0'})

    # Mount the DeviceConnector class using MethodDispatcher
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }

    # Mount the DeviceConnector application
    cherrypy.tree.mount(DeviceConnector(), '/', conf)

    # Start the CherryPy server
    cherrypy.engine.start()
    cherrypy.engine.block()
