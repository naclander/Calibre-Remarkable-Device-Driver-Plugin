import json

from calibre.devices.interface import DevicePlugin, BookList
from calibre.devices.errors import FreeSpaceError

from os import system, fstat
from io import BytesIO
from typing import List
from dataclasses import dataclass, field, asdict
from pathlib import Path

import time

import sys

class RemarkablePlugin(DevicePlugin):
    name = "Remarkable Plugin"
    description = "Send files to Remarkable"
    author = "Nathan Aclander"
    supported_platforms = ["linux", "windows", "osx"]
    version = (1, 2, 3)  # The version number of this plugin
    minimum_calibre_version = (0, 7, 53)

    FORMATS = ["epub", "pdf"]

    MANAGES_DEVICE_PRESENCE = True

    def startup(self):
        # Use the plugins directory that's included with the plugin
        sys.path.append(self.plugin_path)
        global remarkable_fs
        global paramiko
        import remarkable_fs
        import paramiko

        # Currently we only support 1 device. Use this variable to remember if we've already seen it or not so as to
        # not keep detecting it. If for some reason we decide to support multiple devices, we should probably change this
        # to a list, maybe.
        self.seen_device = False

        self.apply_settings()

        self.booklist = RemarkableBookList("What", "Are", "These")
        self.conn = None
        self.document_root = None
        self.device_total_space = None
        self.device_free_space = None

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

        self.conn = remarkable_fs.connection.Connection(ssh, sftp)
        print("Creating document root")
        self.document_root = remarkable_fs.documents.DocumentRoot(self.conn)
        print("Finished creating document root")

        # Lets get some information about the device while we're here

        # The version of busybox on the remarkable tablet doesn't seem to support `-B 1`,
        # so lets just get the total size in 1024-byte blocks and multiple by 1024
        stdin, stdout, stderr = ssh.exec_command(
            "df -k | grep " + self.storage + " -m 1 | awk '{print $2}' | tr -d '\n'"
        )
        self.device_total_space = 1024 * int(stdout.read())
        
        stdin, stdout, stderr = ssh.exec_command(
            "df -k | grep " + self.storage + " -m 1 | awk '{print $4}' | tr -d '\n'"
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

    def _create_new_doc(self, title):
        parts = self.books_path.parts[1:]
        current = self.document_root
        for part in parts:
            if part in current.children.keys():
                current = current.children[part]
            else:
                current = current.new_collection(part)

        return current.new_document(title)

    def upload_books(self, files, names, on_card=None, end_session=True, metadata=None):
        # Currently everything is being uploaded under /
        print(f"Uploading {len(files)} books")
        locations = []
        for i, file in enumerate(files):
            with open(file, "rb") as f:
                size = fstat(f.fileno()).st_size
                if self.device_free_space + size > self.device_total_space:
                    raise FreeSpaceError("No space left in device 'memory'")
                metadata[i].set("size", size)
                title = metadata[i].get("title")
                new_doc = self._create_new_doc(title)
                new_doc.write(0, f.read())
                new_doc.save()
                self.device_free_space += size
                new_doc.buf.seek(0)
                # If the file is an epub, add the extension. Otherwise RemarkableFS will convert it to a PDF
                extension = ".epub" if new_doc.buf.read().startswith(b"PK") else ".pdf"
                locations.append(str(self.books_path / (title + extension)))
            print(f"Uploaded {file}")
        self.document_root = remarkable_fs.documents.DocumentRoot(self.conn)
        print("Finished uploading books")

        # The return object is the "locations" arg to add_books_to_metadata
        return (locations, None, None)

    def delete_books(self, paths, end_session=True):
        """
        Delete books at paths on device.
        """
        for path in paths:
            parts = Path(path).parts[1:]
            current = self.document_root
            for part in parts:
                if part in current.children.keys():
                    current = current.children[part]
                else:
                    raise FileNotFoundError
            print(f"Deleting {current}")
            current.delete()
            current.save()

        ftp = self.conn.ssh.open_sftp()
        json_on_device = json.load(ftp.open(str(self.metadata_path)))
        booklist_on_device = (
            [RemarkableBook(**x) for x in json_on_device] if json_on_device else []
        )
        booklist_on_device = [
            book for book in booklist_on_device if book.path not in paths
        ]
        ftp.putfo(
            BytesIO(json.dumps([asdict(x) for x in booklist_on_device]).encode()),
            str(self.metadata_path),
        )

    @classmethod
    def remove_books_from_metadata(cls, paths, booklists):
        to_remove = []
        for book in booklists[0]:
            if book.path in paths:
                to_remove.append(book)

        for book in to_remove:
            booklists[0].remove_book(book)

    @classmethod
    def add_books_to_metadata(cls, locations, metadata, booklists):
        print("Adding books to metadata")
        print(f"locations: {locations}, metadata: {metadata}, booklists: {booklists}")
        for i, m in enumerate(metadata):
            title = m.get("title")
            authors = m.get("authors")
            tags = m.get("tags")
            pubdate = m.get("pubdate")
            size = m.get("size")
            uuid = m.get("uuid")
            path = locations[0][i]
            b = RemarkableBook(
                title=title,
                authors=authors,
                size=size,
                datetime=pubdate.timetuple(),
                tags=tags,
                uuid=uuid,
                path=path,
            )
            if b not in booklists[0]:
                booklists[0].add_book(b, None)

    def books(self, oncard=None, end_session=True):
        print("`books()` called")
        self.sync_booklists((self.booklist, None, None))
        return self.booklist

    def sync_booklists(self, booklist, end_session=True):
        # TODO -  Make this function better
        # Ensure the booklist on device matches the local calibre booklist
        ftp = self.conn.ssh.open_sftp()
        try:
            print("Attempting to open existing calibre file on device")
            json_on_device = json.load(ftp.open(str(self.metadata_path)))
            booklist_on_device = (
                [RemarkableBook(**x) for x in json_on_device] if json_on_device else []
            )
        except FileNotFoundError as e:
            booklist_on_device = []

        # TOOD optimize this, maybe somehow hash RemarkableBookList
        for book in booklist[0]:
            if book not in booklist_on_device:
                booklist_on_device.append(book)
        ftp.putfo(
            BytesIO(json.dumps([asdict(x) for x in booklist_on_device]).encode()),
            str(self.metadata_path),
        )

        # Make sure our local booklist matches what's on the device too
        for book in booklist_on_device:
            if book not in booklist[0]:
                booklist[0].add_book(book)

        ftp.close()
        return booklist[0], None, None

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

        self.remarkable_ip: str = prefs["ip"]
        self.books_path: Path = Path(prefs["books_path"])
        self.metadata_path: Path = Path(prefs["metadata_path"]) / ".calibre.json"
        self.remarkable_password: str = prefs["password"]
        self.storage: str = prefs["storage"]

    def free_space(self, end_session=True):
        return (self.device_free_space, -1, -1)

    def total_space(self, end_session=True):
        return (self.device_total_space, -1, -1)

    def config_widget(self):
        from calibre_plugins.remarkable_plugin.config import ConfigWidget

        return ConfigWidget()


class RemarkableBookList(BookList):
    def __init__(self, oncard, prefix, settings):
        pass

    def supports_collections(self):
        return False

    def add_book(self, book, replace_metadata=None):
        self.append(book)

    def remove_book(self, book):
        self.remove(book)

    def get_collections(self, collection_attributes):
        return self

    def json_dumps(self):
        return json.dumps([asdict(x) for x in self])

    @staticmethod
    def json_loads(json_data):
        books = json.loads(json_data)
        rbl = RemarkableBookList("What", "Are", "These")
        for book in books:
            rbl.add_book(RemarkableBook(**book), None)
        return rbl


@dataclass()
class RemarkableBook:
    title: str
    authors: List[str]
    size: int
    datetime: field(init=False)
    tags: List[str]
    uuid: str
    path: str = "/"
    thumbnail: str = ""
    device_collections: List = field(default_factory=list)

    def __post_init__(self):
        # When RemarkableBook is created from a json blob the argument is a n array and must be converted properly
        self.datetime = time.struct_time(self.datetime)

    def __eq__(self, other):
        return self.uuid == other.uuid


class Opts:
    def __init__(self, format_map):
        self.format_map = format_map
