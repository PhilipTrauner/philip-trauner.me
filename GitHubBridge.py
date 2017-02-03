from requests import get
from time import time
from _thread import start_new_thread
from socket import gaierror

_get = get


class MockedResponse:
	def __init__(self):
		pass

	def json(self):
		return []


# If GitHub is offline or the network connection is cut
def get(*args, **kwargs):
	try:
		response =  _get(*args, **kwargs)
		if response.status_code == 200:
			return response
		else:
			return MockedResponse()
	except (gaierror, IOError):
		return MockedResponse()




class GitHub:
	def __init__(self, user, refresh_delay=3600, disable_fetch=False, 
			additional_repos=[]):
		self.user = user
		self.refresh_delay = refresh_delay
		self.disable_fetch = False
		self.additional_repos = additional_repos

		self._repos = []
		self._orgs = []
		self.repo_last_retrieve = None
		self.org_last_retrieve = None


	@property
	def repos(self):
		if not self.disable_fetch:
			if (self.repo_last_retrieve != None):
				if (self.repo_last_retrieve + self.refresh_delay) < time():
					self.repo_last_retrieve = time()
					start_new_thread(self._fetch_repos, ())
			else:
				self._fetch_repos()
				self.repo_last_retrieve = time()
		return self._repos


	@property
	def orgs(self):
		if not self.disable_fetch:
			if (self.org_last_retrieve != None):
				if (self.org_last_retrieve + self.refresh_delay) < time():
					self.org_last_retrieve = time()
					start_new_thread(self._fetch_orgs, ())
			else:
				self._fetch_orgs()
				self.org_last_retrieve = time()
		return self._orgs


	def _fetch_repos(self):
		repos = []
		forks = []
		for repo in get("https://api.github.com/users/%s/repos" % self.user).json():
			repo = Repo(*[repo["html_url"], repo["name"],
				repo["watchers_count"], repo["stargazers_count"],
				repo["fork"], repo["description"],
				repo["forks"], repo["language"]])
			if repo.fork:
				forks.append(repo)
			else:
				repos.append(repo)
		for repo in self.additional_repos:
			repo = get("https://api.github.com/repos/%s" % repo).json()
			repo = Repo(*[repo["html_url"], repo["name"],
				repo["watchers_count"], repo["stargazers_count"],
				repo["fork"], repo["description"],
				repo["forks"], repo["language"]])
			repos.append(repo)			
		for org in self.orgs:
			for repo in get("https://api.github.com/orgs/%s/repos" % org.name).json():
				repo = Repo(*[repo["html_url"], repo["name"],
					repo["watchers_count"], repo["stargazers_count"],
					repo["fork"], repo["description"],
					repo["forks"], repo["language"]])				
				for user in get("https://api.github.com/repos/%s/%s/contributors" % (org.name, repo.name)).json():
					if user["login"].lower() == self.user.lower():
						if repo.fork:
							forks.append(repo)
						else:
							repos.append(repo)
						break
		if len(repos) > 0 and len(forks) > 0:
			self._repos = sorted(repos, reverse=True) + sorted(forks, reverse=True)


	def _fetch_orgs(self):
		orgs = []
		for org in get("https://api.github.com/users/%s/orgs" % self.user).json():
			orgs.append(Org(*[org["login"], "https://github.com/" + org["login"],
				org["description"], org["avatar_url"]]))
		self._orgs = orgs


	def force_fetch(self):
		self.repos
		self.orgs


class Repo:
	def __init__(self, url, name, watchers, stars, fork, description, forks, lang):
		self.url = url
		self.name = name
		self.watchers = watchers
		self.stars = stars
		self.fork = fork
		self.description = description
		self.forks = forks
		self.lang = lang


	def __eq__(self, other):
		if type(other) is Repo:
			return self.__dict__ == other.__dict__
		return False


	def __gt__(self, other):
		if type(other) is Repo:
			return self.stars > other.stars
		return NotImplemented


	def __lt__(self, other):
		if type(other) is Repo:
			return self.stars < other.stars
		return NotImplemented


	def __repr__(self):
		return "%s: 👁 : %s ★ : %s 🍴 : %s" % (self.name, self.watchers, self.stars, "Yes" if self.fork else "No")


class Org:
	def __init__(self, name, url, description, avatar):
		self.name = name
		self.url = url
		self.description = description
		self.avatar = avatar
	

	def __eq__(self, other):
		if type(other) is Org:
			return self.__dict__ == other.__dict__
		return False


	def __repr__(self):
		return "%s: %s" % (self.name, self.url)
