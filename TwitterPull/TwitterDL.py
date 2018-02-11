"""Public class for Downloading Tweets."""
import os
import shutil
import subprocess
import tarfile
from tqdm import tqdm
import requests


class TwitterDL():
    """
    Twitter Download.

    A Class for downlaoding and navigating twitter archives as hosted by the
    twitter archive team.
    """

    def __init__(self, month, year):
        """
        Initialize tweet archive download.

        :param month: int
            Integer representing month.
        :param year: int
            Integer representing year.
        """
        home = os.path.expanduser("~")
        self.module = (
            'archiveteam-twitter-stream-'
            '{y:04d}-{m:02d}'.format(y=year, m=month))
        self.tar_url = "https://archive.org/compress/" +\
            "{m}/{m}.tar".format(m=self.module)
        self.torr_url = "https://archive.org/download/" +\
            "{m}/{m}_archive.torrent".format(m=self.module)
        self.torr_kill = home + '/Documents/OpenProgress/kill_transmission.sh'
        self.torr_file = home +\
            '/Downloads/{m}_archive.torrent'.format(m=self.module)
        self.down_dir = home + '/Downloads/' + self.module
        self.down_file = self.down_dir + "/" + self.module + ".tar"
        self.year = year
        self.month = month
        self.tar_file = self.down_dir + "/" + self.module + ".tar"
        self.exdir = self.down_dir + "/{y:04d}/{m:02d}".format(y=year, m=month)

    def download_torrent(self):
        """
        Dowload file via Torrent.

        Downloads a twitter archive using torrent lib transmission-cli.
        Currently you need to be on a linux based system for this to work. In
        the future we should try and move over to the python libtorrent library
        """
        response = requests.get(self.torr_url, stream=True)
        if not os.path.exists(self.torr_file):
            with open(self.torr_file, "wb") as handle:
                for data in tqdm(response.iter_content()):
                    handle.write(data)
        tc = 'transmission-cli'
        f_ = open("/tmp/torr_down.txt", "w")
        subprocess.call([tc, self.torr_file, '-f', self.torr_kill],
                        stdout=f_)
        f_.close()

    def download_wget(self):
        """Download a file using wget, Not yet fully implemented and slow."""
        if not os.path.exists(self.down_dir):
                os.makedirs(self.down_dir)
        if self.year == 2017 and self.month > 6:
            pass
        else:
            response = requests.get(self.tar_url, stream=True)
            with open(self.down_file, "wb") as handle:
                for data in tqdm(response.iter_content()):
                    handle.write(data)

    def extract_data(self, verbose=True):
        """After Data has been downloaded extract the tar files."""
        tfiles = [x for x in os.listdir(self.down_dir)if x.endswith(".tar")]
        for t in tfiles:
            tfile = self.down_dir + "/" + t
            if verbose:
                print("Extracting file: {}".format(tfile))
            tar = tarfile.open(tfile)
            tar.extractall(self.down_dir)
            tar.close()

    def remove_folder(self):
        """Delete tweets pulled from archives."""
        shutil.rmtree(self.down_dir)
