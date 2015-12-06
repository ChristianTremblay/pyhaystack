__author__ = 'Yafit'
import requests

ip = 'http://XX.XX.XX.XXX:XXXX'


def loginApi(ip, username, password):
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'password': password}
    r = requests.get(ip + '/rest/v1/login/' + username, headers=myHeader)
    print r.status_code
    setCookie = r.headers['Set-Cookie']
    print setCookie
    print r.content
    return setCookie


# =============================================================================
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
               'validationMessages': '[{message:"", level: "INFORMATION", property: ""}]',

               }
    myHeader = {'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36',
                'Content-Type': 'application/json',
                'Connection': 'keep-alive'}
    r = requests.post(ip + '/rest/v1/users', headers=myHeader, params=payload, cookies=reqCookie)
    print r.status_code
    print r.content


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


def explainQuery(ip, reqCookie):
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


def userComments(ip, reqCookie):
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/comments', headers=myHeader, cookies=reqCookie)
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


# ===========================================

def dataPointsApi(ip, reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Query Data Points
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-points', headers=myHeader, cookies=reqCookie)
    # print r.status_code
    # print r.content


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


# =======================================

def dataPointsSummary(ip, reqCookie):
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-point-summaries', headers=myHeader, cookies=reqCookie)
    # print r.status_code
    # print r.content


# =======================================

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


# =======================================

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


# =======================================
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


# =======================================
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


# =======================================


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


username = 'XXX'
password = 'XXX'
myCookie = loginApi(ip, username, password)  # must login before doing anything else!!!
parsedCookie = parseMyCookie(myCookie)

# usersApi(ip, parsedCookie)
# currentUser(ip, parsedCookie)
# deleteUser(ip, parsedCookie,'yafit')
newUser(ip, parsedCookie, 'test', 'test123', 'test123@mail')

# dataPointsApi(ip, parsedCookie)

# dataPointListWithLimit(ip, parsedCookie,100)
# deleteDataPointByXid(ip, parsedCookie,'DP_258211')
# getDataPointByXid(ip, parsedCookie,'DP_519610')
# getAllDataPointsForDataSourceByXid(ip, parsedCookie,'DS_110513')
# getDataPointById(ip, parsedCookie,22)


# dataPointsSummary(ip, parsedCookie)
# dataSources(ip, parsedCookie)

# getDataSourceByXid(ip, parsedCookie,'DS_110513')

# eventsApi(ip, parsedCookie)

# getEventById(ip, parsedCookie, 170)
# getEventsListWithLimit(ip, parsedCookie, 170)

# userComments(ip, parsedCookie)

# getMaillingList(ip, parsedCookie)
# realTimeData(ip, parsedCookie)
# realTimeList(ip, parsedCookie)
# realTimeDataByXid(ip, parsedCookie,'DP_519610')
# getThreads(ip, parsedCookie)

# logoutApi(ip, parsedCookie)
# logoutUserByPOST(ip, parsedCookie, username)
