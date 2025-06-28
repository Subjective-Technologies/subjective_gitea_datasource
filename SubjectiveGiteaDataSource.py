import os
import subprocess
import requests
from urllib.parse import urljoin

from subjective_abstract_data_source_package import SubjectiveDataSource
from brainboost_data_source_logger_package.BBLogger import BBLogger
from brainboost_configuration_package.BBConfig import BBConfig


class SubjectiveGiteaDataSource(SubjectiveDataSource):
    def __init__(self, name=None, session=None, dependency_data_sources=[], subscribers=None, params=None):
        super().__init__(name=name, session=session, dependency_data_sources=dependency_data_sources, subscribers=subscribers, params=params)
        self.params = params

    def fetch(self):
        base_url = self.params['base_url']
        username = self.params['username']
        target_directory = self.params['target_directory']
        token = self.params['token']

        BBLogger.log(f"Starting fetch process for Gitea user '{username}' at '{base_url}' into directory '{target_directory}'.")

        if not os.path.exists(target_directory):
            try:
                os.makedirs(target_directory)
                BBLogger.log(f"Created directory: {target_directory}")
            except OSError as e:
                BBLogger.log(f"Failed to create directory '{target_directory}': {e}")
                raise

        try:
            headers = {
                'Authorization': f'token {token}'
            }
            url = f"{base_url}/api/v1/users/{username}/repos"
            BBLogger.log(f"Fetching list of repositories for Gitea user '{username}' from '{url}'.")

            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                error_msg = f"Failed to fetch repositories: HTTP {response.status_code}"
                BBLogger.log(error_msg)
                raise ConnectionError(error_msg)

            repos = response.json()
            if not repos:
                BBLogger.log(f"No repositories found for user '{username}'.")
                return

            BBLogger.log(f"Found {len(repos)} repositories. Starting cloning process.")

            for repo in repos:
                repo_name = repo.get('name', 'Unnamed Repository')
                clone_url = repo.get('clone_url')
                if clone_url:
                    self.clone_repo(clone_url, target_directory, repo_name)
                else:
                    BBLogger.log(f"No clone URL found for repository '{repo_name}'. Skipping.")

        except requests.RequestException as e:
            BBLogger.log(f"Error fetching repositories from Gitea: {e}")
        except Exception as e:
            BBLogger.log(f"Unexpected error: {e}")

    def clone_repo(self, repo_clone_url, target_directory, repo_name):
        try:
            BBLogger.log(f"Cloning repository '{repo_name}' from {repo_clone_url}...")
            subprocess.run(['git', 'clone', repo_clone_url], cwd=target_directory, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            BBLogger.log(f"Successfully cloned '{repo_name}'.")
        except subprocess.CalledProcessError as e:
            BBLogger.log(f"Error cloning repository '{repo_name}': {e.stderr.decode().strip()}")
        except Exception as e:
            BBLogger.log(f"Unexpected error cloning repository '{repo_name}': {e}")

    # ------------------ New Methods ------------------
    def get_icon(self):
        """Return the SVG code for the Gitea icon."""
        return """
<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" fill="#000000" data-darkreader-inline-fill="" style="--darkreader-inline-fill: #000000;">
  <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
  <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
  <g id="SVGRepo_iconCarrier">
    <circle cx="512" cy="512" r="512" style="fill: rgb(96, 153, 38); --darkreader-inline-fill: #a3da6b;" data-darkreader-inline-fill=""></circle>
    <path fill="#fff" d="M762.2 350.3c-100.9 5.3-160.7 8-212 8.5v114.1l-16-7.9-.1-106.1c-58.9 0-110.7-3.1-209.1-8.6-12.3-.1-29.5-2.4-47.9-2.5-47.1-.1-110.2 33.5-106.7 118C175.8 597.6 296 609.9 344 610.9c5.3 24.7 61.8 110.1 103.6 114.6H631c109.9-8.2 192.3-373.8 131.2-375.2zM216.2 467.6c-4.7-36.6 11.8-74.8 73.2-73.2 53.9.8 64.8 40.3 86.8 100.7-56.2-7.4-104-25.7-112.8-94.3zM679 551.1c8.3-28.7 7.1-63.4-4-84.7-20.1-31.1-55.4-42.4-86.9-37.4z"/>
  </g>
</svg>
        """

    def get_connection_data(self):
        """
        Return the connection type and required fields for Gitea.
        """
        return {
            "connection_type": "Gitea",
            "fields": ["base_url", "username", "token", "target_directory"]
        }


