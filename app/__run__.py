#
# PIIMS Laboratory Image Data Processing
#
'''
	This module is the main processing module for converting Gribbles laboratory submission form
	images from the delivered TIFF format into GIF images which are stored in BLOB types in an
	Oracle database.

	The process is normally installed as a Windows service so that it runs autonomously.

	The operating parameters are stored in a Java properties file which is in the application
	home directory and by default is "imageload.props". This may be overridden on the commandline
	by using the -p propsfile, or --props=propsfile switches. E.g.:

		jython Scandir.py -p testprops.props

		jython Scandir.py --props=testprops.props
	
	The only other switch is -h ( or its alias --help ) which results in this message being printed.

	The properties file should contain the following settings:

		dbname=Oracle database instance name
		dbstr=Host connect string
		dbdriver=JDBC Driver class
		user=Database user name
		passwd=Database password for user
		#
		# optional overrides for program defaults
		#
		pollwait=The time in seconds to wait between checking for new files
		schema=Optional schema name to prefix tables with (including '.' seperator)
		homedir=Path to the directory where incoming images are to be stored.
		faildir=Optional override for default failed file directory "fail" under homedir
		savedir=Optional override for default good file directory "processed" under homedir
		thumbX=Optional X size for thumbnails - A4 aspect ratio always assumed
'''

from time import sleep,time,strftime
import os,os.path, getopt, sys, java
import java.io as jio
#import dbi
from com.ziclix.python.sql import zxJDBC
from java.util import UUID, Properties

from TiffToGif import TiffToGif
from SimpleLogging import SimpleLogger,SimpleAuditor
from shutil import copy

import traceback as tb
import re

timeFmt = '%a, %d %b %Y %H:%M:%S %Z'
insertStmt = 'insert into %slab_images (lab_request_number,isthumb_yn,add_date,imageID,image)\
		values (?,?,SYSDATE,?,?)'

sys.registry["python.options.internalTablesImpl"]="weak"

def getImgID(cursor,schema=''):
	cursor.execute("select %simageIDSeq.nextval from dual" %(schema,))
	row = cursor.fetchone()
	return int(row[0])

def simpleLogger(x):
	print x

def moveFile(fpath,destdir,logger,seqstr=None):
	
	file = os.path.basename(fpath)
	outfile = file
	if seqstr != None:
		(root,ext) = os.path.splitext(file)
		outfile = root + "_" + str(seqstr) + ext
#	print "going to move",fpath," to ",os.path.join(destdir,outfile)
	if not os.path.exists(destdir):
		 os.mkdir(destdir)
	try:
		copy(fpath,os.path.join(destdir, outfile))
		os.unlink(fpath)
	except Exception,e:
		logger("ERROR: couldn't simply move %s to %s. Reason: %s" % (fpath,os.path.join(destdir,outfile),e))
	
	
def ScanDir(imgHome,\
		dbSession,\
		faildir="fail",\
		savedir="processed",\
		inType="tif",\
		outType="gif",\
		selectAge=800,\
		thumbX=250,\
		debug=0,\
		logger=simpleLogger,\
		auditor=simpleLogger,\
		schema=""\
		):

	starttime = time()
	c = None		# DB cursor
	# Assume already in directory with images
	try:
		if not os.path.isdir(savedir):
			os.mkdir(savedir)
	except Exception,err:
		logger("Unable to find or create output directory: " + \
				savedir + ", reason: " + err )
		return

	try:
		if not os.path.isdir(faildir):
			os.mkdir(faildir)
	except Exception,err:
		logger("SEVERE: Unable to find or create fail directory: " + \
				faildir + ", reason: " + err )
		return


	try:
		auditor("Scan starting at: %s" % (strftime(timeFmt),))
		for f in filter(lambda x : os.path.isfile(os.path.join(imgHome,x))\
				and (x.endswith('.' + inType) or x.endswith('.' + inType.upper()))\
				and os.path.getmtime(os.path.join(imgHome,x)) < starttime - selectAge,\
				os.listdir(imgHome)):
			auditor("Processing imagefile: " + f)

			fpath = os.path.join(imgHome,f)

			try:	# Image processing
				inStream = jio.FileInputStream(jio.File(fpath))
				imgConverter = TiffToGif(inStream)
				inStream.close()

				fullImgStream = jio.ByteArrayOutputStream()
				thumbImgStream = jio.ByteArrayOutputStream()

				imgConverter.convert(fullImgStream,None,None,outType)
				imgConverter.convert(thumbImgStream,thumbX,thumbX*1.4142,outType)

			except Exception,e:
				logger("ERROR: Failed to convert image in %s. Reason :%s" % (fpath,e))
				auditor("Failed to convert image in %s. Reason :%s" % (fpath,e))
				try:
					moveFile(fpath,faildir,logger,str(UUID.randomUUID()))
					continue
				except Exception,e:
					logger("SEVERE: unable to move file %s to fail directory. Reason: %s" % (fpath,e))
					continue


			try:	# Database save
				labnumber = f[:11].strip('_')
				labnumber = re.sub(r'[A-Z]+', '', labnumber, re.I)
#				if c != None:
				try:
					c.close()	# Get a new cursor each time.
				except:
					pass
#					c=None
				c = dbSession.cursor()
				imgID = getImgID(c,schema)
#				print "image id :",imgID,"\n INSERT: ",insertStmt %(schema,)
				c.execute(insertStmt %(schema,),\
					(labnumber,'N',imgID,fullImgStream.toByteArray()))
				c.execute(insertStmt %(schema,),\
					(labnumber,'Y',imgID,thumbImgStream.toByteArray()))

			except zxJDBC.ProgrammingError,dberr:
				logger("ERROR: db error unable to insert images of %s into the database. Reason: %s" % (f,dberr))
				auditor("Unable to insert images of %s into the database. Reason: %s" % (f,dberr))
				dbSession.rollback()

			except Exception,e:
				logger("ERROR: db error unable to insert images of %s into the database. Reason: %s" % (f,e))
				auditor("Unable to insert images of %s into the database. Reason: %s" % (f,e))
				dbSession.rollback()

				try:
					moveFile(f,faildir,logger,str(imgID))
				except Exception,e:
					logger("SEVERE: unable to move file %s to fail directory. Reason: %s" % (f,e))
				try:
					fullImgStream.close()
				except: pass
				try:
					thumbImgStream.close()
				except: pass
				
				continue
					
			try:	# Move the file to the processed directory

				moveFile(fpath,savedir,logger,str(imgID))
			except Exception,e:
				logger("SEVERE: Unable to move file %s to save directory %s. Reason:%s"\
						% (f,savedir,e))
				auditor("Unable to move file %s to save directory %s. Reason:%s"\
						% (f,savedir,e))
				try:
					fullImgStream.close()
				except: pass
				try:
					thumbImgStream.close()
				except: pass

				continue


			dbSession.commit()	# All's well that ends well :)
			try:
				fullImgStream.close()
			except: pass
			try:
				thumbImgStream.close()
			except: pass
			
			auditor("Processed %s in %d seconds. Image ID was %d. Main image %d bytes, thumbnail %d bytes"\
				% (f,time()-starttime,imgID,fullImgStream.size(),thumbImgStream.size()))
		
	except Exception, e:
		logger("CRITICAL: Unable to process any images. Reason: " + str(e) + tb.print_exc())
	try:
		c.close()
	except:
		pass




#
# Main Entry Point
#

propsfile = "imageload.props"
props = None
session = None
homedir = "..\\goodData"
schema = ""
pollwait = 600
faildir = ".\\fail"
savedir = ".\\processed"
auditpath = "..\\logs\\audit.log"
logpath = "..\\logs\\system.log"

try:
	f = getopt.getopt(sys.argv[1:],"p:h",["props=","help"])

	if f[0].count(("--help","")) or f[0].count(("-h","")):
		print __doc__
		sys.exit(0)

	elif f[0].count(("--props","")) or f[0].count(("-p")):
		for tok in f[0]:
			tokname == tok[0]
			if tokname == "--props" or tokname =="-p":
				propsfile = tok[1]
			else:
				print "Unrecognised switch ", tok[0]
	
	try:
		props=Properties()
		props.load(jio.FileReader(propsfile))

	except Exception,e:
		print "Unable to read properties file %s. Reason: %s " % (propsfile,e)

	#
	# Get DB Session
	#
	
	zxJDBC.autocommit=0	# ensure that auto-commit is off
	session = zxJDBC.connect(props["dbstr"] + props["dbname"],props["user"],props["passwd"],props["dbdriver"])
	
	if props.containsKey("logpath"):
		logpath = props["logpath"]
	logger = SimpleLogger(logpath).logger
		
	if props.containsKey("auditpath"):
		auditpath = props["auditpath"]
	auditor = SimpleAuditor(auditpath).auditor
	
	if props.containsKey("schema"):
		schema = props["schema"]
	
	if props.containsKey("pollwait"):
		pollwait = int(props["pollwait"])
		
	if props.containsKey("homedir"):
		homedir = props["homedir"]

	while 1:
		try:
			ScanDir(homedir,session,faildir,savedir,"tif","gif",800,250,0,logger,auditor,schema)
		except Exception,e:
			logger("ERROR: Error in processing loop: " + str(e))
			tb.print_exc()
		
		sleep(pollwait)

	logger("***** Lab image processing terminated ******")
	session.close()




except getopt.GetoptError,e:
	print __doc__
	print "Error processing commandline and options. Reason: ",e

except Exception,err:
	print "ERROR: ",err, tb.print_exc()
