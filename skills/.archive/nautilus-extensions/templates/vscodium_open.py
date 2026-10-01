#!/usr/bin/env python3
import subprocess
from gi.repository import Nautilus, GObject

class VSCodiumMenuProvider(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        pass

    def _get_items_for_path(self, path):
        item = Nautilus.MenuItem(
            name="VSCodiumExtension::open",
            label="Abrir con VSCodium",
            tip="Abrir esta carpeta en VSCodium",
        )
        item.connect("activate", self._open_in_vscodium, path)
        return [item]

    def get_file_items(self, files):
        if len(files) != 1 or not files[0].is_directory():
            return []
        path = files[0].get_location().get_path()
        return self._get_items_for_path(path)

    def get_background_items(self, current_folder):
        path = current_folder.get_location().get_path()
        return self._get_items_for_path(path)

    def _open_in_vscodium(self, menu, path):
        subprocess.Popen(["/usr/bin/codium", path])
