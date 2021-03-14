from calibre.devices.interface import DevicePlugin, BookList
from calibre.ebooks.metadata.book.base import Metadata

from os import system

import paramiko

from remarkable_fs import connection, documents


class RemarkablePlugin(DevicePlugin):
    name = "Remarkable Plugin"
    description = "Send files to Remarkable"
    supported_platforms = ["linux"]
    version = (0, 0, 1)  # The version number of this plugin
    minimum_calibre_version = (0, 7, 53)

    FORMATS = ["epub", "pdf"]

    MANAGES_DEVICE_PRESENCE = True

    def startup(self):
        # Currently we only support 1 device. Use this variable to remember if we've already seen it or not so as to
        # not keep detecting it. If for some reason we decie to support multiple devices, we should probably change this
        # to a list, maybe.
        self.seen_device = False

        self.apply_settings()

    def detect_managed_devices(self, devices_on_system, force_refresh=False):
        if self.seen_device:
            return True
        try:
            print(f"Trying to connect to {self.remarkable_ip}")
            if system("ping -c 1 " + self.remarkable_ip) == 0:
                print(f"Devcie {self.remarkable_ip} Present")
                self.seen_device = True
                return True
            else:
                print("No Device")
        except Exception as e:
            print("No Device")

    def debug_managed_device_detection(self, devices_on_system, output):
        print("TODO")
        return False

    def post_yank_cleanup(self):
        self.seen_device = False
        print("Device was yanked")

    def open(self, connected_device, library_uuid):
        print("Opening device")

        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        ssh.connect(
            self.remarkable_ip, username="root", password=self.remarkable_password
        )

        sftp = ssh.open_sftp()
        sftp.chdir("/home/root/.local/share/remarkable/xochitl")

        self.conn = connection.Connection(ssh, sftp)
        self.document_root = documents.DocumentRoot(self.conn)

        # Lets get some information about the device while we're here

        # The version of busybox on the remarkable tablet doesn't seem to support `-B 1`,
        # so lets just get the total size in 1024-byte blocks and multiple by 1024
        stdin, stdout, stderr = ssh.exec_command(
            "df -k | grep \"/dev/mmcblk1p7\" -m 1 | awk '{print $2}'"
        )
        self.device_total_space = 1024 * int(stdout.read())

        stdin, stdout, stderr = ssh.exec_command(
            "df -k | grep \"/dev/mmcblk1p7\" -m 1 | awk '{print $4}'"
        )
        self.device_free_space = 1024 * int(stdout.read())

        print(f"opened device: {self.document_root}")

    def eject(self):
        self.seen_device = False
        # Restart xochitl on eject so that any new files will show up
        on_finish = "systemctl restart xochitl"
        self.conn.ssh.exec_command(on_finish)

    def shutdown(self):
        return self.eject()

    def stop_plugin(self):
        return self.eject()

    def upload_books(self, files, names, on_card=None, end_session=True, metadata=None):
        # Currently everything is being uploaded under /
        print(f"Uploading {len(files)} books")
        for i, file in enumerate(files):
            with open(file, 'rb') as f:
                # TODO - Check if we have enough space on device to upload
                name = names[i]
                new_doc = self.document_root.new_document(name)
                new_doc.write(0, f.read())
                new_doc.save()
            print(f"Uploaded {file}")
        print("Finished uploading books")

    def delete_books(self, paths, end_session=True):
        '''
        Delete books at paths on device.
        '''
        raise NotImplementedError()

    @classmethod
    def add_books_to_metadata(cls, locations, metadata, booklists):
        print("Adding books to metadata")

    def books(self, oncard=None, end_session=True):
        # TODO - The user should be able to define an on-device library path - via the configuration - default to "/"
        # For now return an empty book list. Need to figure out how to store and retreive metadata from remarkable
        rbl = RemarkableBookList("What", "Are", "These")
        return rbl

    def sync_booklists(self, booklist, end_session=True):
        print("Returning empty booklist")
        rbl = self.books()
        return (rbl, rbl, rbl)

    def get_device_information(self, end_session=True):
        return ("TODO", "TODO", "TODO", "TODO")

    def set_progress_reporter(self, report_progress):
        print("set progress reporter")

    def card_prefix(self, end_session=True):
        return (None, None)

    def is_customizable(self):
        """
        This method must return True to enable customization via
        Preferences->Plugins
        """
        return True

    def settings(self):
        return Opts(self.FORMATS)

    def save_settings(self, config_widget):
        """
        Save the settings specified by the user with config_widget.

        :param config_widget: The widget returned by :meth:`config_widget`.
        """
        config_widget.save_settings()

        # Apply the changes
        ac = self
        if ac is not None:
            ac.apply_settings()

    def apply_settings(self):
        from calibre_plugins.remarkable_plugin.config import prefs

        # In an actual non trivial plugin, you would probably need to
        # do something based on the settings in prefs
        print(prefs)
        self.remarkable_ip: str = prefs["ip"]
        self.remarkable_password: str = prefs["password"]

    def free_space(self, end_session=True):
        return (self.device_free_space, -1, -1)

    def total_space(self, end_session=True):
        return (self.device_total_space, -1, -1)

    def config_widget(self):
        from calibre_plugins.remarkable_plugin.config import ConfigWidget
        return ConfigWidget()


class Book(Metadata):
    def __init__(
        self,
        title=None,
        authors=None,
        size=None,
        datetime=None,
        path=None,
        thumbnail=None,
        tags=[],
    ):

        Metadata.__init__(self, "")
        self._new_book = False
        self.device_collections = []

        self.title = title
        self.authors = authors
        self.size = size
        self.datetime = datetime
        self.path = path
        self.thumbnail = thumbnail
        self.tags = tags


class RemarkableBookList(BookList):
    def __init__(self, oncard, prefix, settings):
        pass

    def supports_collections(self):
        return False

    def add_book(self, book, replace_metadata):
        self.append(book)

    def remove_book(self, book):
        self.remove(book)

    def get_collections(self, collection_attributes):
        return {}


class Opts:
    def __init__(self, format_map):
        self.format_map = format_map
