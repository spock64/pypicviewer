#!/usr/bin/python3
# PJR
# Simple web server script to deliver clickable thumbnails ...
# Uses lazy loading to mak it snappy (thumbnails heavy-ish to generate on the pi) 
# 
# NOTE: Read the comments - especially for the configuration constants (variables in CAPITALS)
# Pillow and Flask need to be installed ...
# So "pip3 install Flask" and "pip3 install Pillow"
# The 'jquery.unveil.js' file needs to be in the same directory as this file


import os
from io import BytesIO

from flask import Flask, Response, request, abort, render_template_string, send_from_directory
from PIL import Image, ExifTags

app = Flask(__name__)

# 0.0.0.0 means listen on all interfaces
HOST="0.0.0.0"
PORT="3030"

# Max width  height for thre thumbnails
WIDTH = 300
HEIGHT = 300

# The file 'extension'
SUFFIX = '.jpeg'
# the location of the jpegs ...
# Must end in '/'
FILEROOT = './jpg/'

# This is the template for the web page that is generated when the site is visited
# Note that anything inside '{{}}' is code that gets executed
# Note that Python allows multi line strings to be defined by enclosing the string in triple quote marks ...
TEMPLATE = '''
<!DOCTYPE html>
<html>
    <head>
        <title>Pictures in {{ root }}...</title>
        <meta charset="utf-8"/>
        <style>
        body {
            margin: 0;
            background-color: #b5b4b0;
        }
        .image {
            display: inline;
            margin: 2em auto;
            background-color: #2570d9;
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
        }
        img {
            display: block;
        }
        </style>
        <script src="https://code.jquery.com/jquery-1.10.2.min.js" charset="utf-8"></script>
        <script src="jquery.unveil.js" charset="utf-8"></script>
        <script>
            $(document).ready(function() {
                $('img').unveil();
            });
        </script>
    </head>
    <body>
    <p>Images in {{ root }} ...</p>
        {% for image in images %}
            <a class="image" href="{{ image.src }}"
               style="width: {{ image.width/2 }}px; height: {{ image.height/2 }}px">

                <img src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
                data-src="{{ image.src }}?w={{ image.width/2 }}&amp;h={{ image.height/2 }}&amp;r={{image.rotate}}"
                        width="{{ image.width/2 }}" height="{{ image.height/2 }}" />
            </a>
        {% endfor %}
    </body>
'''
# ^^^ The triple quote marks end the string ...

@app.route('/<path:filename>')
def image(filename):
    try:
        w = int(request.args['w'])
        h = int(request.args['h'])
        r = int(request.args['r'])
    except (KeyError, ValueError):
        return send_from_directory('.', filename)

    try:
        im = Image.open(filename)
        im.rotate(r).thumbnail((w, h), Image.ANTIALIAS)
        io = BytesIO()
        im.save(io, format='JPEG')
        return Response(io.getvalue(), mimetype='image/jpeg')

    except IOError:
        abort(404)

    return send_from_directory('.', filename)


# The index() function is called when the default page is loaded ...
@app.route('/')
def index():

    # Make an array to hold information about the images we find ...
    images = []

    # Find the key value for orientation EXIF tag ...
    # Used later in the loop
    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation]=='Orientation':
            break


    # Find the directories in the folder FILEROOT
    for root, dirs, files in os.walk(FILEROOT):
        # ... and for each directory ...
        # Find the files in the directory
        for filename in [os.path.join(root, name) for name in files]:
            # If its not a file with the correct SUFFIX ... skip to the next one
            if not filename.endswith(SUFFIX):
                continue

            # Use PIL to open the file
            # We can then use the im object to examine the imag
            im = Image.open(filename)

            # Now, let's deal with image rotation ...
            # Read the EXIF data which returns a list of key:value tuples
            exif=dict(im._getexif().items())

            # Is there a tag for orientation?
            # This is a "try, except" constuct ... which works as follows:
            # If the assignment works, the tag value is in o
            # Otherwise, set o to -1
            # This is needed because the image may not contain an exif tag for "orientation"
            try:
                o=exif[orientation]
            except:
                o = -1

            # Default is no rotation ...
            r= 0

            if o == 3:
                r = 180
            elif o == 6:
                r = 270
            elif o == 8:
                r = 90

            w, h = im.size

            # Deal with rotation
            if r == 90 or r == 270:
                # Swap width and height ...
                # otherwise we end up with odd stretched images
                tmp = w
                w = h
                h = tmp

            aspect = 1.0*w/h

            if aspect > 1.0*WIDTH/HEIGHT:
                width = min(w, WIDTH)
                height = width/aspect
            else:
                height = min(h, HEIGHT)
                width = height*aspect

            # Add the data we have just generated to the 'images' array
            # Inside the '{}' is a python 'dictionary' - the elements are accessed by name
            images.append({
                'width': int(width),
                'height': int(height),
                'src': filename,
                'rotate': r
            })

    # So now we have found the files in FILEROOT and built the 'images' array ...
    # We can build an html page ... and return it to the requestor
    # The line below uses the TEMPLATE strinf and is passed in the images array we built
    # Look at the TEMPLATE string to see how the page is built
    return render_template_string(TEMPLATE, **{
        'images': images,
        'root': FILEROOT
    })


# Python default startup 
if __name__ == '__main__':
    app.run(debug=False, host=HOST, port=PORT)