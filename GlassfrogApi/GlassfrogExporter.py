__author__ = 'Erie'

from GlassfrogApi.GlassfrogClient import GlassfrogClient
import json

config = {
    "API_KEY": "{YOUR_GLASSFROG_API_KEY}",
    "PROXIES": {
        "http": "",
        "https": ""
    },
    "SERVER_URL": "https://api.glassfrog.com/api/v3/",
    "VERIFY_SSL": True
}

class GlassfrogExporter:

    people = []
    circles = []
    roles = []
    rolefillers = []
    glassfrog = None

    def __init__(self):
        # instantiate glassfrog api object
        self.glassfrog = GlassfrogClient(config=config)

    def doExport(self):
        self.people =  self.glassfrog.get_people()['people']
        self.circles = self.glassfrog.get_circles(include_members=True)['circles']
        self.roles =   self.glassfrog.get_roles()['roles']

    def enrichData(self):
        # take array of people, add empty linked-roles array to each person, to be filled later
        for person in self.people:
            person['links']['roles'] = []

        # add linked data to roles and people lists
        for role in self.roles:
            # add circle name to role, as circle Id is not human readable
            role = self._addCircleNameToRole(role)
            if role == None:
                # Skip if this role is a 'lead link' role in the super circle
                pass
            else:
                # for each role, take each person and look for him in the people list. If found, add the role to his list
                role = self._addRoleToPerson(role)

        # add super-circle id to each circle (is otherwise very difficult to obtain from glassfrog api results, as it is liked by supported/supporting_roles)
        for circle in self.circles:
            # get the roleId that represents this circle as a role (leadlink) in the super-circle
            # find this role in the list of roles, and grab the role's CircleId
            circle['links']['super_circle'] = self._getSuperCircle(circle)

    def buildRoleFillers(self):
        # create list of rollfillers (all person/role combo's)
        self.rolefillers = [] # empty the list, to prevent adding existing combos twice
        for person in self.people:
            for role in person['links']['roles']:
                self.rolefillers.append({
                    "roleFillerId":     str(role['id']) + ":" + str(person['id']),
                    "personId":         person['id'],
                    "circleId":         role['links']['circle'],
                    "roleId":           role['id'],
                    "personName":       person['name'],
                    "circleRoleName":   role['links']['circle_short_name'] + ":" + role['name']
                })

    # Private helper methods
    def _addCircleNameToRole(self, role):
        # add circle name to role, as circle Id is not human readable
        role['links']['circle_short_name'] = ''
        for circle in self.circles:
            if circle['links']['supported_role'] == role['id']:
                return None     # Return None if the role is a lead link for a sub circle, in a super circle
            if circle['id'] == role['links']['circle']:
                role['links']['circle_short_name'] = circle['short_name']
        return role

    def _addRoleToPerson(self, role):
        # for each role, take each person and look for him in the people list. If found, add the role to his list
        for personId in role['links']['people']:
            for person in self.people:
                if(person['id']==personId):
                    person['links']['roles'].append(role)
        return role

    def _getSuperCircle(self, circle):
        for role in self.roles:
            if role['id'] == circle['links']['supported_role']:
                return role['links']['circle']
        return None

    # def storeDataAsJSONFiles(self):
    #     self.__storeDataInJSONFile({'people':self.people},     'people')
    #     self.__storeDataInJSONFile({'circles':self.circles},    'circles')
    #     self.__storeDataInJSONFile({'roles':self.roles},      'roles')
    #     self.__storeDataInJSONFile({'rolefillers':self.rolefillers},'rolefillers')
    #
    # def __storeDataInJSONFile(self, data, type, prettyprint=True):
    #     print("Writing data to file: " + self.config[type]['filename'])
    #     GlassfrogExporter.writeJsonToFile(self.config[type]['filename'], data, prettyprint)
    #
    # # static utilities
    # @staticmethod
    # def writeJsonToFile(filename, jsonObj, prettyPrint=False):
    #     file = open(filename, 'w')
    #     if len(jsonObj) > 0:
    #         if(prettyPrint):
    #             jsonStr = json.dumps(jsonObj, indent=4, sort_keys=True)
    #         else:
    #             jsonStr = json.dumps(jsonObj)
    #         if len(jsonStr):
    #             file.write(jsonStr)
    #         else:
    #             print('jsonString is empty. Skipped writing to file')
    #     else:
    #         print('jsonObj is empty. Skipped writing to file')
    #
    #     file.close()
    #
    # @staticmethod
    # def selectDataInit(colHeaders):
    #     values = {'values':[colHeaders]}
    #     # print("Selecting specific values from dataset... ")
    #     # print(values['values'])
    #     return values
    #
    # @staticmethod
    # def selectDataLoop(row, values, selectedData):
    #     values['values'].append(selectedData)
    #     # print("Row: " + str(row))
    #     # print("==> Selected Data: " + str(selectedData))
    #     return values
    #
    # @staticmethod
    # def selectDataFromPeople(dataArray):
    #     values = GlassfrogExporter.selectDataInit(['Id','Name', '#Circles'])
    #     for row in dataArray:
    #         selectedData = [row['id'], row['name'], len(row['links']['circles'])]
    #         GlassfrogExporter.selectDataLoop(row, values, selectedData)
    #     return values
    #
    # @staticmethod
    # def selectDataFromPeople2(dataArray):
    #     values = GlassfrogExporter.selectDataInit(['Id','URL', 'Name', '#Circles', '#Roles'])
    #     for row in dataArray:
    #         selectedData = [row['id'], "https://app.glassfrog.com/people/"+str(row['id']), row['name'], len(row['links']['circles']), len(row['links']['roles'])]
    #         GlassfrogExporter.selectDataLoop(row, values, selectedData)
    #     return values
    #
    # @staticmethod
    # def selectDataFromCircles(dataArray):
    #     values = GlassfrogExporter.selectDataInit(['Id','URL', 'ShortName', '#People', '#Roles', '#Policies', '#Domains'])
    #     for row in dataArray:
    #         selectedData = [row['id'], "https://app.glassfrog.com/circles/"+str(row['id']), row['short_name'], len(row['links']['people']), len(row['links']['roles']), len(row['links']['policies']), len(row['links']['domain'])]
    #         GlassfrogExporter.selectDataLoop(row, values, selectedData)
    #     return values
    #
    # @staticmethod
    # def selectDataFromRoles(dataArray):
    #     values = GlassfrogExporter.selectDataInit(['Id','URL', 'Name', 'CircleId', '#Accountabilities', '#People', '#Domains'])
    #     for row in dataArray:
    #         selectedData = [row['id'], "https://app.glassfrog.com/roles/"+str(row['id']), row['name'], "https://app.glassfrog.com/circles/"+str(row['links']['circle']), len(row['links']['accountabilities']), len(row['links']['people']), len(row['links']['domains'])]
    #         GlassfrogExporter.selectDataLoop(row, values, selectedData)
    #     return values
    #
    # @staticmethod
    # def selectDataFromRoles2(dataArray):
    #     values = GlassfrogExporter.selectDataInit(['Id','URL', 'Name', 'CircleId', 'CircleURL', 'CircleName', '#accountabilities', '#People', '#Domains'])
    #     for row in dataArray:
    #         selectedData = [row['id'], "https://app.glassfrog.com/roles/"+str(row['id']), row['name'], row['links']['circle'], "https://app.glassfrog.com/circles/"+str(row['links']['circle']), row['links']['circle_short_name'], len(row['links']['accountabilities']), len(row['links']['people']), len(row['links']['domains'])]
    #         GlassfrogExporter.selectDataLoop(row, values, selectedData)
    #     return values
    #
    # @staticmethod
    # def selectRolefillerData(dataArray):
    #     values = GlassfrogExporter.selectDataInit(['roleFillerId', 'personId', 'circleId', 'roleId', 'personName', 'circleRoleName'])
    #     for row in dataArray:
    #         selectedData = [row['roleFillerId'], row['personId'], row['circleId'], row['roleId'], row['personName'], row['circleRoleName']]
    #         GlassfrogExporter.selectDataLoop(row, values, selectedData)
    #     return values
