def get_blob_content(repo, branch, path_name):
    """
    Retrieves the content of a specific file from a GitHub repository.

    :param repo: The GitHub repository object.
    :param branch: The branch name where the file is located.
    :param path_name: The path and name of the file to retrieve.
    :return: The content of the file as a blob object, or None if the file is not found.
    """
    ref = repo.get_git_ref(f'heads/{branch}')
    tree = repo.get_git_tree(ref.object.sha, recursive='/' in path_name).tree
    sha = [x.sha for x in tree if x.path == path_name]
    if not sha:
        return None
    return repo.get_git_blob(sha[0])