"""Active project state management."""

from pathlib import Path

from marketolog.core.projects import DEFAULT_PROJECTS_DIR, get_project


class ProjectContext:
    """Tracks the currently active project and provides its context to tools."""

    def __init__(self, *, projects_dir: Path = DEFAULT_PROJECTS_DIR) -> None:
        self.projects_dir = projects_dir
        self.active_project: dict | None = None
        self._active_name: str | None = None

    def switch(self, name: str) -> dict:
        """Switch active project. Raises FileNotFoundError if missing."""
        data = get_project(name, projects_dir=self.projects_dir)
        self.active_project = data
        self._active_name = name
        return data

    def get_context(self) -> dict:
        """Return full context of active project. Raises RuntimeError if none."""
        if self.active_project is None:
            raise RuntimeError("Нет активного проекта. Используйте switch_project.")
        return self.active_project

    def refresh(self) -> None:
        """Reload active project data from disk."""
        if self._active_name is not None:
            self.active_project = get_project(
                self._active_name, projects_dir=self.projects_dir
            )
