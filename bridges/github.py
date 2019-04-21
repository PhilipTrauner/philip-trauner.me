from _thread import start_new_thread  # type: ignore
from socket import gaierror
from time import time
from typing import Any
from typing import Dict
from typing import List
from typing import Union

from requests import get
from requests.models import Response

_get = get


class MockedResponse:
    def __init__(self) -> None:
        pass

    def json(self) -> Union[List, Dict]:
        return []


# If GitHub is offline or the network connection is cut
def get(*args, **kwargs) -> Union[MockedResponse, Response]:
    try:
        response = _get(*args, **kwargs)
        if response.status_code == 200:
            return response
        else:
            return MockedResponse()
    except (gaierror, IOError):
        return MockedResponse()


class Repo:
    def __init__(
        self,
        url: str,
        name: str,
        watchers: int,
        stars: int,
        fork: bool,
        archived: bool,
        description: str,
        forks: int,
        lang: str,
    ) -> None:
        self.url = url
        self.name = name
        self.watchers = watchers
        self.stars = stars
        self.fork = fork
        self.archived = archived
        self.description = description
        self.forks = forks
        self.lang = lang

    def __eq__(self, other: Any) -> bool:
        if type(other) is Repo:
            return self.__dict__ == other.__dict__
        return False

    def __gt__(self, other: Any) -> bool:
        if type(other) is Repo:
            return self.stars > other.stars
        return NotImplemented

    def __lt__(self, other: Any) -> bool:
        if type(other) is Repo:
            return self.stars < other.stars
        return NotImplemented

    def __repr__(self) -> str:
        return "%s: 👁 : %s ★ : %s 🍴 : %s" % (
            self.name,
            self.watchers,
            self.stars,
            "Yes" if self.fork else "No",
        )


class Org:
    def __init__(self, name: str, url: str, description: str, avatar: str) -> None:
        self.name = name
        self.url = url
        self.description = description
        self.avatar = avatar

    def __eq__(self, other: Any):
        if type(other) is Org:
            return self.__dict__ == other.__dict__
        return False

    def __repr__(self) -> str:
        return "%s: %s" % (self.name, self.url)


class GitHub:
    def __init__(
        self,
        user: str,
        refresh_delay: int = 3600,
        disable_fetch: bool = False,
        additional_repos: List[Any] = [],
    ) -> None:
        self.user = user
        self.refresh_delay = refresh_delay
        self.disable_fetch = False
        self.additional_repos = additional_repos

        self._repos: List[Repo] = []
        self._orgs: List[Org] = []
        self.repo_last_retrieve: float = -1.0
        self.org_last_retrieve: float = -1.0

    @property
    def repos(self) -> List[Repo]:
        if not self.disable_fetch:
            if self.repo_last_retrieve is not None:
                if (self.repo_last_retrieve + self.refresh_delay) < time():
                    self.repo_last_retrieve = time()
                    start_new_thread(self._fetch_repos, ())
            else:
                self._fetch_repos()
                self.repo_last_retrieve = time()
        return self._repos

    @property
    def orgs(self) -> List[Org]:
        if not self.disable_fetch:
            if self.org_last_retrieve is not None:
                if (self.org_last_retrieve + self.refresh_delay) < time():
                    self.org_last_retrieve = time()
                    start_new_thread(self._fetch_orgs, ())
            else:
                self._fetch_orgs()
                self.org_last_retrieve = time()
        return self._orgs

    def _fetch_repos(self) -> None:
        repos = []
        forks = []
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
            if repo.fork:
                forks.append(repo)
            else:
                repos.append(repo)
        for repo in self.additional_repos:
            repo = get("https://api.github.com/repos/%s" % repo).json()
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
            repos.append(repo)
        for org in self.orgs:
            for repo in get("https://api.github.com/orgs/%s/repos" % org.name).json():
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
                for user in get(
                    "https://api.github.com/repos/%s/%s/contributors"
                    % (org.name, repo.name)
                ).json():
                    if user["login"].lower() == self.user.lower():
                        if repo.fork:
                            forks.append(repo)
                        else:
                            repos.append(repo)
                        break
        if len(repos) > 0:
            self._repos = sorted(repos, reverse=True)
        if len(forks) > 0:
            self._repos += sorted(forks, reverse=True)

    def _fetch_orgs(self) -> None:
        orgs = []
        for org in get("https://api.github.com/users/%s/orgs" % self.user).json():
            orgs.append(
                Org(
                    *[
                        org["login"],
                        "https://github.com/" + org["login"],
                        org["description"],
                        org["avatar_url"],
                    ]
                )
            )
        self._orgs = orgs

    def force_fetch(self) -> None:
        self.repos
        self.orgs
