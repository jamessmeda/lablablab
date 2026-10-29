REM Run script for starting image processing app until
REM established as a service.
REM If you run this manually, make sure that its the ONLY ; copy running.
REM If you don't you may find that some of the ; images are doubled up!
REM
REM Contact Terry Pulford on 33310 or Peter Zviedrans if
REM you have any queries.

set JAVA_HOME=C:\Program Files (x86)\Java\jre6
path=%JAVA_HOME%\bin;C:\jython2.5.2;%path%
set classpath=C:\GribblesImages\jars\jai_codec.jar;C:\GribblesImages\jars\jai_core.jar;C:\GribblesImages\jars\jai_imageio.jar;C:\GribblesImages\jars\ojdbc6.jar;%classpath%
C:
cd C:\GribblesImages\app
jython.bat __run__.py -p imageload.props
