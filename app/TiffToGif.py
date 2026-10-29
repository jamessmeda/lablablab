import java
from javax.imageio import *
from com.sun.media.jai.codecimpl import *
from java.awt.image import AffineTransformOp, BufferedImage
from java.awt.geom import AffineTransform



#
# Image convertor. Takes input  stream as arguments.
# Has method to convert full image 
# has method to produce converted thumbnail image

class TiffToGif :
    
    fullHeight = 1024
    fullWidth = 800
    
    def __init__(self,instream):
        self.image = ImageIO.read(instream)
        self.tiffWidth = self.image.getWidth()
        self.tiffHeight = self.image.getHeight()
        
   
    def convert(self,outstream,xsize=None,ysize=None,itype="gif"):
        if xsize != None:

            xscale = abs(float(xsize)/float(self.tiffWidth))
        else:
            xscale = 1.0
            
        if ysize != None:
            yscale = abs(float(ysize)/float(self.tiffHeight))
        else:
            yscale = 1.0
        
        img = None
        if xscale != 1.0 or yscale != 1.0:               
            atfm =AffineTransform() 
            atfm.scale(xscale,yscale)
            atfmOp = AffineTransformOp(atfm,AffineTransformOp.TYPE_BILINEAR)
            img = atfmOp.filter(self.image,None)
        else:
            img = self.image
            
        ImageIO.write(img,itype,outstream)
        return
    
if __name__ == '__main__':
#    filename = "07-4672217."
#    indir = "./goodData/"
    filename = "07-4952536."
    indir = "./failedData/"
    inext = "tif"
    outext = "gif"
    print "Converting : ", indir + filename  + inext," to: ",filename + outext
    
    inStream = java.io.FileInputStream(java.io.File(indir + filename + inext))
    
    imgConverter = TiffToGif(inStream)
    inStream.close()
    outYsize = imgConverter.tiffWidth * 1.4142
    print "New image size: ",imgConverter.tiffWidth," x ",outYsize
    
    outStream = java.io.FileOutputStream(java.io.File(filename + outext))  
    imgConverter.convert(outStream, None, outYsize, outext)
    outStream.close()
    
    thumbStream = java.io.FileOutputStream(java.io.File("thumb-" + filename + outext))
    imgConverter.convert(thumbStream,250,250*1.4142,outext)
    
    
        
        
    
