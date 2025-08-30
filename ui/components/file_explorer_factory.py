from .file_explorer import FileExplorer


class FileExplorerFactory:
    """Factory für die Erstellung von File-Explorern."""
    
    def __init__(self, parent):
        self.parent = parent
    
    def create_explorer(self, section: str):
        """Erstellt einen neuen File-Explorer für den angegebenen Bereich."""
        return FileExplorer(self.parent, section)
