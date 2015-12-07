__author__ = 'Yafit'
import requests
import json

ip = 'http://xxxxxxxxxx'


def loginApi(ip, username, password):
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'password': password}
    r = requests.get(ip + '/rest/v1/login/' + username, headers=myHeader)
    print r.status_code
    setCookie = r.headers['Set-Cookie']
    print setCookie
    print r.content
    return setCookie


# ======= DATA POINT SUMMARY ==============
def dataPointsSummary(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Query Data Points
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-point-summaries', headers=myHeader, cookies=reqCookie)
    # print r.status_code
    # print r.content


def dataPointSummExplainQuery(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get Explaination For Query
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-point-summaries/explain-query', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


# ========== DATA POINTS ====================

def dataPointsApi(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Query Data Points
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-points', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getDataPointById(ip, reqCookie, id):
    """
    :param ip:
    :param reqCookie:
    :param id:
    :return: Get data point by ID
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-points/by-id/' + str(id), headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getAllDataPointsForDataSourceByXid(ip, reqCookie, Xid):
    """
    :param ip:
    :param reqCookie:
    :param Xid:  data source xid
    :return: Get all data points for data source
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-points/data-source/' + str(Xid), headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getDataPointExplainQuery(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get Explaination For Query
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-points/explain-query', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def dataPointListWithLimit(ip, reqCookie, limit):
    """
    :param ip:
    :param reqCookie:
    :return:Get all data points
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-points/list?limit=' + str(limit), headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def deleteDataPointByXid(ip, reqCookie, Xid):
    """
    :param ip:
    :param reqCookie:
    :param Xid:
    :return: Delete a data point
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.delete(ip + '/rest/v1/data-points/' + str(Xid), headers=myHeader, cookies=reqCookie)
    print r.status_code


def getDataPointByXid(ip, reqCookie, Xid):
    """
    :param ip:
    :param reqCookie:
    :param Xid: data point xis
    :return: Get data point by XID
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-points/' + str(Xid), headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


# ===== DATA SOURCES ==============
def dataSources(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get all data sources
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-sources/list', headers=myHeader, cookies=reqCookie)
    print r.status_code
    # print r.content


def getDataSourceByXid(ip, reqCookie, Xid):
    """
    :param ip:
    :param reqCookie:
    :param Xid: data sorce Xid
    :return: Get data source by xid
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-sources/' + str(Xid), headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


# ============ EVENTS ============

def eventsApi(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Query Events
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/events', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getActiveEventsSummary(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get the active events summary
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/events/active-summary', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getEventsListWithLimit(ip, reqCookie, limit):
    """
    :param ip:
    :param reqCookie:
    :param limit:
    :return:Get all events
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/events/list?limit=' + str(limit), headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getEventById(ip, reqCookie, Eid):
    """
    :param ip:
    :param reqCookie:
    :param Eid: event id
    :return: Get event by ID
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/events/' + str(Eid), headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


# ============ LOGGING =================
def getRecentLogsFromFile(ip, reqCookie, fileName):
    """
    :param ip:
    :param reqCookie:
    :param fileName:
    :return: Returns a list of recent logs
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/logging/by-filename/' + fileName, headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content

def getLogFilesNames(ip, reqCookie, limit):
    """
    :param ip:
    :param reqCookie:
    :return: Returns a list of logfile names
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/logging/files?limit=' + str(limit), headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content
# =========== MAILLING LISTS ==================
def getMaillingList(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get Mailing List
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/mailing-lists', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getMaillingListByXid(ip, reqCookie, Xid):
    """
    :param ip:
    :param reqCookie:
    :param Xid: mailling list xid
    :return: Get Mailing List by XID
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/mailing-lists/'+ Xid, headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content

# ========= POINT HIERARCHY ============

def getPointHierarchyFolderByName(ip, reqCookie, folderName):
    """
    :param ip:
    :param reqCookie:
    :param folderName:
    :return: Get point hierarchy folder by name
    """
    numOfWOrdes = len(folderName.split())
    newName = ""
    i=0
    while i < numOfWOrdes-1:
        newName= newName +folderName.split()[i]+'%20'
        i+=1
    newName= newName +folderName.split()[i]
    print newName
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/hierarchy/by-name/'+ newName, headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getPointHierarchy(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get full point hierarchy
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/hierarchy/full', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getPathToPointByXid(ip, reqCookie, Xid):
    """
    :param ip:
    :param reqCookie:
    :param Xid: point data Xid
    :return: Get path to a point using point's XID
    """
    numOfWOrdes = len(Xid.split())
    newXid = ""
    i=0
    while i < numOfWOrdes-1:
        newXid= newXid +Xid.split()[i]+'%20'
        i+=1
    newXid= newXid +Xid.split()[i]
    print newXid
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/hierarchy/path/'+newXid, headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content

# =========== POINT VALUES =============
def getLatestPointValues(ip, reqCookie, Xid, limit):
    """
    :param ip:
    :param reqCookie:
    :param Xid:
    :param limit:
    :return: Get Latest Point Values
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/point-values/'+Xid+'/latest?useRendered=false&unitConversion=false&limit='+str(limit)+'&useCache=true',
                     headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getPointStatistics(ip, reqCookie, Xid, fromDate, toDate):
    """
    :param ip:
    :param reqCookie:
    :param Xid:
    :param fromDate:
    :param toDate:
    :return: Get Point Statistics
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/point-values/'+Xid+'/statistics?useRendered=false&unitConversion=false'
                                                       '&from='+fromDate+'&useCache=true',
                     headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content

# =========== REAL TIME DATA =============
def realTimeData(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return:Query realtime values
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/realtime', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def realTimeDataByXid(ip, reqCookie, Xid):
    """
    :param ip:
    :param reqCookie:
    :param Xid: data point Xid
    :return:
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/realtime/by-xid/' + str(Xid), headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def realTimeList(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return:List realtime values
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/realtime/list?limit=100', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


# ============== THREADS ===============


def getThreads(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get all thread
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/threads?stackDepth=10&asFile=false', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


 # ======== USER ACCESS ============
def getDataPointAccessListByXid(ip, reqCookie, Xid):
    """
    :param ip:
    :param reqCookie:
    :param Xid: data point Xid
    :return: Get Data Point Access List
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/access/data-point/' + Xid, headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getDataSourceAccessListByXid(ip, reqCookie, Xid):
    """
    :param ip:
    :param reqCookie:
    :param Xid: data source Xid
    :return: Get Data Source Access List
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/access/data-source/' + Xid, headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


 # ========== USER COMMENTS =========
def userComments(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Query User Comments
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/comments', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def createNewComment(ip, reqCookie, comment, level):
    """
    :param ip:
    :param reqCookie:
    :param comment:
    :param level: INFORMATION/ERRORE/WARNING
    :return: Create New User Comment
    """
    payload = {"xid": "null",
                "name": "null",
                "timestamp": 0,
                "commentType": "POINT",
                "comment": comment,
                "username": "",
                "modelType": "null",
                "userId": 0,
                "referenceId": 0,
                "validationMessages": [{"message": "",
                                        "level": level,
                                        "property": ""}]}
    parameters_json = json.dumps(payload)
    myHeader = {'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36',
                'Content-Type': 'application/json; charset=UTF-8',
                'Connection': 'keep-alive'}
    r = requests.post(ip + '/rest/v1/comments', headers=myHeader, data=parameters_json, cookies=reqCookie)
    print r.status_code
    print r.headers


def getCommentsExplainQuery(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get Explaination For Query
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/comments/explain-query', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getAllUserComments(ip, reqCookie, limit):
    """
    :param ip:
    :param reqCookie:
    :param limit:
    :return: Get all User Comments
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/comments/list?limit='+str(limit), headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


# ============ USERS ============


def newUser(ip, reqCookie, userName, userPassword, userEmail):
    """
    :param ip:
    :param reqCookie:
    :param userName:
    :param userPassword:
    :param userEmail:
    :return: create  a new user
    """
    payload = {'username': userName,
               'email': userEmail,
               'admin': 'false',
               'disabled': 'false',
               'homeUrl': "",
               'muted': 'true',
               'password': userPassword,
               'permissions': "user",
               'receiveAlarmEmails': "NONE",
               'receiveOwnAuditEvents': 'false',
               'systemTimezone': "Etc/UTC",
               'timezone': "Etc/UTC",
               'validationMessages': [{'message': "",
                                       'level': "INFORMATION",
                                       'property': ""}]
               }
    parameters_json = json.dumps(payload)
    myHeader = {'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36',
                'Content-Type': 'application/json; charset=UTF-8',
                'Connection': 'keep-alive'}
    r = requests.post(ip + '/rest/v1/users', headers=myHeader, data=parameters_json, cookies=reqCookie)
    print r.status_code
    print r.headers


def usersApi(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Query Users
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users', headers=myHeader, cookies=reqCookie)
    # print r.status_code
    # print r.content


def currentUser(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get current user
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users/current', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def usersExplainQuery(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get Explaination For Query
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users/explain-query', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def usersList(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return:Get all user
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users/list', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getNewUser(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return:Get new user
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users/new/user', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def usersPremissions(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get User Permissions Information for all users
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users/permissions', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def usersPremissionsGroups(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get All User Groups
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users/permissions-groups', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def deleteUser(ip, reqCookie, userName):
    """
    :param ip:
    :param reqCookie:
    :param userName:
    :return:
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.delete(ip + '/rest/v1/users/' + userName, headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getUserByName(ip, reqCookie, userName):
    """
    :param ip:
    :param reqCookie:
    :param useerName:
    :return:Get user info by name
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users/'+userName, headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def setUser(ip, reqCookie, currentUserName, newUserName, newPass, newMail):
    """
    :param ip:
    :param reqCookie:
    :param currentUserName:
    :param newUserName:
    :param newPass:
    :param newMail:
    :return: Updates a user
    """
    payload = {'username': newUserName,
               'email': newMail,
               'admin': 'false',
               'disabled': 'false',
               'homeUrl': "",
               'muted': 'true',
               'password': newPass,
               'permissions': "user",
               'receiveAlarmEmails': "NONE",
               'receiveOwnAuditEvents': 'false',
               'systemTimezone': "Etc/UTC",
               'timezone': "Etc/UTC",
               'validationMessages': [{'message': "",
                                       'level': "INFORMATION",
                                       'property': ""}]
               }
    parameters_json = json.dumps(payload)
    myHeader = {'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36',
                'Content-Type': 'application/json; charset=UTF-8',
                'Connection': 'keep-alive'}
    r = requests.put(ip + '/rest/v1/users/'+currentUserName, headers=myHeader, data=parameters_json, cookies=reqCookie)
    print r.status_code
    print r.content


def setUserHomePage (ip, reqCookie, userName, newUrl):
    """
    :param ip:
    :param reqCookie:
    :param userName:
    :param newUrl:
    :return: Update a user's home url
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.put(ip + '/rest/v1/users/'+userName+'/homepage?url='+newUrl, headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def setUserMuteSettings(ip, reqCookie, userName, mute):
    """
    :param ip:
    :param reqCookie:
    :param userName:
    :param mute: true/false
    :return: Update a user's audio mute setting
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.put(ip + '/rest/v1/users/'+userName+'/mute?mute='+mute, headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


# =======================================

def logoutApi(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: logout
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/logout', cookies=reqCookie)
    # print r.status_code
    # print r.content


def logoutUserByPOST(ip, reqCookie, userName):
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.post(ip + '/rest/v1/logout/' + userName, headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


# ====================================
def parseMyCookie(reqCookie):
    tempCookie = reqCookie.split(';')[0]
    myCookie = {tempCookie.split('=')[0]: tempCookie.split('=')[1]}
    return myCookie


username = 'xxxx'
password = 'xxxxx'
myCookie = loginApi(ip, username, password)  # must login before doing anything else!!!
parsedCookie = parseMyCookie(myCookie)

# usersApi(ip, parsedCookie)
# currentUser(ip, parsedCookie)
# deleteUser(ip, parsedCookie,'yafit')
#newUser(ip, parsedCookie, 'test', 'test123', 'test123@mail')
#getUserByName(ip, parsedCookie, 'test')
#setUser(ip, parsedCookie, 'yafit', 'test', '12345', '@mail')
#setUserHomePage(ip, parsedCookie,'test','www.123.com')
#setUserMuteSettings(ip, parsedCookie,'test','false')

# dataPointsApi(ip, parsedCookie)
#getDataPointExplainQuery(ip, parsedCookie)


# dataPointListWithLimit(ip, parsedCookie,100)
# deleteDataPointByXid(ip, parsedCookie,'DP_258211')
# getDataPointByXid(ip, parsedCookie,'DP_519610')
# getAllDataPointsForDataSourceByXid(ip, parsedCookie,'DS_110513')
# getDataPointById(ip, parsedCookie,22)


# dataPointsSummary(ip, parsedCookie)
#dataPointSummExplainQuery(ip, parsedCookie)

# dataSources(ip, parsedCookie)

# getDataSourceByXid(ip, parsedCookie,'DS_110513')

# eventsApi(ip, parsedCookie)

# getEventById(ip, parsedCookie, 170)
# getEventsListWithLimit(ip, parsedCookie, 170)

# userComments(ip, parsedCookie)
#createNewComment(ip, parsedCookie, "BLA BLA BLA BLA BLA", 'WARNING')
#getCommentsExplainQuery(ip, parsedCookie)
#getAllUserComments(ip, parsedCookie,3)

#getDataPointAccessListByXid(ip, parsedCookie,'DP_519610')
#getDataSourceAccessListByXid(ip, parsedCookie,'DS_110513')

# getMaillingList(ip, parsedCookie)
#getMaillingListByXid(ip, parsedCookie, "ML_091391")
# realTimeData(ip, parsedCookie)
# realTimeList(ip, parsedCookie)
# realTimeDataByXid(ip, parsedCookie,'DP_519610')
# getThreads(ip, parsedCookie)

#getPointHierarchy(ip, parsedCookie)
#getLogFilesNames(ip, parsedCookie, 20)
#getRecentLogsFromFile(ip, parsedCookie,'ma.log')
#getLatestPointValues(ip, parsedCookie, 'DP_519610', 100 )
#getPointHierarchyFolderByName(ip, parsedCookie,'Demo Data' )
getPathToPointByXid(ip, parsedCookie,'teat 2-watts')

# logoutApi(ip, parsedCookie)
# logoutUserByPOST(ip, parsedCookie, username)
