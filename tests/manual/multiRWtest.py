# Simple application that uses the pyhaystack library
# For this program to work you will need to have;
# 1) the API server up and running at port 3000
# 2) Insert the point AUTH_Site.1.Equip.multiPt04 and AUTH_Site.1.Equip.multiPt05
#      - You can the API system test to insert these points

# Expected output:
# Setup Widesky session. Object= <pyhaystack.client.widesky.WideskyHaystackSession object at 0x7f144f9e79d0>
# Written some data using multi hisWrite. response should be blank =  []
# Read the written data using multi hisRead. response is =
# <GetGridOperation done:
#  <Grid>
#     Metadata: MetadataObject{u'hisEnd'=datetime.datetime(2016, 7, 26, 14, 0, tzinfo=<StaticTzInfo 'Etc/UTC'>), u'hisStart'=datetime.datetime(2016, 7, 25, 14, 0, tzinfo=<StaticTzInfo 'Etc/UTC'>)}
#         Columns:
#             ts
#             id0: MetadataObject{u'id'=Ref(u'AUTH_Site.1.Equip.1.multiPt04', None, False)}
#             id1: MetadataObject{u'id'=Ref(u'AUTH_Site.1.Equip.1.multiPt05', None, False)}
#             Row    0: ts=datetime.datetime(2016, 7, 26, 12, 17, 52, tzinfo=<DstTzInfo 'Australia/Brisbane' AEST+10:00:00 STD>), id0=BasicQuantity(800.8, u'kWh'), id1=BasicQuantity(123.0, u'kWh')
#             Row    1: ts=datetime.datetime(2016, 7, 26, 14, 38, 53, tzinfo=<DstTzInfo 'Australia/Brisbane' AEST+10:00:00 STD>), id0=BasicQuantity(800.8, u'kWh'), id1=BasicQuantity(123.0, u'kWh')
#             Row    2: ts=datetime.datetime(2016, 7, 26, 14, 39, 6, tzinfo=<DstTzInfo 'Australia/Brisbane' AEST+10:00:00 STD>), id0=BasicQuantity(800.8, u'kWh'), id1=BasicQuantity(123.0, u'kWh')
#             Row    3: ts=datetime.datetime(2016, 7, 26, 14, 39, 16, tzinfo=<DstTzInfo 'Australia/Brisbane' AEST+10:00:00 STD>), id0=BasicQuantity(800.8, u'kWh'), id1=BasicQuantity(123.0, u'kWh')
#             Row    4: ts=datetime.datetime(2016, 7, 26, 14, 39, 42, tzinfo=<DstTzInfo 'Australia/Brisbane' AEST+10:00:00 STD>), id0=BasicQuantity(800.8, u'kWh'), id1=BasicQuantity(123.0, u'kWh')
#             Row    5: ts=datetime.datetime(2016, 7, 26, 14, 46, 45, tzinfo=<DstTzInfo 'Australia/Brisbane' AEST+10:00:00 STD>), id0=BasicQuantity(800.8, u'kWh'), id1=BasicQuantity(123.0, u'kWh')
#             Row    6: ts=datetime.datetime(2016, 7, 26, 14, 49, 13, tzinfo=<DstTzInfo 'Australia/Brisbane' AEST+10:00:00 STD>), id0=BasicQuantity(800.8, u'kWh'), id1=BasicQuantity(123.0, u'kWh')
#             Row    7: ts=datetime.datetime(2016, 7, 26, 14, 52, 17, tzinfo=<DstTzInfo 'Australia/Brisbane' AEST+10:00:00 STD>), id0=BasicQuantity(800.8, u'kWh'), id1=BasicQuantity(123.0, u'kWh')
#   </Grid>>
import sys
from pyhaystack.client.widesky import WideskyHaystackSession
import datetime
import pytz

# Edit the following parameters to suit your system
WS_URI = "http://localhost:3000"
WS_USERNAME = "youruser@example.com"
WS_PASSWORD = "yourpassword"
WS_CLIENT_ID = "xxxx"
WS_CLIENT_SECRET = "yyyy"


def doStuff():
    session = WideskyHaystackSession(
        uri=WS_URI,
        username=WS_USERNAME,
        password=WS_PASSWORD,
        client_id=WS_CLIENT_ID,
        client_secret=WS_CLIENT_SECRET,
    )

    print("Setup Widesky session. Object=", session)
    result = session.multi_his_write(
        timestamp_records={
            datetime.datetime.now(tz=pytz.timezone("Australia/Brisbane")).replace(
                microsecond=0
            ): {
                "AUTH_Site.1.Equip.1.multiPt04": 800.8,
                "AUTH_Site.1.Equip.1.multiPt05": 123,
            }
        }
    ).result[:]

    print("Written some data using multi hisWrite. response should be blank = ", result)

    result = session.multi_his_read(
        points=["AUTH_Site.1.Equip.1.multiPt04", "AUTH_Site.1.Equip.1.multiPt05"],
        rng="today",
    )
    print("Read the written data using multi hisRead. response is = ", result)


if __name__ == "__main__":
    try:
        doStuff()
    except KeyboardInterrupt:
        sys.exit(0)
