#!/usr/bin/python

import sys
import re
import os
from binascii import b2a_hex
reload(sys)
sys.setdefaultencoding('utf8')

###
### pdf-miner requirements
###

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage, LTChar

def with_pdf (pdf_doc, fn, pdf_pwd, *args):
    """Open the pdf document, and apply the function, returning the results"""
    result = None
    try:
        # open the pdf file
        fp = open(pdf_doc, 'rb')
        # create a parser object associated with the file object
        parser = PDFParser(fp)
        # create a PDFDocument object that stores the document structure
        doc = PDFDocument(parser,pdf_pwd)
        # connect the parser and document objects
        parser.set_document(doc)
        # supply the password for initialization
        #doc._initialize_password(pdf_pwd)
        if doc.is_extractable:
            # apply the function and return the result
            result = fn(doc, *args)

        # close the pdf file
        fp.close()
    except IOError:
        # the file doesn't exist or similar problem
        pass
    return result


###
### Table of Contents
###

def _parse_toc (doc):
    """With an open PDFDocument object, get the table of contents (toc) data
    [this is a higher-order function to be passed to with_pdf()]"""
    toc = []
    try:
        outlines = doc.get_outlines()
        for (level,title,dest,a,se) in outlines:
            toc.append( (level, title) )
    except PDFNoOutlines:
        pass
    return toc

def get_toc (pdf_doc, pdf_pwd=''):
    """Return the table of contents (toc), if any, for this pdf file"""
    return with_pdf(pdf_doc, _parse_toc, pdf_pwd)


###
### Extracting Images
###

def write_file (folder, filename, filedata, flags='w'):
    """Write the file data to the folder and filename combination
    (flags: 'w' for write text, 'wb' for write binary, use 'a' instead of 'w' for append)"""
    result = False
    if os.path.isdir(folder):
        try:
            file_obj = open(os.path.join(folder, filename), flags)
            file_obj.write(filedata)
            file_obj.close()
            result = True
        except IOError:
            pass
    return result

def determine_image_type (stream_first_4_bytes):
    """Find out the image file type based on the magic number comparison of the first 4 (or 2) bytes"""
    file_type = None
    bytes_as_hex = b2a_hex(stream_first_4_bytes)
    if bytes_as_hex.startswith('ffd8'):
        file_type = '.jpeg'
    elif bytes_as_hex == '89504e47':
        file_type = '.png'
    elif bytes_as_hex == '47494638':
        file_type = '.gif'
    elif bytes_as_hex.startswith('424d'):
        file_type = '.bmp'
    return file_type




def save_image (lt_image, page_number, images_folder):
    """Try to save the image data from this LTImage object, and return the file name, if successful"""
    result = None
    if lt_image.stream:
        file_stream = lt_image.stream.get_rawdata()
        if file_stream:
            file_ext = determine_image_type(file_stream[0:4])
            if file_ext:
                file_name = ''.join([str(page_number), '_', lt_image.name, file_ext])
                if write_file(images_folder, file_name, file_stream, flags='wb'):
                    result = file_name
    return result



###
### Extracting Text
###

def to_bytestring (s, enc='utf-8'):
    """Convert the given unicode string to a bytestring, using the standard encoding,
    unless it's already a bytestring"""
    if s:
        if isinstance(s, str):
            return s
        else:
            return s.encode(enc)

def update_page_text_hash (h, lt_obj, pct=0.2):
    """Use the bbox x0,x1 values within pct% to produce lists of associated text within the hash"""

    x0 = lt_obj.bbox[0]
    x1 = lt_obj.bbox[2]

    key_found = False
    for k, v in h.items():
        hash_x0 = k[0]
        if x0 >= (hash_x0 * (1.0-pct)) and (hash_x0 * (1.0+pct)) >= x0:
            hash_x1 = k[1]
            if x1 >= (hash_x1 * (1.0-pct)) and (hash_x1 * (1.0+pct)) >= x1:
                # the text inside this LT* object was positioned at the same
                # width as a prior series of text, so it belongs together
                key_found = True
                v.append(to_bytestring(lt_obj.get_text()))
                h[k] = v
    if not key_found:
        # the text, based on width, is a new series,
        # so it gets its own series (entry in the hash)
        h[(x0,x1)] = [to_bytestring(lt_obj.get_text())]

    return h
#save_sort_content start#
def save_sort_content (text_content, file_abs):
    with open(file_abs, "r") as f:
        a = re.split(r'\n\n+', f.read())
        j = 0
        for i in range(len(a)):
            if a[i].startswith('Fig.'):

                if '(a)' in a[i] and '(c)' not in a[i]:  # explanation is for image (a) and image (b)
                    b = re.split('[\(a\)][\(b\)]', a[i])
                    with open('C:\P1\%s.txt' % j, 'w') as g:
                        g.write(b[0] + b[1])

                    h = j + 1
                    with open('C:\P1\%s.txt' % h, 'w') as g:
                        g.write(b[0] + b[2])
                    j += 2
                elif '(c)' in a[i]:  # explanation is for image (a), image (b) and image(c)
                    c = re.split('\(a\)|\(b\)|\(c\)', a[i])
                    with open('C:\P1\%s.txt' % j, 'w') as g:
                        g.write(c[0] + c[1])
                        h = j + 1
                    with open('C:\P1\%s.txt' % h, 'w') as g:
                        g.write(c[0] + c[2])
                        k = j + 2
                    with open('C:\P1\%s.txt' % k, 'w') as g:
                        g.write(c[0] + c[3])
                    j += 3
                else:  # explanation is just for one image
                    with open('C:\P1\%s.txt' % j, 'w') as g:
                        g.write(a[i])
                        j += 1
                        # clear the content in all the txt files which weren't used
        for i in range(j, 90):
            with open('C:\P1\%s.txt' % i, 'w') as g2:
                g2.write('')
# save_sort_content end#


#determine image_folder start#
def determine_image_folder(lt_image, page_number,file_abs):

  for i in range(0,1000):
    if lt_image.name == 'Im%s'%i:
        images_folder = 'C:\P2\unknown'
        with open('C:\P1\%s.txt' % i, 'r') as f:
             for line in f:
                if 'normal' in line:
                   images_folder = 'C:\P2\Normal'
                elif 'healthy' in line:
                    images_folder = 'C:\P2\Healthy'
                elif 'lung cancer' in line:
                    images_folder = 'C:\P2\Lung_cancer'
        #         elif 'lung tumor' in line:
        #             images_folder = 'C:\P2\Lung_cancer'

        return images_folder
# #determine image_folder end#


def parse_lt_objs (lt_objs, page_number, images_folder, text_content=None):
    file_abs = 'C:\P1\P.txt'
   # """Iterate through the list of LT* objects and capture the text or image data contained in each"""
    if text_content is None:
        text_content = []

    page_text = {} # k=(x0, x1) of the bbox, v=list of text strings within that bbox width (physical column)
    for lt_obj in lt_objs:
        if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
            # text, so arrange is logically based on its column width
            page_text = update_page_text_hash(page_text, lt_obj)


        elif isinstance(lt_obj, LTFigure):
            # LTFigure objects are containers for other LT* objects, so recurse through the children
            text_content.append(parse_lt_objs(lt_obj, page_number, images_folder, text_content))

    for k, v in sorted([(key,value) for (key,value) in page_text.items()]):
        #sort the page_text hash by the keys (x0,x1 values of the bbox),
       # which produces a top-down, left-to-right sequence of related columns
        text_content.append(''.join(v))
        # save and sort page's content start#

    with open(file_abs, "w") as f:
        for a in text_content:
            f.write(a)
    save_sort_content(text_content, file_abs)

    # save and sort page's content end#
    for lt_obj in lt_objs:
       if isinstance(lt_obj, LTImage):
            #determine image folder start#
            images_folder = determine_image_folder(lt_obj, page_number, file_abs)

            # determine image folder end#

            # an image, so save it to the designated folder, and note its place in the text
            saved_file = save_image(lt_obj, page_number, images_folder)
            if saved_file:
                # use html style <img /> tag to mark the position of the image within the text
                text_content.append('<img src="'+os.path.join(images_folder, saved_file)+'" />')
            else:
                print >> sys.stderr, "error saving image on page", page_number, lt_obj.__repr__
       elif isinstance(lt_obj, LTFigure):
            # LTFigure objects are containers for other LT* objects, so recurse through the children
            text_content.append(parse_lt_objs(lt_obj, page_number, images_folder, text_content))



    return '\n'.join(text_content)


###
### Processing Pages
###

def _parse_pages (doc, images_folder):
    """With an open PDFDocument object, get the pages and parse each one
    [this is a higher-order function to be passed to with_pdf()]"""
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    text_content = []

    for i, page in enumerate(PDFPage.create_pages(doc)):
        interpreter.process_page(page)
        # receive the LTPage object for this page
        layout = device.get_result()
        # layout is an LTPage object which may contain child objects like LTTextBox, LTFigure, LTImage, etc.
        text_content.append(parse_lt_objs(layout, (i + 1), images_folder))

    return text_content

def get_pages (pdf_doc, pdf_pwd='', images_folder='/tmp'):
    """Process each of the pages in this pdf file and return a list of strings representing the text found in each page"""
    return with_pdf(pdf_doc, _parse_pages, pdf_pwd, *tuple([images_folder]))
