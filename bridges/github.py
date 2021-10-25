from _thread import start_new_thread  # type: ignore
from socket import gaierror
from time import time
from typing import Dict
from typing import List
from typing import Union
from typing import Optional
from dataclasses import dataclass

from requests import get as _get
from requests.models import Response


class MockedResponse:
    def __init__(self) -> None:
        pass

    def json(self) -> Union[List, Dict]:
        return []


# If GitHub is offline or the network connection is cut
def get(*args, **kwargs) -> Union[MockedResponse, Response]:  # type: ignore
    try:
        response = _get(*args, **kwargs)
        if response.status_code == 200:
            return response
        else:
            return MockedResponse()
    except (gaierror, IOError):
        return MockedResponse()


@dataclass(frozen=True, order=False)
class Repo:
    url: str
    name: str
    watchers: int
    stars: int
    fork: bool
    archived: bool
    description: str
    forks: int
    lang: Optional[str]

    def __gt__(self, other: "Repo") -> bool:
        return self.stars > other.stars

    def __lt__(self, other: "Repo") -> bool:
        return self.stars < other.stars


class GitHub:
    def __init__(
        self,
        user: str,
        refresh_delay: int = 3600,
        disable_fetch: bool = False,
        additional_repos: Optional[List[str]] = None,
    ) -> None:
        self.user = user
        self.refresh_delay = refresh_delay
        self.disable_fetch = disable_fetch
        self.additional_repos = [] if additional_repos is None else additional_repos

        self._repos: List[Repo] = []
        self.repo_last_retrieve: float = -1.0
        self.org_last_retrieve: float = -1.0

    @property
    def repos(self) -> List[Repo]:
        if not self.disable_fetch:
            if (self.repo_last_retrieve + self.refresh_delay) < time():
                self.repo_last_retrieve = time()
                start_new_thread(self._fetch_repos, ())
        return self._repos

    def _fetch_repos(self) -> None:
        repos = []
        archived = []
        for repo in get("https://api.github.com/users/%s/repos" % self.user).json():
            repo = Repo(
                *[
                    repo["html_url"],
                    repo["name"],
                    repo["watchers_count"],
                    repo["stargazers_count"],
                    repo["fork"],
                    repo["archived"],
                    repo["description"],
                    repo["forks"],
                    repo["language"],
                ]
            )
            if not repo.fork:
                if not repo.archived:
                    repos.append(repo)
                else:
                    archived.append(repo)

        if len(repos) > 0:
            combined = sorted(repos, reverse=True) + sorted(archived, reverse=True)

            self._repos = combined
