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
        """Return SVG icon content, preferring a local icon.svg in the plugin folder."""
        import os
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.svg')
        try:
            if os.path.exists(icon_path):
                with open(icon_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception:
            pass
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#609926"/><path fill="#fff" d="M6 12h12v2H6z"/></svg>'

    def get_connection_data(self):
        """
        Return the connection type and required fields for Gitea.
        """
        return {
            "connection_type": "Gitea",
            "fields": ["base_url", "username", "token", "target_directory"]
        }


