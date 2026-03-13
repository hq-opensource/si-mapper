# 223 Standard README file

Evolving prototypes for sketching out elements of the eventual 223 model.

## Folder structure:
- collections - Files that can be used for easy imports of multiple parts of the 223 standard
- data - Sample data files for validation, examples, etc.
- documents - All documentation files for humans
- documents/figures - Figures used in the documentation
- extensions - Configuration folder where settings are invoked (see SETTINGS_SP223-v1.0.ttl)
- imports - External standards and ontologies used by the 223 standard
- inference - Inference rules for deriving additional properties and behavior
- models - The 223 ontologies
- validation - Validation rule files

---

## Git Best Practices used in the development of the 223 standard

(Most of this borrowed from [QUDT](https://github.com/qudt/qudt-public-repo/wiki/GoodGitPractices))


### Making changes to file(s)


1. On the GitLab web page, create an issue describing the new feature or problem to be fixed. If appropriate, you can add an assignee, a Label (To Do, Doing, On Hold), and add the issue to your own GitLab Todo.

2. Create a new branch for your work using the GitLab option found under the button "Create merge request" when viewing the Issue. The branch will be automatically named.

3. Ensure you are up to date on your clone of the repo:
```
    git checkout master
    git pull
```
4. Check out the newly created 
```
    git checkout <the new branch name>
```
5. Do all your changes and additions and testing on this branch. This might last for days or more.

6. Check that all the changed files are the ones you intended using the 'git status' command below.
```
    git status
```
7. If so, add them for tracking (you can also add individual files or files satisfying regular expressions). There are a few ways of adding files using git
```
    git add -u # add only changes to files that already exist in the repo
    git add -p # add changes 'line by line', good for reviewing the changes you are committing
    git add <filename or directory> # add filename or all files in directory
```

8. Frequently commit, so that each change can be tracked and rolled back if needed.
```
    git commit -m 'Descriptive message about the change'
```
9. Bring in the latest changes from master before you push (i.e. things others might have done):
```
    git checkout master
    git pull
    git checkout srr-mynewbranch
    git merge master
```
10. Push your branch to the remote.
```
    git push
```

### Submitting a merge request for review

11. This is most easily done via the GitLab website. Once you have pushed your
   branch, it will show up under the "branches" tab. Just click the button that
   says "Merge request". Pay attention to what the pull-downs say about what
   repository and branch is being merged into what other repository and branch, to make sure they are correct. You will also be offered the chance to begin the name of the merge request with "WIP". Choosing this option tells the group that you are inviting them to review and comment on your work, but it is not yet ready for merging into the master branch. You can also attach a label of "Review" to the merge request and the associated branch.

### Reviewing the changes

12. Everybody is encouraged to review the merge requests of others. By reviewing the files on the GitLab website, you are able to attach comments to individual lines in the files. Normally, we expect the creator of the branch to actually make any changes, but with agreement by the branch creator, you can create your own branch from the branch under review, make changes there, and submit a merge request to be merged into the branch being reviewed.

### Ready to merge

13. Once the branch creator is satisfied that all the comments have been addressed, they click the "Resolve WIP status" button when viewing the merge request. This results in the "WIP:" part of the merge request name to be removed. This signals to the group that the merge request is ready for final review and merging. At least one committee member other than the branch creator should add their approval (using the "Add approval" button).

14. At this point, the merge request can be completed by anyone by clicking the "Merge" button.

