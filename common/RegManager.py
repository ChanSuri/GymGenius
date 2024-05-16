import requests
import json


class RegManager():
    def __init__(self,gymCat):
        self.gymCat = gymCat

    def register(self, regMsg):
        reg = requests.post(self.gymCat, json.dumps(regMsg))
        response = json.loads(reg.text)
        if response["status"] == "fail":
            print("Register Fail!!!")
            print("Fail type: " + response["errorType"])
        else:
            print("Register Success")
        return response["setting"]

    def getData(self, fatherType, childType,params):
        uri = self.gymCat+"/"+fatherType+"/"+childType
        response = requests.get(uri,params)
        data = json.loads(response.text)
        return data


    def delete(self,type,id):
        requests.delete(self.gymCat + "/"+type+"/" + id)