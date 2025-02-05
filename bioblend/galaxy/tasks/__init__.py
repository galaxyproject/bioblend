"""
Contains possible interaction dealing with Galaxy tasks.
"""

from typing import TYPE_CHECKING

from bioblend.galaxy.client import Client

if TYPE_CHECKING:
    from uuid import UUID

    from bioblend.galaxy import GalaxyInstance


class TasksClient(Client):
    """
    This endpoint only works on Galaxy 22.05 or later.
    """

    module = "tasks"

    def __init__(self, galaxy_instance: "GalaxyInstance") -> None:
        super().__init__(galaxy_instance)

    def get_task_status(self, task_id: "UUID") -> str:
        """
        Determine state of task ID

        :type task_id: UUID
        :param task_id: the task ID

        :rtype: str
        :return: String indicating task state
        """
        url = self._make_url() + f"/{task_id}/state"
        return self._get(url=url)
