from urllib.parse import urljoin

import requests
import requests.adapters
import requests.packages
import urllib3


def bunchify(obj):
    if isinstance(obj, (list, tuple)):
        return [bunchify(item) for item in obj]
    if isinstance(obj, dict):
        return Bunch(obj)
    return obj


class Bunch(dict):
    def __init__(self, kwargs=None):
        if kwargs is None:
            kwargs = {}
        for key, value in kwargs.items():
            kwargs[key] = bunchify(value)
        super(Bunch, self).__init__(kwargs)
        self.__dict__ = self


class MinimalConfluence:
    def __init__(
        self, host, username=None, password=None, token=None, verify=True, max_retries=4
    ):
        if token is None:
            if username is None and password is None:
                raise ValueError(
                    "Either a personal access token, "
                    "or username and password are required"
                )

        if not host.endswith("/"):
            self.host = host + "/"
        else:
            self.host = host
        self.api = requests.Session()
        self.api.verify = verify

        if token is not None:
            self.api.headers.update({"Authorization": f"Bearer {token}"})
        elif username is not None and password is not None:
            self.api.auth = (username, password)

        adapter = requests.adapters.HTTPAdapter(
            max_retries=urllib3.Retry(
                total=max_retries,
                backoff_factor=1,
                respect_retry_after_header=True,
                allowed_methods=None,
            )
        )
        self.api.mount("http://", adapter)
        self.api.mount("https://", adapter)

        if not verify:
            requests.packages.urllib3.disable_warnings(
                requests.packages.urllib3.exceptions.InsecureRequestWarning
            )

    def _request(self, method, path, **kwargs):
        r = self.api.request(method, urljoin(self.host, path), **kwargs)
        r.raise_for_status()
        return bunchify(r.json())

    def _get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)

    def _post(self, path, **kwargs):
        return self._request("POST", path, **kwargs)

    def _put(self, path, **kwargs):
        return self._request("PUT", path, **kwargs)

    def get_page(
        self,
        title=None,
        space_id=None,
        page_id=None,
    ):
        """
        Create a new page in a space

        Args:
            title (str): the title for the page
            space_id (str): the Confluence space for the page
            page_id (str or int): the ID of the page

        Returns:
            The response from the API

        """
        params = None

        if page_id is not None:
            return self._get(f"api/v2/pages/{page_id}", params=params)
        elif title is not None:
            params = {"title": title}
            if space_id is not None:
                params["space-id"] = space_id
            response = self._get("api/v2/pages", params=params)
            try:
                # A search by title/space doesn't return full page objects,
                # and since we don't support expansion in this implementation
                # just yet, we just retrieve the "full" page data using the page
                # ID for the first search result
                return self.get_page(
                    page_id=response.results[0].id,
                )
            except IndexError:
                return None
        else:
            raise ValueError("At least one of title or page_id must not be None")

    def create_page(
        self,
        space,
        title,
        body,
        parent_id=None,
        update_message=None,
        labels=None,
    ):
        """
        Create a new page in a space

        Args:
            space (str): the Confluence space id for the page
            title (str): the title for the page
            body (str): the body of the page, in Confluence Storage Format
            parent_id (str or int): the ID of the parent page
            update_message (str): optional. A message that will appear in Confluence's
              history
            labels (list(str)): optional. The set of labels the final page should have.
              None leaves existing labels unchanged

        Returns:
            The response from the API

        """
        page_structure = {
            "title": title,
            "spaceId": space,
            "status": "current",
            "body": {"representation": "storage", "value": body},
        }

        if parent_id is not None:
            # if type(parent_id) is str:
            #     parent_id = int(parent_id)
            page_structure["parentId"] = parent_id

        # if update_message is not None:
        #     page_structure["version"] = {"message": update_message}

        # if labels is not None:
        #     page_structure["metadata"] = {
        #         "labels": [{"name": label, "prefix": "global"} for label in labels]
        #     }

        return self._post("api/v2/pages", json=page_structure)

        # todo - add support for labels
        # https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content-labels/#api-wiki-rest-api-content-id-label-post
        # todo - add support for update_message if possible

    def update_page(
        self,
        page,
        body,
        parent_id=None,
        update_message=None,
        labels=None,
        minor_edit=False,
    ):
        update_structure = {
            "id": page.id,
            "status": "current",
            "title": page.title,
            "body": {
                "representation": "storage",
                "value": body,
            },
            "version": {
                "number": page.version.number + 1,
                "message": minor_edit,
            },
        }

        if parent_id is not None:
            if type(parent_id) is str:
                parent_id = int(parent_id)
            update_structure["ancestors"] = [{"id": parent_id}]

        if update_message is not None:
            update_structure["version"]["message"] = update_message

        if labels is not None:
            update_structure["metadata"] = {
                "labels": [{"name": label, "prefix": "global"} for label in labels]
            }

        return self._put(f"api/v2/pages/{page.id}", json=update_structure)

    def get_attachment(self, confluence_page, name):
        existing_attachments = self._get(
            f"api/v2/pages/{confluence_page.id}/attachments",
            headers={"X-Atlassian-Token": "nocheck", "Accept": "application/json"},
            params={"filename": name},
        )

        if len(existing_attachments.results) > 0:
            return existing_attachments.results[0]

    def update_attachment(self, confluence_page, fp, existing_attachment, message=""):
        return self._post(
            f"rest/api/content/{confluence_page.id}/child/attachment/{existing_attachment.id}/"
            f"data",
            headers={"X-Atlassian-Token": "nocheck"},
            files={"file": fp, "comment": message if message else None},
        )

    def create_attachment(self, confluence_page, fp, message=""):
        return self._post(
            f"rest/api/content/{confluence_page.id}/child/attachment",
            json={"comment": message} if message else None,
            headers={"X-Atlassian-Token": "nocheck"},
            params={"allowDuplicated": "true"},
            files={"file": fp, "comment": message if message else None},
        )

    def add_labels(self, page, labels):
        # return self.api.content(page.id).post(
        return self._post(
            f"api/v2/pages/{page.id}/label",
            data=[{"name": label, "type": "global"} for label in labels],
        )

    def get_url(self, page):
        return f"{page._links.base}{page._links.webui}"

    def get_parent_id(self, page):
        return page.ancestors[-1].id

    # todo remove expansion
    def get_space(self, space, additional_expansions=None):
        params = None
        if additional_expansions is not None:
            params = {"expand": ",".join(additional_expansions)}
        return self._get(f"api/v2/spaces/{space}", params=params)

    def get_page_ancestors(self, page_id=None):
        """
        TODO: write this docstring
        """
        params = None

        if page_id is not None:
            return self._get(f"api/v2/pages/{page_id}/ancestors", params=params).results
        else:
            raise ValueError("page_id must not be None")

    def get_page_labels(self, page_id=None):
        """
        TODO: write this docstring
        """
        params = None

        if page_id is not None:
            return self._get(f"api/v2/pages/{page_id}/labels", params=params).results
        else:
            raise ValueError("page_id must not be None")
