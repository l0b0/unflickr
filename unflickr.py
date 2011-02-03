#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
"""
unflickr
License: GPLv2

"""

import sys
import libxml2
import urllib
import getopt
import time
import os.path
import threading

# Beej's Python Flickr API
# http://beej.us/flickr/flickrapi/

from flickrapi import FlickrAPI

__version__ = '0.22 - 2009-03-20'
MAX_TIME = '9999999999'

# Gotten from Flickr

FLICKR_API_KEY = '1391fcd0a9780b247cd6a101272acf71'
FLICKR_SECRET = 'fd221d0336de3b6d'


def __test_failure(rsp):
    """Returns whether the previous call was successful"""

    if rsp['stat'] == 'fail':
        print 'Error!'
        return True
    else:
        return False

class unflickr:
    """Flickr communications object"""

    def __init__(
        self,
        key,
        secret,
        uid,
        httplib=None,
        dryrun=False,
        verbose=False,
        ):
        """Instantiates an unflickr object
        An API key is needed, as well as an API secret and a user id."""

        self.flickr_api_key = key
        self.flickr_secret = secret
        self.httplib = httplib

        # Get authentication token
        # note we must explicitly select the xmlnode parser to be compatible
        # with FlickrAPI 1.2

        self.fapi = FlickrAPI(
            self.flickr_api_key,
            self.flickr_secret,
            format='xmlnode')
        (token, frob) = self.fapi.get_token_part_one()
        if not token:
            raw_input('Press ENTER after you authorized this program')
        self.fapi.get_token_part_two((token, frob))
        self.token = token
        self.flickr_user_id = uid
        self.dryrun = dryrun
        self.verbose = verbose

    def get_photo_list(self, date_low, date_high):
        """Returns a list of photo given a time frame"""

        index = 0
        flickr_max = 500
        photos = []

        print 'Retrieving list of photos'
        while True:
            if self.verbose:
                print 'Requesting a page...'
            index = index + 1
            rsp = self.fapi.photos_search(
                api_key=self.flickr_api_key,
                auth_token=self.token,
                user_id=self.flickr_user_id,
                per_page=str(flickr_max),
                page=str(index),
                min_upload_date=date_low,
                max_upload_date=date_high,
                )
            if __test_failure(rsp):
                return None
            if rsp.photos[0]['total'] == '0':
                return None
            photos += rsp.photos[0].photo
            if self.verbose:
                print ' %d photos so far' % len(photos)
            if len(photos) >= int(rsp.photos[0]['total']):
                break

        return photos

    def get_geotagged_photo_list(self):
        """Returns a list of geotagged photos"""

        index = 0
        flickr_max = 500
        photos = []

        print 'Retrieving list of photos'
        while True:
            if self.verbose:
                print 'Requesting a page...'
            index = index + 1
            rsp = self.fapi.photos_getWithGeoData(
                api_key=self.flickr_api_key,
                auth_token=self.token,
                user_id=self.flickr_user_id,
                per_page=str(flickr_max),
                page=str(index))
            if __test_failure(rsp):
                return None
            if rsp.photos[0]['total'] == '0':
                return None
            photos += rsp.photos[0].photo
            if self.verbose:
                print ' %d photos so far' % len(photos)
            if len(photos) >= int(rsp.photos[0]['total']):
                break

        return photos

    def get_photo_location(self, pid):
        """Returns a string containing location of a photo (in XML)"""

        rsp = self.fapi.photos_geo_getLocation(
            api_key=self.flickr_api_key,
            auth_token=self.token,
            photo_id=pid)
        if __test_failure(rsp):
            return None
        doc = libxml2.parseDoc(rsp.xml)
        info = doc.xpathEval('/rsp/photo')[0].serialize()
        doc.freeDoc()
        return info

    def get_photo_location_permission(self, pid):
        """Returns a string containing location permision for a photo (in
        XML)"""

        rsp = self.fapi.photos_geo_getPerms(
            api_key=self.flickr_api_key,
            auth_token=self.token,
            photo_id=pid)
        if __test_failure(rsp):
            return None
        doc = libxml2.parseDoc(rsp.xml)
        info = doc.xpathEval('/rsp/perms')[0].serialize()
        doc.freeDoc()
        return info

    def get_photoset_list(self):
        """Returns a list of photosets for a user"""

        rsp = self.fapi.photosets_getList(
            api_key=self.flickr_api_key,
            auth_token=self.token,
            user_id=self.flickr_user_id)
        if __test_failure(rsp):
            return None
        return rsp.photosets[0].photoset

    def get_photoset_photos(self, pid):
        """Returns a list of photos in a photosets"""

        rsp = self.fapi.photosets_get_photos(
            api_key=self.flickr_api_key,
            auth_token=self.token,
            user_id=self.flickr_user_id,
            photoset_id=pid)
        if __test_failure(rsp):
            return None
        return rsp.photoset[0].photo

    def get_photoset_info(self, pid, method):
        """Returns a string containing information about a photoset (in XML)"""

        rsp = method(
            api_key=self.flickr_api_key,
            auth_token=self.token,
            photoset_id=pid)
        if __test_failure(rsp):
            return None
        doc = libxml2.parseDoc(rsp.xml)
        info = doc.xpathEval('/rsp/photoset')[0].serialize()
        doc.freeDoc()
        return info

    def get_photo_metadata(self, pid):
        """Returns an array containing containing the photo metadata (as a
        string), and the format of the photo"""

        if self.verbose:
            print 'Requesting metadata for photo %s' % pid
        rsp = self.fapi.photos_getInfo(api_key=self.flickr_api_key,
                auth_token=self.token, photo_id=pid)
        if __test_failure(rsp):
            return None
        doc = libxml2.parseDoc(rsp.xml)
        metadata = doc.xpathEval('/rsp/photo')[0].serialize()
        doc.freeDoc()
        return [metadata, rsp.photo[0]['originalformat']]

    def get_photo_comments(self, pid):
        """Returns an XML string containing the photo comments"""

        if self.verbose:
            print 'Requesting comments for photo %s' % pid
        rsp = \
            self.fapi.photos_comments_getList(api_key=self.flickr_api_key,
                auth_token=self.token, photo_id=pid)
        if __test_failure(rsp):
            return None
        doc = libxml2.parseDoc(rsp.xml)
        comments = doc.xpathEval('/rsp/comments')[0].serialize()
        doc.freeDoc()
        return comments

    def get_photo_sizes(self, pid):
        """Returns a string with is a list of available sizes for a photo"""

        rsp = self.fapi.photos_getSizes(api_key=self.flickr_api_key,
                auth_token=self.token, photo_id=pid)
        if __test_failure(rsp):
            return None
        return rsp

    def get_original_photo(self, pid):
        """Returns a URL which is the original photo, if it exists"""

        source = None
        rsp = self.get_photo_sizes(pid)
        if rsp == None:
            return None
        for size in rsp.sizes[0].size:
            if size['label'] == 'Original':
                source = size['source']
        for size in rsp.sizes[0].size:
            if size['label'] == 'Video Original':
                source = size['source']
        return [source, size['label'] == 'Video Original']

    def __download_report_hook(
        self,
        count,
        block_size,
        total_size,
        ):

        if not self.verbose:
            return
        percentage = ((100 * count) * block_size) / total_size
        if percentage > 100:
            percentage = 100
        print '\r %3d %%' % percentage,
        sys.stdout.flush()

    def download_url(
        self,
        url,
        target,
        filename
        ):
        """Saves a photo in a file"""

        if self.dryrun:
            return
        tmpfile = '%s/%s.TMP' % (target, filename)
        if self.httplib == 'wget':
            cmd = 'wget -q -t 0 -T 120 -w 10 -c -O %s %s' % (tmpfile, url)
            os.system(cmd)
        else:
            urllib.urlretrieve(
                url,
                tmpfile,
                reporthook=self.__download_report_hook)
        os.rename(tmpfile, '%s/%s' % (target, filename))


def usage():
    """Command line interface usage"""

    print """Usage: unflickr.py -i <flickr Id>
Backs up Flickr photos and metadata
Options:
  -f <date>     beginning of the date range
                (default: since you started using Flickr)
  -t <date>     end of the date range
                (default: until now)
  -d <dir>      directory for saving files (default: ./dst)
  -l <level>    levels of directory hashes (default: 0)
  -p            back up photos in addition to photo metadata
  -n            do not redownload anything which has already been downloaded
                (only jpg checked)
  -o            overwrite photo, even if it already exists
  -L            back up human-readable photo locations and permissions to
                separate files
  -s            back up all photosets (time range is ignored)
  -w            use wget instead of internal Python HTTP library
  -c <threads>  number of threads to run to backup photos (default: 1)
  -v            verbose output
  -N            dry run
  -h            this help message

Dates are specified in seconds since the Epoch (00:00:00 UTC, January 1, 1970).

Version %(version)s""" % {'version': __version__}


def file_write(
    dryrun,
    directory,
    filename,
    string,
    ):
    """Write a string into a file"""

    if dryrun:
        return
    if not os.access(directory, os.F_OK):
        os.makedirs(directory)
    file_handle = open(directory + '/' + filename, 'w')
    file_handle.write(string)
    file_handle.close()
    print 'Written as', filename


class PhotoBackupThread(threading.Thread):

    def __init__(
        self,
        sem,
        index,
        total,
        uid,
        title,
        offlickr,
        target,
        hash_level,
        get_photos,
        do_not_redownload,
        overwrite_photos,
        ):

        self.sem = sem
        self.index = index
        self.total = total
        self.uid = uid
        self.title = title
        self.offlickr = offlickr
        self.target = target
        self.hash_level = hash_level
        self.get_photos = get_photos
        self.do_not_redownload = do_not_redownload
        self.overwrite_photos = overwrite_photos
        threading.Thread.__init__(self)

    def run(self):
        backup_photo(
            self.index,
            self.total,
            self.uid,
            self.title,
            self.target,
            self.hash_level,
            self.offlickr,
            self.do_not_redownload,
            self.get_photos,
            self.overwrite_photos,
            )
        self.sem.release()


def backup_photo(
    index,
    total,
    uid,
    title,
    target,
    hash_level,
    offlickr,
    do_not_redownload,
    get_photos,
    overwrite_photos,
    ):

    print '%d/%d: %s: %s' % (index, total, uid, title.encode('utf-8'))
    target_directory = target_dir(target, hash_level, uid)
    if do_not_redownload and os.path.isfile(
        target_directory + '/' + uid + '.xml') and os.path.isfile(
        target_directory + '/' + uid + '-comments.xml') and (
            not get_photos or get_photos and os.path.isfile(
                target_directory + '/' + uid + '.jpg')):
        print 'Photo %s already downloaded; continuing' % uid
        return

    # Get Metadata

    metadata_results = offlickr.getPhotoMetadata(uid)
    if metadata_results == None:
        print 'Failed!'
        sys.exit(2)
    metadata = metadata_results[0]
    extension = metadata_results[1]
    t_dir = target_dir(target, hash_level, uid)

    # Write metadata

    file_write(offlickr.dryrun, t_dir, uid + '.xml', metadata)

    # Get comments

    photo_comments = offlickr.getPhotoComments(uid)
    file_write(
        offlickr.dryrun,
        t_dir,
        uid + '-comments.xml',
        photo_comments)

    # Do we want the picture too?

    if not get_photos:
        return
    [source, is_video] = offlickr.getOriginalPhoto(uid)

    if source == None:
        print 'Oopsie, no photo found'
        return

    # if it's a Video, we cannot trust the format that getInfo told us.
    # we have to make an extra round trip to grab the Content-Disposition
    is_private_failure = False
    if is_video:
        sourceconnection = urllib.urlopen(source)
        try:
            extension = sourceconnection.headers['Content-Disposition'].split(
                '.')[-1].rstrip('"')
        except:
            print 'warning: private video %s cannot be backed up due to a Flickr bug' % str(uid)
            extension = 'privateVideofailure'
            is_private_failure = True

    filename = uid + '.' + extension

    is_private_failure = False
    if os.path.isfile('%s/%s' % (t_dir, filename)) and not overwrite_photos:
        print '%s already downloaded... continuing' % filename
        return
    if not is_private_failure:
        print 'Retrieving ' + source + ' as ' + filename
        offlickr.download_url(source, t_dir, filename)
        print 'Done downloading %s' % filename


def backup_photos(
    threads,
    offlickr,
    target,
    hash_level,
    date_low,
    date_high,
    get_photos,
    do_not_redownload,
    overwrite_photos,
    ):
    """Back photos up for a particular time range"""

    if date_high == MAX_TIME:
        now = time.time()
        print 'For incremental backups, the current time is %.0f' % now
        print "You can rerun the program with '-f %.0f'" % now

    photos = offlickr.get_photo_list(date_low, date_high)
    if photos == None:
        print 'No photos found'
        sys.exit(1)

    total = len(photos)
    print 'Backing up', total, 'photos'

    if threads > 1:
        concurrent_threads = threading.Semaphore(threads)
    index = 0
    for photo in photos:
        index = index + 1
        # Making sure we don't have weird things here
        pid = str(int(photo['id']))
        if threads > 1:
            concurrent_threads.acquire()
            downloader = PhotoBackupThread(
                concurrent_threads,
                index,
                total,
                pid,
                photo['title'],
                offlickr,
                target,
                hash_level,
                get_photos,
                do_not_redownload,
                overwrite_photos,
                )
            downloader.start()
        else:
            backup_photo(
                index,
                total,
                pid,
                photo['title'],
                target,
                hash_level,
                offlickr,
                do_not_redownload,
                get_photos,
                overwrite_photos,
                )


def backup_location(
    offlickr,
    target,
    hash_level,
    date_high,
    do_not_redownload,
    ):
    """Back photo locations up for a particular time range"""

    if date_high == MAX_TIME:
        now = time.time()
        print 'For incremental backups, the current time is %.0f' % now
        print "You can rerun the program with '-f %.0f'" % now

    photos = offlickr.get_geotagged_photo_list()
    if photos == None:
        print 'No photos found'
        sys.exit(1)

    total = len(photos)
    print 'Backing up', total, 'photo locations'

    for photo in photos:
        # Making sure we don't have weird things here
        pid = str(int(photo['id']))
        target_directory = target_dir(target, hash_level, pid) + '/'
        if do_not_redownload and os.path.isfile(
            target_directory + pid + '-location.xml') and os.path.isfile(
            target_directory + pid + '-location-permissions.xml'):
            print pid + ': Already there'
            continue
        location = offlickr.get_photolocation(pid)
        if location == None:
            print 'Failed!'
        else:
            file_write(
                offlickr.dryrun,
                target_dir(
                    target,
                    hash_level,
                    pid),
                pid + '-location.xml',
                location)
        location_permission = offlickr.get_photolocation_permission(pid)
        if location_permission == None:
            print 'Failed!'
        else:
            file_write(
                offlickr.dryrun,
                target_dir(
                    target,
                    hash_level,
                    pid),
                pid + '-location-permissions.xml',
                location_permission)


def backup_photosets(
    threads,
    offlickr,
    get_photos,
    target,
    hash_level,
    do_not_redownload,
    overwrite_photos):
    """Back photosets up"""

    photosets = offlickr.get_photosetList()
    if photosets == None:
        print 'No photosets found'
        sys.exit(0)

    total = len(photosets)
    print 'Backing up', total, 'photosets'

    index = 0
    for photoset in photosets:
        index = index + 1
        # Making sure we don't have weird things here
        pid = str(int(photoset['id']))
        print '%d/%d: %s: %s' % (
            index,
            total,
            pid,
            photoset.title[0].text.encode('utf-8'))

        # Get Metadata

        info = offlickr.get_photosetInfo(pid,
                offlickr.fapi.photosets_getInfo)
        if info == None:
            print 'Failed!'
        else:
            file_write(
                offlickr.dryrun,
                target_dir(
                    target + '/sets/' + pid,
                    hash_level,
                    pid),
                'set_' + pid + '_info.xml',
                info)
        photos = offlickr.get_photosetInfo(
            pid,
            offlickr.fapi.photosets_get_photos)
        if photos == None:
            print 'Failed!'
        else:
            file_write(
                offlickr.dryrun,
                target_dir(
                    target + '/sets/' + pid,
                    hash_level,
                    pid),
                'set_' + pid + '_photos.xml',
                photos)

        photos = offlickr.get_photosetPhotos(pid)
        if photos == None:
            print 'No photos found in this photoset'
        else:
            total = len(photos)
            print 'Backing up', total, 'photos'
            
            if threads > 1:
                concurrent_threads = threading.Semaphore(threads)
            index = 0
            for photo in photos:
                index = index + 1

                # Making sure we don't have weird things here
                photoid = str(int(photo['id']))

                if threads > 1:
                    concurrent_threads.acquire()
                    downloader = PhotoBackupThread(
                        concurrent_threads,
                        index,
                        total,
                        photoid,
                        photo['title'],
                        offlickr,
                        target + '/sets/' + pid + '/photos',
                        hash_level,
                        get_photos,
                        do_not_redownload,
                        overwrite_photos,
                        )
                    downloader.start()
                else:
                    backup_photo(
                        index,
                        total,
                        photoid,
                        photo['title'],
                        target + '/sets/' + pid + '/photos',
                        hash_level,
                        offlickr,
                        do_not_redownload,
                        get_photos,
                        overwrite_photos,
                        )


        # Do we want the picture too?


def target_dir(target, hash_level, uid):
    directory = target
    index = 1
    while index <= hash_level:
        directory = directory + '/' + uid[len(uid) - index]
        index = index + 1
    return directory


def main():
    """Command-line interface"""

    # Default options

    flickr_user_id = None
    date_low = '1'
    date_high = MAX_TIME
    get_photos = False
    overwrite_photos = False
    do_not_redownload = False
    target = 'dst'
    photo_locations = False
    photosets = False
    verbose = False
    threads = 1
    httplib = None
    hash_level = 0
    dryrun = False

    # Parse command line

    try:
        (opts, args) = getopt.getopt(sys.argv[1:],
                'hvponNLswf:t:d:i:c:l:', ['help'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for (option, value) in opts:
        if option in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif option == '-i':
            flickr_user_id = value
        elif option == '-p':
            get_photos = True
        elif option == '-o':
            overwrite_photos = True
        elif option == '-n':
            do_not_redownload = True
        elif option == '-L':
            photo_locations = True
        elif option == '-s':
            photosets = True
        elif option == '-f':
            date_low = value
        elif option == '-t':
            date_high = value
        elif option == '-d':
            target = value
        elif option == '-w':
            httplib = 'wget'
        elif option == '-c':
            threads = int(value)
        elif option == '-l':
            hash_level = int(value)
        elif option == '-N':
            dryrun = True
        elif option == '-v':
            verbose = True

    # Check that we have a user id specified

    if flickr_user_id == None:
        print 'You need to specify a Flickr Id'
        sys.exit(1)

    # Check that the target directory exists

    if not os.path.isdir(target):
        print target + ' is not a directory; please fix that.'
        sys.exit(1)

    offlickr = unflickr(
        FLICKR_API_KEY,
        FLICKR_SECRET,
        flickr_user_id,
        httplib,
        dryrun,
        verbose,
        )

    if photosets:
        backup_photosets(
            threads,
            offlickr,
            get_photos,
            target,
            hash_level,
            do_not_redownload,
            overwrite_photos)
    elif photo_locations:
        backup_location(
            offlickr,
            target,
            hash_level,
            date_high,
            do_not_redownload,
            )
    else:
        backup_photos(
            threads,
            offlickr,
            target,
            hash_level,
            date_low,
            date_high,
            get_photos,
            do_not_redownload,
            overwrite_photos,
            )


if __name__ == '__main__':
    main()
